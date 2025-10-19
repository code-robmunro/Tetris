import pygame
from piece_types import PieceType
import globals
import assets
import sprite_utils

class Board:
    def __init__(self):
        self.grid = [[0 for _ in range(globals.BOARD_HEIGHT)] for _ in range(globals.BOARD_WIDTH)]
        self.grid[0][19] = int(PieceType.L)
        self.grid[1][19] = int(PieceType.L)
        self.grid[2][19] = int(PieceType.L)
        self.grid[2][18] = int(PieceType.L)
        self.grid[4][19] = int(PieceType.O)
        self.grid[5][19] = int(PieceType.O)
        self.grid[4][18] = int(PieceType.O)
        self.grid[5][18] = int(PieceType.O)
        self.piece_bits = self.load_piece_bits()
        self.play_area = pygame.Surface((globals.BOARD_WIDTH * globals.TETRIS_BIT_24_WIDTH,
                                         globals.BOARD_HEIGHT * globals.TETRIS_BIT_24_HEIGHT))

    def draw(self, screen):
        for x, row in enumerate(self.grid):
            for y, cell_value in enumerate(row):
                # if cell is 0, do nothing
                if cell_value == 1:
                    self.draw_bit(cell_value, x, y)
                elif cell_value == 2:
                    self.draw_bit(cell_value, x, y)
                elif cell_value == 3:
                    self.draw_bit(cell_value, x, y)
                elif cell_value == 4:
                    self.draw_bit(cell_value, x, y)
                elif cell_value == 5:
                    self.draw_bit(cell_value, x, y)
                elif cell_value == 6:
                    self.draw_bit(cell_value, x, y)
                elif cell_value == 7:
                    self.draw_bit(cell_value, x, y)


        screen.blit(self.play_area, (280, 64))

    def load_piece_bits(self):
        piece_bit_sheet = assets.load_image(globals.TETRIS_BIT_24_SHEET)
        piece_bits = []
        for i in range(7):
            piece_bits.append(sprite_utils.get_sprite(piece_bit_sheet, i * 24, 0, 24, 24))

        return piece_bits
    
    def draw_bit(self, cell_value, grid_x, grid_y):
        self.play_area.blit(
            self.piece_bits[cell_value],
            (
                grid_x * globals.TETRIS_BIT_24_WIDTH,
                grid_y * globals.TETRIS_BIT_24_HEIGHT,
            )
        )