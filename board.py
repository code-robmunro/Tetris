import pygame
from piece import Piece
from piece_data import PieceType
import globals
import assets
import sprite_utils

class Board:
    def __init__(self):
        # grid[x][y] - x-major storage
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

        for x, y, value in self.current_piece.iter_cells():
            self.draw_bit(value, x + self.current_piece.x, y + self.current_piece.y)

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
        if self.can_move_left():
            self.current_piece.x -= 1

    def can_move_left(self):
        for x, y, value in self.current_piece.iter_cells():
            if value is not 0 and self.current_piece.x + x <= 0:
                return False
        return True
                
    def move_right(self):
        if self.can_move_right():
            self.current_piece.x += 1

    def can_move_right(self):
        for x, y, value in self.current_piece.iter_cells():
            if value is not 0 and self.current_piece.x + x >= 9:
                return False
        return True
    
    def can_place(self):
        for x, y, value in self.current_piece.iter_cells():
            if value == 0:
                continue
            board_x = self.current_piece.x + x
            board_y = self.current_piece.y + y

            # check bounds
            if board_x < 0 or board_x >= globals.BOARD_WIDTH or board_y >= globals.BOARD_HEIGHT:
                return False

            # check existing blocks
            if self.grid[board_x][board_y] != 0:
                return False

        return True

    def rotate_cw(self):
        self.current_piece.rotate_cw()
        if not self.can_place():
            # simple wall kick
            for offset in (-1, 1):
                self.current_piece.x += offset
                if self.can_place():
                    return
                self.current_piece.x -= offset
            # revert if all failed
            self.current_piece.rotate_ccw()
            
    def rotate_ccw(self):
        self.current_piece.rotate_ccw()
        if not self.can_place():
            # simple wall kick
            for offset in (-1, 1):
                self.current_piece.x += offset
                if self.can_place():
                    return
                self.current_piece.x -= offset
            # revert if all failed
            self.current_piece.rotate_cw()