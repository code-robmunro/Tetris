import asyncio
import sys
import json
import pygame
import globals
from eventbus import EventBus
from board import Board
from piece import Piece
from soundmanager import SoundManager
from ui import UI

class Game:
    GRAVITY_TIMER_GROWTH_FACTOR = 1.1
    ENTRY_DELAY = 0.5  # Before next piece enters
    DELAYED_AUTO_SHIFT = 0.17  # Before holding L/R results in repeated movement
    SOFT_DROP_MULTIPLIER = 20
    
    def __init__(self, screen, multiplayer=False):
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.running = True
        self.delta_time = self.clock.get_time() / 1000
        self.paused = False
        self.show_fps = False
        self.fps_display = 60
        self.fps_timer = 0
        self.font = pygame.font.SysFont(None, 36)  # None = default font, 36 = size
        
        self.event_bus = EventBus()
        self.ui = UI(self.event_bus)
        self.sound = SoundManager(self.event_bus)
        self.sound.play_music()
        
        # Local player board
        self.board = Board(self.event_bus)
        
        # Multiplayer setup
        self.multiplayer = multiplayer
        self.opponent_board = None
        self.websocket = None
        
        if self.multiplayer:
            from opponent_board import OpponentBoard
            self.opponent_board = OpponentBoard()
        
        self.state = "PLAYING"
        self.level = 5  # 1
        self.lines_cleared = 140  # 0
        self.score = 0
        self.spawn_piece()
        
        self.last_lock_info = {
            "lines_cleared": 0,
            "board_full": False,
        }
        
        self.gravity_time = 0
        self.seconds_per_row = globals.LEVEL_SPEEDS[
            min(self.level - 1, len(globals.LEVEL_SPEEDS) - 1)
        ]
        
        self.lock_delay = 0.5  # Grounded slide / wall kick - Level 1
        self.soft_drop_timer = 0
        self.soft_drop_active = False
    
    async def run(self):
        # Connect to websocket if multiplayer
        if self.multiplayer:
            await self.connect_websocket()
        
        while self.running:
            self.handle_input()
            if not self.paused:
                self.update()
            
            self.draw()  # always draw so you can see the paused frame
            
            # Optional: draw pause text
            if self.paused:
                pause_text = self.font.render("PAUSED", True, (255, 255, 0))
                self.screen.blit(pause_text, (100, 100))
            
            if self.fps_timer >= 1:
                self.fps_display = round(1 / self.delta_time)
                self.fps_timer = 0
            
            if self.show_fps:
                show_fps_text = self.font.render(f"FPS: {self.fps_display}", True, (255, 255, 0))
                self.screen.blit(show_fps_text, (100, 100))
            
            # Send/receive websocket data
            if self.multiplayer and not self.paused:
                await self.sync_network()
            
            pygame.display.flip()
            self.clock.tick(60)
            await asyncio.sleep(0)  # keep async flow for pygbag/browser
        
        # Cleanup websocket connection
        if self.websocket:
            await self.websocket.close()
    
    async def connect_websocket(self):
        """Establish websocket connection"""
        try:
            import websockets
            self.websocket = await websockets.connect("ws://localhost:8765")
            print("Connected to game server")
        except ImportError:
            print("websockets library not installed. Run: pip install websockets")
            # self.multiplayer = False
        except Exception as e:
            print(f"Failed to connect to game server: {e}")
            # self.multiplayer = False
    
    async def sync_network(self):
        """Send local state and receive opponent state"""
        if not self.websocket:
            return
        
        try:
            # Send local player state
            local_state = self.serialize_board_state()
            await self.websocket.send(json.dumps(local_state))
            
            # Receive opponent state (non-blocking)
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(), 
                    timeout=0.001
                )
                opponent_data = json.loads(message)
                if self.opponent_board:
                    self.opponent_board.update_from_network(opponent_data)
            except asyncio.TimeoutError:
                pass  # No data available this frame
                
        except Exception as e:
            print(f"Network error: {e}")
            # Optionally disable multiplayer on persistent errors
    
    def serialize_board_state(self):
        """Convert local board to data for sending"""
        data = {
            'grid': self.board.grid,
            'current_piece': None
        }
        
        if self.board.current_piece:
            data['current_piece'] = {
                'x': self.board.current_piece.x,
                'y': self.board.current_piece.y,
                'shape': self.board.current_piece.shape,
                'piece_type': int(self.board.current_piece.piece_type)
            }
        
        return data
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.move_left()
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.move_right()
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.soft_drop_active = True
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif (
                    event.key == pygame.K_w
                    or event.key == pygame.K_e
                    or event.key == pygame.K_UP
                ):
                    self.rotate_cw()
                elif event.key == pygame.K_q or event.key == pygame.K_z:
                    self.rotate_ccw()
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    self.hold_piece()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"Paused: {self.paused}")
                elif event.key == pygame.K_f:
                    self.show_fps = not self.show_fps
                elif event.key == pygame.K_b:
                    breakpoint()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    self.soft_drop_active = False  # stop soft drop
    
    def update(self):
        self.delta_time = self.clock.tick(60) / 1000
        self.fps_timer += self.delta_time
        
        if self.soft_drop_active:
            self.gravity_time += self.delta_time * self.SOFT_DROP_MULTIPLIER
        else:
            self.gravity_time += self.delta_time
        
        # Update gravity
        while self.gravity_time >= self.seconds_per_row:
            self.move_down(from_input=self.soft_drop_active)
            self.gravity_time -= self.seconds_per_row
        
        # Update board (includes piece lock detection)
        lock_info = self.board.update(self.delta_time)
        
        # Check for line clear animation updates
        if self.board.line_clear_animation:
            animation_result = self.board.update_line_clear_animation(self.delta_time)
            if animation_result and animation_result['lines_cleared'] > 0:
                # Animation finished, now handle the cleared lines
                self.handle_piece_lock(animation_result)
        elif lock_info['lines_cleared'] > 0:
            # No animation active, but lines need clearing
            # This shouldn't happen with new system, but kept for safety
            self.handle_piece_lock(lock_info)
        
        self.ui.update()
        
        # Spawn new piece if needed (but not during animation)
        if self.board.current_piece is None and not self.board.line_clear_animation:
            self.spawn_piece()
    
    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)
        
        # Draw opponent board if multiplayer
        if self.multiplayer and self.opponent_board:
            self.opponent_board.draw(self.screen)
    
    def spawn_piece(self):
        piece = Piece()
        if not self.board.place_piece(piece):
            self.state = "GAME_OVER"
            return
    
    def handle_piece_lock(self, lock_info):
        if lock_info["lines_cleared"] > 0:
            self.sound.play("line_clear")
            self.lines_cleared += lock_info["lines_cleared"]
            self.event_bus.emit("lines_change", self.lines_cleared)
            self.calculate_level()
            self.calculate_score(lock_info)
        
        if lock_info["board_full"]:
            self.state = "GAME_OVER"
        else:
            self.spawn_piece()
    
    def total_lines_for_level(self, level):
        # Returns cumulative total lines needed to reach the given level
        # Level 1 → 2 requires 20 lines
        return 10 * (level * (level + 1) // 2) - 10
    
    def calculate_level(self):
        while self.lines_cleared >= self.total_lines_for_level(self.level + 1):
            self.level += 1
            self.event_bus.emit("level_change", self.level)
            self.seconds_per_row = globals.LEVEL_SPEEDS[
                min(self.level - 1, len(globals.LEVEL_SPEEDS) - 1)
            ]
    
    def calculate_score(self, lock_info):
        self.score += globals.SCORES[lock_info["lines_cleared"] - 1] * (self.level + 1)
        self.event_bus.emit("score_change", self.score)
    
    # -----------------------------
    # Input event handlers
    # -----------------------------
    
    def move_down(self, from_input=False):
        moved = self.board.move_down()
        if from_input and moved:
            self.sound.play("move")
        if self.soft_drop_active:
            self.gravity_time = 0
    
    def move_left(self):
        if self.board.move_left():
            self.sound.play("move")
    
    def move_right(self):
        if self.board.move_right():
            self.sound.play("move")
    
    def hard_drop(self):
        lock_info = self.board.hard_drop()
        self.handle_piece_lock(lock_info)
    
    def rotate_cw(self):
        if self.board.rotate_cw():
            self.sound.play("rotate")
    
    def rotate_ccw(self):
        if self.board.rotate_ccw():
            self.sound.play("rotate")
    
    def hold_piece(self):
        self.board.hold_piece()
