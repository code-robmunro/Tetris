import pygame
from piece import Piece
from piece_data import PieceType
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
        self.current_piece = None

    def draw(self, screen):
        self.play_area.fill((0,0,0))
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

        for x, row in enumerate(self.current_piece.shape):
            for y, cell_value in enumerate(self.current_piece.shape):
                self.draw_bit(self.current_piece.shape[x][y], x + self.current_piece.x, y + self.current_piece.y)


        screen.blit(self.play_area, (280, 64))

    def update(self):
        pass

    def load_piece_bits(self):
        piece_bit_sheet = assets.load_image(globals.TETRIS_BIT_24_SHEET)
        piece_bits = []
        for i in range(7):
            piece_bits.append(sprite_utils.get_sprite(piece_bit_sheet, i * 24, 0, 24, 24))

        return piece_bits
    
    def draw_bit(self, cell_value, grid_x, grid_y):
        # We are off by 1 on cell values, so we subtract 1 later.
        # This means that 0 becomes 6 and we end up rendering a block instead of empty space.
        # This check prevents that but we should find a real solution.
        if cell_value == 0: 
            return

        self.play_area.blit(
            self.piece_bits[cell_value - 1],
            (
                grid_x * globals.TETRIS_BIT_24_WIDTH,
                grid_y * globals.TETRIS_BIT_24_HEIGHT,
            )
        )

    def place_piece(self, piece: Piece):
        self.current_piece = piece

    def move_down(self):
        if self.current_piece is not None and self.current_piece.y < 19:
            print("Current Y: " + str(self.current_piece.y))
            print("Current X: " + str(self.current_piece.x))
            print("Shape: \n" + str(self.current_piece.shape))
            self.current_piece.y += 1

    def move_left(self):
        self.current_piece.x -= 1

    def move_right(self):
        self.current_piece.x += 1

    def rotate_cw(self):
        self.current_piece.rotate_cw()
    
    def rotate_ccw(self):
        self.current_piece.rotate_ccw()