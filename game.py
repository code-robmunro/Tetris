import pygame
import sys
import asyncio
from ui import UI
from board import Board
from piece import Piece

class Game:
    GRAVITY_TIMER_GROWTH_FACTOR = 1.1
    ENTRY_DELAY = 0.5 # Before next piece enters
    DELAYED_AUTO_SHIFT = 0.17 # Before holding L/R results in repeated movement
    SOFT_DROP_MULTIPLIER = 20

    def __init__(self, screen):
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.running = True
        self.delta_time = self.clock.get_time() / 1000
        self.paused = False
        self.font = pygame.font.SysFont(None, 36)  # None = default font, 36 = size

        self.ui = UI()
        self.board = Board()

        self.state = "PLAYING"
        self.score = 0
        self.spawn_piece()

        self.last_lock_info = {
            "lines_cleared": 0,
            "board_full": False,
        }

        self.gravity_time = 0
        self.seconds_per_row = 0.2 # 1
        self.lock_delay = 0.5 # Grounded slide / wall kick - Level 1
        self.soft_drop_timer = 0
        self.soft_drop_active = False 

        # Initialize Pygame mixer
        pygame.mixer.init()

        # Load your music
        pygame.mixer.music.load("assets/sound/tetris.wav")

        pygame.mixer.music.set_volume(0.05)
        pygame.mixer.music.play(loops=-1, fade_ms=1000)

    async def run(self):
        while self.running:
            self.handle_input()

            if not self.paused:
                self.update()
            self.draw()  # always draw so you can see the paused frame

            # Optional: draw pause text
            if self.paused:
                pause_text = self.font.render("PAUSED", True, (255, 255, 0))
                self.screen.blit(pause_text, (100, 100))
                
            pygame.display.flip()

            self.clock.tick(60)
            await asyncio.sleep(0)  # keep async flow for pygbag/browser

        pygame.quit()
        sys.exit()

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
                elif event.key == pygame.K_w or event.key == pygame.K_e or event.key == pygame.K_UP:
                    self.rotate_cw()
                elif event.key == pygame.K_q or event.key == pygame.K_z:
                    self.rotate_ccw()
                elif event.key == pygame.K_LSHIFT:
                    self.hold_piece()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"Paused: {self.paused}")
                elif event.key == pygame.K_b:
                    breakpoint()

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    self.soft_drop_active = False  # stop soft drop

    def update(self):
        self.delta_time = self.clock.tick(60) / 1000

        # Update gravity
        if self.soft_drop_active:
            self.gravity_time += self.delta_time * self.SOFT_DROP_MULTIPLIER
        else:
            self.gravity_time += self.delta_time

        # Move piece down based on gravity
        while self.gravity_time >= self.seconds_per_row:
            self.move_down()
            self.gravity_time -= self.seconds_per_row

        self.board.update(self.delta_time)

        # Spawn a new piece if needed
        if self.board.current_piece is None:
            self.spawn_piece()

    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)

    def spawn_piece(self):
        piece = Piece()

        if not self.board.place_piece(piece):
            self.state = "GAME_OVER"
            return

    def handle_piece_lock(self):
        if self.last_lock_info["lines_cleared"]:
            self.score += self.calculate_line_score(self.last_lock_info["lines_cleared"])

        # Check game over
        if self.last_lock_info["board_full"]:
            self.state = "GAME_OVER"
        else:
        # Spawn next piece
            self.spawn_piece()

    # -----------------------------
    # Input event handlers
    # -----------------------------
    def move_down(self):
        self.board.move_down()
        
        if self.soft_drop_active == True:
            self.gravity_time = 0        

    def move_left(self):
        self.board.move_left()

    def move_right(self):
        self.board.move_right()

    def hard_drop(self):
        self.board.hard_drop()
        self.spawn_piece()        

    def rotate_cw(self):
        self.board.rotate_cw()

    def rotate_ccw(self):
        self.board.rotate_ccw()

    def hold_piece(self):
        pass