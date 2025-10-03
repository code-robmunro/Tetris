import pygame
from sprite import get_sprite
from settings import TETRIS_BIT_SHEET, TETRIS_BIT_WIDTH, TETRIS_BIT_HEIGHT

class Board:
    def __init__(self):
        self.width = 10
        self.height = 20
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def draw(self, screen):
        sprite = pygame.image.load("assets/graphics/cat.png").convert_alpha()
        sprite_scaled = pygame.transform.scale(sprite, (500, 500))
        screen.blit(sprite_scaled, (0, 0))


        for row in range(self.height):
            for col in range(self.width):
                if self.grid[row][col] != 0:
                    sprite = get_sprite(TETRIS_BIT_SHEET, self.grid[row][col], 0, TETRIS_BIT_WIDTH, TETRIS_BIT_HEIGHT)
                    screen.blit(sprite, (col * TETRIS_BIT_WIDTH, row * TETRIS_BIT_HEIGHT))