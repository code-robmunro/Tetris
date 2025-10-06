import pygame
import sys
import assets
from game import Game
from globals import SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    game = Game(screen)
    assets.preload()

    game.run()

if __name__ == "__main__":
    main()
