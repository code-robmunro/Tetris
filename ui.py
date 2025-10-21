import pygame
import sys
import assets
import globals
import sprite_utils

class UI:
    def __init__(self):
        self.layout = pygame.Surface((globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT))        
        background = assets.load_image(globals.BACKGROUND)
        self.layout.blit(background, (0, 0))

        play_area_border = assets.load_image(globals.PLAY_AREA_BORDER)
        self.layout.blit(play_area_border, (274, 60))
        self.layout.fill((0, 0, 0), (280, 66, 240, 480))

        level_txt_border = assets.load_image(globals.LEVEL_TXT_BORDER)
        self.layout.blit(level_txt_border, (285, 15))
        self.layout.fill((0, 0, 0), (289, 19, 221, 36))

        next_piece_border = assets.load_image(globals.NEXT_PIECE_BORDER)
        self.layout.blit(next_piece_border, (545, 216))
        self.layout.fill((0, 0, 0), (551, 222, 96, 96))

        next_txt_border = assets.load_image(globals.NEXT_TXT_BORDER)
        self.layout.blit(next_txt_border, (558, 186))
        self.layout.fill((0, 0, 0), (562, 190, 73, 20))

        point_value_border = assets.load_image(globals.POINT_VALUE_BORDER)
        self.layout.blit(point_value_border, (44, 120))
        self.layout.fill((0, 0, 0), (48, 124, 205, 422))

        score_border = assets.load_image(globals.SCORE_BORDER)
        self.layout.blit(score_border, (543, 15))
        self.layout.fill((0, 0, 0), (547, 19, 187, 116))

    def draw(self, screen):
        screen.blit(self.layout, (0, 0))