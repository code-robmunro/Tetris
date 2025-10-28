import pygame
import sys
import assets
import globals
import sprite_utils

class UI:
    def __init__(self):
        self.layout = pygame.Surface((globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT))        
        self.paint_layout()

    def draw(self, screen):
        screen.blit(self.layout, (0, 0))

    def paint_layout(self):
        background = assets.load_image(globals.BACKGROUND)
        self.layout.blit(background, (0, 0))

        play_area_border = assets.load_image(globals.PLAY_AREA_BORDER)
        self.layout.blit(play_area_border, globals.PLAY_AREA_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.PLAY_AREA_BOX_RECT)

        level_txt_border = assets.load_image(globals.LEVEL_TXT_BORDER)
        self.layout.blit(level_txt_border, globals.LEVEL_TXT_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.LEVEL_TXT_BOX_RECT)

        # Paint secondary first, so it is underneath primary
        next_piece_secondary_border = assets.load_image(globals.NEXT_PIECE_SECONDARY_BORDER)
        self.layout.blit(next_piece_secondary_border, globals.NEXT_PIECE_SECONDARY_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.NEXT_PIECE_SECONDARY_BOX_RECT)

        next_piece_border = assets.load_image(globals.NEXT_PIECE_BORDER)
        self.layout.blit(next_piece_border, globals.NEXT_PIECE_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.NEXT_PIECE_BOX_RECT)

        next_txt_border = assets.load_image(globals.NEXT_TXT_BORDER)
        self.layout.blit(next_txt_border, globals.NEXT_TXT_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.NEXT_TXT_BOX_RECT)

        held_piece_border = assets.load_image(globals.HELD_PIECE_BORDER)
        self.layout.blit(held_piece_border, globals.HELD_PIECE_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.HELD_PIECE_BOX_RECT)

        held_txt_border = assets.load_image(globals.HELD_TXT_BORDER)
        self.layout.blit(held_txt_border, globals.HELD_TXT_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.HELD_TXT_BOX_RECT)

        cpu_play_area_border = assets.load_image(globals.CPU_PLAY_AREA_BORDER)
        self.layout.blit(cpu_play_area_border, globals.CPU_PLAY_AREA_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.CPU_PLAY_AREA_BOX_RECT)

        cpu_avatar_border = assets.load_image(globals.CPU_AVATAR_BORDER)
        self.layout.blit(cpu_avatar_border, globals.CPU_AVATAR_BORDER_RECT.topleft)
        cpu_avatar_box = assets.load_image(globals.CPU_AVATAR_BOX)
        self.layout.blit(cpu_avatar_box, globals.CPU_AVATAR_BOX_RECT.topleft)
        cpu_avatar = assets.load_image(globals.CPU_AVATAR_CAT)
        self.layout.blit(cpu_avatar, globals.CPU_AVATAR_CAT_RECT.topleft)

        score_border = assets.load_image(globals.SCORE_BORDER)
        self.layout.blit(score_border, globals.SCORE_BORDER_RECT.topleft)
        self.layout.fill((0, 0, 0), globals.SCORE_BOX_RECT)
