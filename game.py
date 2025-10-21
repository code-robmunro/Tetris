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

        self.game_over = False
        self.score = 0

        # Timers
        self.gravity_timer = .25 # Falling speed - Level 1
        self.gravity_elapsed = 1 # Right at start, we drop 1 level then start accumulating at 0 
        self.gravity_timer_growth_factor = 1.1
        self.lock_timer = 0.8 # Grounded slide / wall kick - Level 1
        self.entry_delay = 0.5 # Before next piece enters
        self.delayed_auto_shift = 0.17 # Before holding L/R results in repeated movement 

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

    def update(self):
        self.delta_time = self.clock.get_time() / 1000
        
        self.spawn_timer += self.delta_time
        if self.spawn_timer >= 4.5:
            self.spawn_piece()
            self.spawn_timer = 0

        self.gravity_elapsed += self.delta_time
        if self.gravity_elapsed >= self.gravity_timer:
            self.drop_piece()
            self.gravity_elapsed = 0

    def spawn_piece(self):
        piece = Piece()

        self.board.can_place_piece(piece)

    def drop_piece(self):
        self.board.can_drop()        

    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)

        # Update the display
        pygame.display.flip()