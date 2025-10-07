import pygame
import sys
import asyncio
import assets
from game import Game
from globals import SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")
game = Game(screen)
assets.preload()

async def main():
    await game.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
