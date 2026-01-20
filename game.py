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
        self.delta_time = 0.016  # Initialize to ~60 FPS (1/60 second)
        self.paused = False
        self.show_fps = False
        self.fps_display = 60
        self.fps_timer = 0
        self.font = pygame.font.SysFont(None, 36)
        self.event_bus = EventBus()

        # Detect browser environment and set appropriate frame rate
        self.is_browser = sys.platform == "emscripten"
        if self.is_browser:
            self.target_fps = 60  # Start at 60, will adapt
            self.actual_fps_samples = []
            self.perf_log_timer = 0  # Separate timer for performance logging
            # Debug: Confirm browser mode is active
            import platform
            platform.window.console.log("[DEBUG] Browser mode detected, FPS tracking enabled")
        else:
            self.target_fps = 60

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

        # Network optimization - track state changes
        self.last_sent_state = None
        self.frames_since_last_send = 0
        self.send_interval = 2  # Send every 2 frames (30 updates/sec instead of 60)

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

        # DAS (Delayed Auto Shift) for left/right movement
        self.left_held = False
        self.right_held = False
        self.left_das_timer = 0
        self.right_das_timer = 0
        self.das_repeat_rate = 0.033  # 33ms between repeated moves (30 moves/sec)

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

            # Wait for game to start - process events while waiting
            import sys
            if sys.platform != "emscripten":
                print(f"[DEBUG] Entering waiting loop, game_started={self.game_started}")

            while self.mode == "multiplayer" and not self.game_started:
                # Process pygame events (important for Pygbag)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        return
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.running = False
                        return

                # Check for game_start message while waiting
                if self.websocket:
                    try:
                        # Try to receive message (non-blocking)
                        message = await asyncio.wait_for(
                            self.websocket.recv(),
                            timeout=0.01
                        )

                        # Debug: log what we received
                        import sys
                        if sys.platform == "emscripten":
                            import platform
                            platform.window.console.log(f"[DEBUG] Waiting loop received: {message}")

                        data = json.loads(message)

                        if sys.platform == "emscripten":
                            platform.window.console.log(f"[DEBUG] Message type: {data.get('type')}")

                        if data.get("type") == "game_start":
                            self.game_seed = data.get("seed")
                            self.player_role = data.get("role")
                            self.piece_randomizer.set_seed(self.game_seed)
                            self.game_started = True

                            if sys.platform == "emscripten":
                                platform.window.console.log(f"[DEBUG] Game starting in waiting loop! Role: {self.player_role}")
                            else:
                                print(f"[DEBUG] Game starting in waiting loop! Role: {self.player_role}, Seed: {self.game_seed}")
                    except asyncio.TimeoutError:
                        pass  # No message yet
                    except Exception as e:
                        import sys
                        if sys.platform == "emscripten":
                            import platform
                            platform.window.console.log(f"[DEBUG] Error in waiting loop: {e}")

                # Show "waiting for opponent" message
                self.screen.fill((0, 0, 0))
                waiting_text = self.font.render("Waiting for opponent...", True, (255, 255, 255))
                text_rect = waiting_text.get_rect(center=(400, 300))
                self.screen.blit(waiting_text, text_rect)
                pygame.display.flip()

                # Important: yield to asyncio event loop
                await asyncio.sleep(0.01)

            import sys
            if sys.platform != "emscripten":
                print(f"[DEBUG] Exited waiting loop, game_started={self.game_started}")

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

            # In browser, yield before tick to sync with requestAnimationFrame
            if self.is_browser:
                await asyncio.sleep(0)
                self.clock.tick(self.target_fps)
            else:
                self.clock.tick(self.target_fps)
                await asyncio.sleep(0)

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

                # Set up WebSocket entirely in JavaScript
                platform.window.eval(f"""
                    window.tetrisMessages = [];
                    window.tetrisConnected = false;

                    window.tetrisWS = new WebSocket('{url}');

                    window.tetrisWS.onopen = function(event) {{
                        console.log('[JS] WebSocket connected');
                        window.tetrisConnected = true;
                    }};

                    window.tetrisWS.onmessage = function(event) {{
                        console.log('[JS] Received: ' + event.data);
                        window.tetrisMessages.push(event.data);
                    }};

                    window.tetrisWS.onerror = function(error) {{
                        console.log('[JS] WebSocket error:', error);
                    }};

                    window.tetrisWS.onclose = function(event) {{
                        console.log('[JS] WebSocket closed');
                        window.tetrisConnected = false;
                    }};
                """)

                # Wait for connection
                max_wait = 50
                wait_count = 0
                while not platform.window.tetrisConnected and wait_count < max_wait:
                    await asyncio.sleep(0.1)
                    wait_count += 1

                if not platform.window.tetrisConnected:
                    platform.window.console.log("[Browser] Failed to connect")
                    return

                platform.window.console.log("[Browser] Connected successfully")

                # Minimal Python wrapper
                class BrowserWebSocket:
                    async def recv(self):
                        import platform
                        while platform.window.tetrisMessages.length == 0:
                            await asyncio.sleep(0.01)
                        return platform.window.tetrisMessages.shift()

                    async def send(self, data):
                        import platform
                        platform.window.tetrisWS.send(data)

                    async def close(self):
                        import platform
                        if platform.window.tetrisWS:
                            platform.window.tetrisWS.close()

                self.websocket = BrowserWebSocket()
                platform.window.console.log("[Browser] Wrapper created")

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

            # Wait for initial message from server (either "waiting" or "game_start")
            message = await self.websocket.recv()
            data = json.loads(message)

            if data.get("type") == "waiting":
                print("Waiting for opponent to connect...")
                self.waiting_for_opponent = True
                # DON'T block here - let the waiting screen loop handle the game_start message

            elif data.get("type") == "game_start":
                # Second player gets game_start immediately
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
        """Send local state and receive opponent state (optimized)"""
        if not self.websocket or not self.game_started:
            return

        try:
            # Only send updates periodically, not every frame
            self.frames_since_last_send += 1
            should_send = False

            if self.frames_since_last_send >= self.send_interval:
                current_state = self.serialize_board_state()

                # Check if state actually changed
                if self.last_sent_state is None or self.state_changed(current_state, self.last_sent_state):
                    should_send = True
                    self.last_sent_state = current_state
                    self.frames_since_last_send = 0

            if should_send:
                await self.websocket.send(json.dumps(current_state))

            # Always check for incoming messages (non-blocking)
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

    def state_changed(self, current, last):
        """Check if game state has meaningfully changed"""
        try:
            # Always send if piece moved or rotated
            if current['current_piece'] != last['current_piece']:
                return True

            # Always send if score/level/lines changed
            if (current['score'] != last['score'] or
                current['level'] != last['level'] or
                current['lines'] != last['lines']):
                return True

            # Grid changes (piece locked)
            if current['grid'] != last['grid']:
                return True

            return False
        except Exception as e:
            # If comparison fails, assume state changed to be safe
            print(f"[DEBUG] state_changed exception: {e}")
            return True

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
                    if not self.left_held:  # Only trigger on initial press
                        self.left_held = True
                        self.left_das_timer = 0
                        self.move_left()  # Immediate move on key press
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    if not self.right_held:  # Only trigger on initial press
                        self.right_held = True
                        self.right_das_timer = 0
                        self.move_right()  # Immediate move on key press
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
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.left_held = False
                    self.left_das_timer = 0
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.right_held = False
                    self.right_das_timer = 0
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.soft_drop_active = False  # stop soft drop

    def update(self):
        self.delta_time = self.clock.tick(self.target_fps) / 1000
        self.fps_timer += self.delta_time

        # Track actual FPS in browser to detect throttling
        if self.is_browser and self.delta_time > 0:
            actual_fps = 1 / self.delta_time
            self.actual_fps_samples.append(actual_fps)

            # Keep last 60 samples (1 second worth)
            if len(self.actual_fps_samples) > 60:
                self.actual_fps_samples.pop(0)

            # Log FPS to browser console every 5 seconds
            self.perf_log_timer += self.delta_time
            if len(self.actual_fps_samples) >= 60 and self.perf_log_timer >= 5:
                avg_fps = sum(self.actual_fps_samples) / len(self.actual_fps_samples)
                import platform
                platform.window.console.log(f"[Perf] Avg FPS: {avg_fps:.1f}, Target: {self.target_fps}, Timer: {self.perf_log_timer:.2f}s")
                self.perf_log_timer = 0  # Reset the performance log timer

            # Debug: Log timer progress every 60 frames (once per second)
            if len(self.actual_fps_samples) == 60:
                import platform
                platform.window.console.log(f"[DEBUG] Perf timer at: {self.perf_log_timer:.2f}s (need 5s to log)")

        # Handle DAS (Delayed Auto Shift) for left/right movement
        if self.left_held:
            self.left_das_timer += self.delta_time
            # Initial move happened on key press, now handle DAS delay and repeat
            if self.left_das_timer >= self.DELAYED_AUTO_SHIFT:
                # After DAS delay, move repeatedly at the repeat rate
                while self.left_das_timer >= self.DELAYED_AUTO_SHIFT + self.das_repeat_rate:
                    self.move_left()
                    self.left_das_timer -= self.das_repeat_rate

        if self.right_held:
            self.right_das_timer += self.delta_time
            # Initial move happened on key press, now handle DAS delay and repeat
            if self.right_das_timer >= self.DELAYED_AUTO_SHIFT:
                # After DAS delay, move repeatedly at the repeat rate
                while self.right_das_timer >= self.DELAYED_AUTO_SHIFT + self.das_repeat_rate:
                    self.move_right()
                    self.right_das_timer -= self.das_repeat_rate

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
