import pygame
import sys

from game import Game
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    game = Game(screen)
    game.run()

if __name__ == "__main__":
    main()
