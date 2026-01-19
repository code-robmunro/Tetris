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

        # Multiplayer state
        self.game_seed = None
        self.player_role = None  # "player1" or "player2"
        self.game_started = False
        self.waiting_for_opponent = False
        self.game_over_notified = False

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
        self.level = 5
        self.lines_cleared = 140
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
        # Debug: Log mode
        import sys
        if sys.platform == "emscripten":
            import platform
            platform.window.console.log(f"[DEBUG] Game mode: {self.mode}")

        # Connect to websocket if multiplayer
        if self.mode == "multiplayer":
            if sys.platform == "emscripten":
                import platform
                platform.window.console.log("[DEBUG] Calling connect_websocket()")
            await self.connect_websocket()

            # Wait for game to start
            while self.mode == "multiplayer" and not self.game_started:
                # Show "waiting for opponent" message
                self.screen.fill((0, 0, 0))
                waiting_text = self.font.render("Waiting for opponent...", True, (255, 255, 255))
                text_rect = waiting_text.get_rect(center=(400, 300))
                self.screen.blit(waiting_text, text_rect)
                pygame.display.flip()
                await asyncio.sleep(0.1)

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

            # Send/receive websocket data and handle game over notification
            if self.mode == "multiplayer":
                await self.notify_game_over()
                if not self.paused:
                    await self.sync_network()

            pygame.display.flip()
            self.clock.tick(60)
            await asyncio.sleep(0)  # keep async flow for pygbag/browser

        # Cleanup websocket connection
        if self.websocket:
            await self.websocket.close()

    async def connect_websocket(self):
        """Establish websocket connection and wait for game start"""
        try:
            # Detect if running in browser (Pygbag/WASM)
            import sys
            is_browser = sys.platform == "emscripten"

            if is_browser:
                # Use Pygbag's platform-specific WebSocket
                import platform

                # Log to browser console
                platform.window.console.log("[Browser] Using Pygbag WebSocket")

                # For Pygbag, only try the secure tunnel URL
                url = "wss://snake-customize-contributing-allowed.trycloudflare.com"
                platform.window.console.log(f"[Browser] Connecting to {url}...")

                # Create a simple WebSocket wrapper for browser
                class BrowserWebSocket:
                    def __init__(self, url):
                        self.url = url
                        self.ws = None
                        self.messages = []

                    async def connect(self):
                        # Use platform.window.WebSocket for browser
                        import platform
                        platform.window.console.log("[DEBUG] Creating WebSocket object")

                        try:
                            # Create WebSocket using JavaScript 'new' operator
                            # Try method 1: js module
                            try:
                                import js
                                self.ws = js.WebSocket.new(self.url)
                                platform.window.console.log("[DEBUG] Method 1 (js.WebSocket.new) succeeded")
                            except:
                                # Try method 2: eval with new
                                platform.window.console.log("[DEBUG] Method 1 failed, trying eval...")
                                self.ws = platform.window.eval(f"new WebSocket('{self.url}')")
                                platform.window.console.log("[DEBUG] Method 2 (eval) succeeded")
                        except Exception as e:
                            platform.window.console.log(f"[DEBUG] All WebSocket creation methods failed: {e}")
                            raise

                        platform.window.console.log(f"[DEBUG] WebSocket created, readyState: {self.ws.readyState}")

                        # Set up event handlers before waiting
                        def on_open(event):
                            platform.window.console.log("[DEBUG] WebSocket opened!")

                        def on_error(event):
                            platform.window.console.log(f"[DEBUG] WebSocket error: {event}")

                        def on_message(event):
                            platform.window.console.log(f"[DEBUG] Received message: {event.data}")
                            self.messages.append(event.data)

                        self.ws.onopen = on_open
                        self.ws.onerror = on_error
                        self.ws.onmessage = on_message

                        # Wait for connection to open
                        max_wait = 50  # 5 seconds
                        wait_count = 0
                        while self.ws.readyState == 0 and wait_count < max_wait:  # CONNECTING
                            await asyncio.sleep(0.1)
                            wait_count += 1

                        platform.window.console.log(f"[DEBUG] After wait, readyState: {self.ws.readyState}")

                        if self.ws.readyState != 1:  # Not OPEN
                            raise ConnectionError(f"WebSocket failed to connect, readyState: {self.ws.readyState}")

                        return self

                    async def recv(self):
                        while not self.messages:
                            await asyncio.sleep(0.01)
                        return self.messages.pop(0)

                    async def send(self, data):
                        self.ws.send(data)

                    async def close(self):
                        if self.ws:
                            self.ws.close()

                ws_wrapper = BrowserWebSocket(url)
                self.websocket = await ws_wrapper.connect()
                platform.window.console.log(f"[Browser] Connected to {url}")

            else:
                # Desktop: Use standard websockets library
                import websockets
                print("[Desktop] Using standard websockets")

                server_urls = [
                    "ws://localhost:8765",  # For local play
                    "ws://75.172.7.65:8765", # Direct IP (only works with non-HTTPS clients)
                    "wss://snake-customize-contributing-allowed.trycloudflare.com"
                ]

                connected = False
                for url in server_urls:
                    try:
                        print(f"Attempting to connect to {url}...")
                        self.websocket = await asyncio.wait_for(
                            websockets.connect(url),
                            timeout=1.0
                        )
                        print(f"Connected to game server at {url}")
                        connected = True
                        break
                    except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                        print(f"Failed to connect to {url}: {e}")
                        continue

                if not connected:
                    print("Could not connect to any game server")
                    return

            # Wait for game_start message from server
            message = await self.websocket.recv()
            data = json.loads(message)

            if data.get("type") == "waiting":
                print("Waiting for opponent to connect...")
                self.waiting_for_opponent = True
                # Wait for game_start
                message = await self.websocket.recv()
                data = json.loads(message)

            if data.get("type") == "game_start":
                self.game_seed = data.get("seed")
                self.player_role = data.get("role")
                print(f"Game starting! You are {self.player_role}")
                print(f"Game seed: {self.game_seed}")

                # Initialize piece randomizer with server seed
                self.piece_randomizer.set_seed(self.game_seed)
                self.game_started = True
        except ImportError:
            print("websockets library not installed. Run: pip install websockets")
            print("Continuing in multiplayer mode without network connection")
        except Exception as e:
            print(f"Failed to connect to game server: {e}")
            print("Continuing in multiplayer mode without network connection")

    async def sync_network(self):
        """Send local state and receive opponent state"""
        if not self.websocket or not self.game_started:
            return

        try:
            # Send local state
            local_state = self.serialize_board_state()
            await self.websocket.send(json.dumps(local_state))

            # Receive opponent updates (non-blocking with short timeout)
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=0.001
                )
                data = json.loads(message)
                await self.handle_network_message(data)
            except asyncio.TimeoutError:
                pass  # No data this frame

        except Exception as e:
            print(f"Network error: {e}")

    async def handle_network_message(self, data):
        """Handle different message types from server"""
        msg_type = data.get("type")

        if msg_type == "opponent_state":
            # Update opponent board display
            if self.opponent_board:
                self.opponent_board.update_from_network(data)

        elif msg_type == "opponent_disconnected":
            print("Opponent disconnected! You win!")
            self.state = "WIN"

        elif msg_type == "opponent_game_over":
            print("Opponent lost! You win!")
            self.state = "WIN"

        elif msg_type == "game_result":
            if data.get("winner") == "opponent":
                print("You lost!")
                self.state = "LOSE"

    async def notify_game_over(self):
        """Send game over notification (called from run loop)"""
        if self.state == "GAME_OVER" and not self.game_over_notified:
            if self.mode == "multiplayer" and self.websocket:
                try:
                    print(f"[DEBUG] Sending game_over message to opponent")
                    await self.websocket.send(json.dumps({
                        "type": "game_over",
                        "timestamp": pygame.time.get_ticks()
                    }))
                    self.game_over_notified = True
                except Exception as e:
                    print(f"Failed to send game over: {e}")

    def serialize_board_state(self):
        """Convert local board to data for sending"""
        data = {
            'type': 'game_state',
            'grid': self.board.grid,
            'current_piece': None,
            'score': self.score,
            'level': self.level,
            'lines': self.lines_cleared,
            'timestamp': pygame.time.get_ticks()
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

        # Draw win/loss overlay
        if self.state == "WIN":
            overlay = pygame.Surface((800, 600))
            overlay.set_alpha(128)
            overlay.fill((0, 100, 0))
            self.screen.blit(overlay, (0, 0))

            win_text = self.font.render("YOU WIN!", True, (255, 255, 0))
            text_rect = win_text.get_rect(center=(400, 300))
            self.screen.blit(win_text, text_rect)

        elif self.state == "LOSE":
            overlay = pygame.Surface((800, 600))
            overlay.set_alpha(128)
            overlay.fill((100, 0, 0))
            self.screen.blit(overlay, (0, 0))

            lose_text = self.font.render("YOU LOSE", True, (255, 0, 0))
            text_rect = lose_text.get_rect(center=(400, 300))
            self.screen.blit(lose_text, text_rect)

    def spawn_piece(self):
        piece = Piece(randomizer=self.piece_randomizer)
        if not self.board.place_piece(piece):
            print(f"[DEBUG] GAME OVER: Failed to place piece type {piece.piece_type} at ({piece.x}, {piece.y})")
            print(f"[DEBUG] Current state: lines={self.lines_cleared}, level={self.level}, score={self.score}")
            self.state = "GAME_OVER"
            # Set flag to notify in async context
            self.game_over_notified = False
            return

    def handle_piece_lock(self, lock_info):
        if lock_info["lines_cleared"] > 0:
            print(f"[DEBUG] Cleared {lock_info['lines_cleared']} lines! Total now: {self.lines_cleared} -> {self.lines_cleared + lock_info['lines_cleared']}")
            self.sound.play("line_clear")
            self.lines_cleared += lock_info["lines_cleared"]
            self.event_bus.emit("lines_change", self.lines_cleared)
            self.calculate_level()
            self.calculate_score(lock_info)

        if lock_info["board_full"]:
            print(f"[DEBUG] GAME OVER: Board is full (lock_info says so)")
            self.state = "GAME_OVER"
            # Set flag to notify in async context
            self.game_over_notified = False
        # Don't spawn piece here - let the main update loop handle it at line 357-358

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
