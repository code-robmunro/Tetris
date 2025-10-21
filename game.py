import pygame
import sys
import asyncio
from ui import UI
from board import Board
from piece import Piece

class Game:
    def __init__(self, screen):
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.running = True
        self.delta_time = self.clock.get_time() / 1000

        self.ui = UI()
        self.board = Board()

        self.state = "PLAYING"
        self.score = 0
        self.spawn_piece()

        self.last_lock_info = {
            "lines_cleared": 0,
            "board_full": False,
        }

        # Timers
        self.seconds_per_row = 1
        self.gravity_elapsed = 1 # Right at start, we drop 1 level then start accumulating at 0 
        self.gravity_timer_growth_factor = 1.1
        self.lock_timer = 0.8 # Grounded slide / wall kick - Level 1
        self.entry_delay = 0.5 # Before next piece enters
        self.delayed_auto_shift = 0.17 # Before holding L/R results in repeated movement 
        self.soft_drop_timer = 0
        self.soft_drop_multiplier = 20
        self.soft_drop_active = False

        self.spawn_timer = 4.5    
        

    async def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()

            self.clock.tick(60)
            # yield control back to pygbag/browser
            await asyncio.sleep(0)

        # Quit pygame
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

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    self.soft_drop_active = False  # stop soft drop

    def update(self):
        self.delta_time = self.clock.tick(60) / 1000
        
        if self.soft_drop_active:
            self.gravity_elapsed += self.delta_time * self.soft_drop_multiplier
        else:
            self.gravity_elapsed += self.delta_time

        while self.gravity_elapsed >= self.seconds_per_row:
            self.move_down()
            self.gravity_elapsed -= self.seconds_per_row

        if self.board.current_piece is None:
            result = self.handle_piece_lock()
        
        self.spawn_timer += self.delta_time
        if self.spawn_timer >= 4.5:
            self.spawn_piece()
            self.spawn_timer = 0

    def handle_piece_lock(self):
        if self.last_lock_info["lines_cleared"]:
            self.score += self.calculate_line_score(self.last_lock_info["lines_cleared"])

        # Check game over
        if self.last_lock_info["board_full"]:
            self.state = "GAME_OVER"
        else:
        # Spawn next piece
            self.spawn_piece()

    def spawn_piece(self):
        piece = Piece()

        self.board.place_piece(piece)

    def move_down(self):
        self.board.move_down()
        
        if self.soft_drop_active == True:
            self.gravity_elapsed = 0        

    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)

        # Update the display
        pygame.display.flip()

    def move_left(self):
        self.board.move_left()

    def move_right(self):
        self.board.move_right()

    def hard_drop(self):
        pass

    def rotate_cw(self):
        self.board.rotate_cw()

    def rotate_ccw(self):
        self.board.rotate_ccw()

    def hold_piece(self):
        pass