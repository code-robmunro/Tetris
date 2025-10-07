import pygame
import sys
import assets

class UI:
    def __init__(self):
        pass

    def draw(self, screen):
        cat = assets.load_image("assets/cat.png")

        # sprite = pygame.image.load("assets/graphics/cat.png").convert_alpha()
        # cat = pygame.transform.scale(cat, (500, 500))
        screen.blit(cat, (0, 0))
