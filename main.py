import pygame
import asyncio
import assets
from game import Game
from menu import Menu
from globals import SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")

assets.preload()

async def main():
    clock = pygame.time.Clock()
    
    while True:
        # Show menu
        menu = Menu(screen)
        menu_choice = None
        
        while menu_choice is None:
            menu_choice = menu.handle_input()
            menu.draw()
            clock.tick(60)
            await asyncio.sleep(0)
        
        # Handle menu choice
        if menu_choice == "EXIT":
            break
        elif menu_choice == "SINGLE_PLAYER":
            # Start single player gamea
            game = Game(screen, mode="single")
            await game.run()
        elif menu_choice == "VS._AI":
            # Start AI opponent game
            game = Game(screen, mode="ai")
            await game.run()
        elif menu_choice == "MULTIPLAYER":
            # Start multiplayer game
            game = Game(screen, mode="multiplayer")
            await game.run()
    
    pygame.quit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
