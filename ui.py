import pygame
import sys
import assets
import globals
import sprite_utils

class UI:
    def __init__(self):
        self.background = pygame.Surface((globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT))
        tetris_bit = assets.load_image(globals.TETRIS_BIT_16_SHEET)
        self.background_tile = sprite_utils.get_sprite(tetris_bit, 10 * 32, 0, 32, 32)
        for x in range(-16, globals.SCREEN_WIDTH, self.background_tile.get_width()):
            for y in range(-16, globals.SCREEN_HEIGHT, self.background_tile.get_height()):
                self.background.blit(self.background_tile, (x, y))

        horizontal_pipe = assets.load_image(globals.PLAY_AREA_HORIZONTAL_BORDER)
        vertical_pipe = assets.load_image(globals.PLAY_AREA_VERTICAL_BORDER)

        self.play_area_border = pygame.Surface((256, 512), pygame.SRCALPHA)

        for x in range(0, 256, horizontal_pipe.get_width()):
            self.play_area_border.blit(horizontal_pipe, (x, 0))
            self.play_area_border.blit(horizontal_pipe, (x, 512 - 16))

        for y in range(16, 512 - 16, vertical_pipe.get_height()):
            self.play_area_border.blit(vertical_pipe, (0, y))
            self.play_area_border.blit(vertical_pipe, (256 - 8, y))

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        screen.fill((0, 0, 0), ((32 * 9) - 16, (32 * 2) - 16, 256, 512))
        screen.blit(self.play_area_border, ((32 * 9) - 16, (32 * 2) - 16))