import pygame
import sys
from ui import UI
from board import Board
from pieces import Piece

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.ui = UI()
        self.board = Board()
        self.current_piece = Piece.random()
        self.next_piece = Piece.random()
        self.score = 0
        self.game_over = False
        self.running = True

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()

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
        pass

    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)

        # Update the display
        pygame.display.flip()