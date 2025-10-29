import pygame
import assets
import globals
from piece import Piece, PieceState
from piece_data import PieceType
from piece_randomizer import PieceRandomizer

class UI:
    randomizer = PieceRandomizer()

    def __init__(self):
        self.ui = pygame.Surface((globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT))
        self.next_pieces = []

        self.paint_layout()

    def update(self):
        self.next_pieces = self.randomizer.next_pieces()

    def draw(self, screen):
        screen.blit(self.ui, (0, 0))
        self.paint_layout()
        self.draw_next_pieces()

    def paint_layout(self):
        background = assets.load_image(globals.BACKGROUND)
        self.ui.blit(background, (0, 0))

        play_area_border = assets.load_image(globals.PLAY_AREA_BORDER)
        self.ui.blit(play_area_border, globals.PLAY_AREA_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.PLAY_AREA_BOX_RECT)

        level_txt_border = assets.load_image(globals.LEVEL_TXT_BORDER)
        self.ui.blit(level_txt_border, globals.LEVEL_TXT_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.LEVEL_TXT_BOX_RECT)

        # Paint secondary first, so it is underneath primary
        next_piece_secondary_border = assets.load_image(globals.NEXT_PIECE_SECONDARY_BORDER)
        self.ui.blit(next_piece_secondary_border, globals.NEXT_PIECE_SECONDARY_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.NEXT_PIECE_SECONDARY_BOX_RECT)

        next_piece_border = assets.load_image(globals.NEXT_PIECE_BORDER)
        self.ui.blit(next_piece_border, globals.NEXT_PIECE_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.NEXT_PIECE_BOX_RECT)

        next_txt_border = assets.load_image(globals.NEXT_TXT_BORDER)
        self.ui.blit(next_txt_border, globals.NEXT_TXT_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.NEXT_TXT_BOX_RECT)

        held_piece_border = assets.load_image(globals.HELD_PIECE_BORDER)
        self.ui.blit(held_piece_border, globals.HELD_PIECE_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.HELD_PIECE_BOX_RECT)

        held_txt_border = assets.load_image(globals.HELD_TXT_BORDER)
        self.ui.blit(held_txt_border, globals.HELD_TXT_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.HELD_TXT_BOX_RECT)

        cpu_play_area_border = assets.load_image(globals.CPU_PLAY_AREA_BORDER)
        self.ui.blit(cpu_play_area_border, globals.CPU_PLAY_AREA_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.CPU_PLAY_AREA_BOX_RECT)

        cpu_avatar_border = assets.load_image(globals.CPU_AVATAR_BORDER)
        self.ui.blit(cpu_avatar_border, globals.CPU_AVATAR_BORDER_RECT.topleft)
        cpu_avatar_box = assets.load_image(globals.CPU_AVATAR_BOX)
        self.ui.blit(cpu_avatar_box, globals.CPU_AVATAR_BOX_RECT.topleft)
        cpu_avatar = assets.load_image(globals.CPU_AVATAR_CAT)
        self.ui.blit(cpu_avatar, globals.CPU_AVATAR_CAT_RECT.topleft)

        score_border = assets.load_image(globals.SCORE_BORDER)
        self.ui.blit(score_border, globals.SCORE_BORDER_RECT.topleft)
        self.ui.fill((0, 0, 0), globals.SCORE_BOX_RECT)

    def draw_next_pieces(self):
        # piece = Piece(self.next_pieces[0], piece_bit_size=16)
        for i, piece_type in enumerate(self.next_pieces):
            piece = Piece(piece_type, piece_bit_size=16)
            if piece.piece_type in (PieceType.S, PieceType.T, PieceType.J, PieceType.L, PieceType.Z):
                x = globals.NEXT_PIECE_BOX_RECT.centerx - 24
                y = globals.NEXT_PIECE_BOX_RECT.centery - 16
            elif piece.piece_type == PieceType.O:
                x = globals.NEXT_PIECE_BOX_RECT.centerx - 32
                y = globals.NEXT_PIECE_BOX_RECT.centery - 32
            else: # the PieceType is 'I'
                x = globals.NEXT_PIECE_BOX_RECT.centerx - 32
                y = globals.NEXT_PIECE_BOX_RECT.centery - 24

            if i > 0:
                y = y + 22 + (50 * i)
            piece.draw(self.ui, x_offset=x, y_offset=y, use_grid=False)