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
from piece_randomizer import PieceRandomizer
import assets

class Game:
    GRAVITY_TIMER_GROWTH_FACTOR = 1.1
    ENTRY_DELAY = 0.5  # Before next piece enters
    DELAYED_AUTO_SHIFT = 0.17  # Before holding L/R results in repeated movement
    SOFT_DROP_MULTIPLIER = 20

    def __init__(self, screen, mode="single"):
        # mode can be: "single", "ai", or "multiplayer"
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.running = True
        self.delta_time = self.clock.get_time() / 1000
        self.paused = False
        self.show_fps = False
        self.fps_display = 60
        self.fps_timer = 0
        self.font = pygame.font.SysFont(None, 36)
        self.event_bus = EventBus()
        
        # Create player's piece randomizer
        self.piece_randomizer = PieceRandomizer()
        
        self.ui = UI(self.event_bus, self.piece_randomizer)
        self.sound = SoundManager(self.event_bus)
        self.sound.play_music()

        # Local player board
        self.board = Board(self.event_bus, self.piece_randomizer)

        # Mode setup
        self.mode = mode
        self.opponent_board = None
        self.ai_opponent = None
        self.websocket = None

        if self.mode == "ai":
            # Create AI opponent
            from opponent_board import OpponentBoard
            from ai_opponent import AIOpponent

            self.opponent_board = OpponentBoard()

            # Remove test pieces for AI mode
            self.opponent_board.grid = [[0 for _ in range(self.opponent_board.height)]
                                        for _ in range(self.opponent_board.width)]
            self.opponent_board.current_piece_data = None

            # Create AI with its own board (don't re-import Board)
            ai_board = Board(self.event_bus, PieceRandomizer())  # AI gets its own randomizer

            # Configure AI board for 16x16 display
            ai_board.block_size = 16
            ai_board.width = 10
            ai_board.height = 20
            ai_board.grid = [[0 for _ in range(20)] for _ in range(10)]
            ai_board.piece_bits = assets.load_piece_sprites(globals.TETRIS_BIT_16_SHEET, sprite_size=16)
            ai_board.play_area = pygame.Surface((160, 320))

            ai_randomizer = PieceRandomizer()
            self.ai_opponent = AIOpponent(ai_board, ai_randomizer)

            # Spawn first piece for AI
            ai_piece = Piece(piece_bit_size=16, randomizer=ai_randomizer)
            ai_board.place_piece(ai_piece)

        elif self.mode == "multiplayer":
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
        if self.mode == "multiplayer":
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
            if self.mode == "multiplayer" and not self.paused:
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
            print("Continuing in multiplayer mode without network connection")
        except Exception as e:
            print(f"Failed to connect to game server: {e}")
            print("Continuing in multiplayer mode without network connection")

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

    def sync_ai_to_display(self):
        """Sync AI board state to opponent board display"""
        ai_board = self.ai_opponent.board
        self.opponent_board.grid = [col[:] for col in ai_board.grid]

        if ai_board.current_piece:
            self.opponent_board.current_piece_data = {
                'x': ai_board.current_piece.x,
                'y': ai_board.current_piece.y,
                'shape': ai_board.current_piece.shape,
                'piece_type': int(ai_board.current_piece.piece_type)
            }
        else:
            self.opponent_board.current_piece_data = None

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
            self.handle_piece_lock(lock_info)

        self.ui.update()

        # Spawn new piece if needed (but not during animation)
        if self.board.current_piece is None and not self.board.line_clear_animation:
            self.spawn_piece()

        # Update AI opponent
        if self.mode == "ai" and self.ai_opponent:
            self.ai_opponent.update(self.delta_time)

            # Sync AI board to opponent display
            if self.opponent_board:
                self.sync_ai_to_display()

    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)

        # Draw opponent board if in AI or multiplayer mode
        if self.mode in ["ai", "multiplayer"] and self.opponent_board:
            self.opponent_board.draw(self.screen)

    def spawn_piece(self):
        piece = Piece(randomizer=self.piece_randomizer)
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
