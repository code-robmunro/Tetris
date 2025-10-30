import pygame
import sys
import asyncio
import assets
from game import Game
from globals import SCREEN_WIDTH, SCREEN_HEIGHT
# import ctypes
# ctypes.windll.user32.SetProcessDPIAware()

# Reseed random when ran in a web browser
if sys.platform == "emscripten":
    from js import crypto, Uint32Array
    arr = Uint32Array.new(1)
    crypto.getRandomValues(arr)
    random.seed(int(arr[0]))

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")
assets.preload()
game = Game(screen)

async def main():
    await game.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
