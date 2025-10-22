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
        if self.can_move(0, 1):
            self.current_piece.y += 1
        else:
            self.lock_piece()
    
    def move_left(self):
        if self.can_move(-1, 0):
            self.current_piece.x -= 1
                
    def move_right(self):
        if self.can_move(1, 0):
            self.current_piece.x += 1
    
    def is_position_valid(self, dx=0, dy=0):
        """Return True if the piece at (x+dx, y+dy) is within board and not colliding."""
        for cell_x, cell_y, value in self.current_piece.iter_cells():
            if value == 0:
                continue

            board_x = self.current_piece.x + cell_x + dx
            board_y = self.current_piece.y + cell_y + dy

            # horizontal bounds
            if board_x < 0 or board_x >= globals.BOARD_WIDTH:
                return False

            # vertical bounds (bottom)
            if board_y >= globals.BOARD_HEIGHT:
                return False

            # above the board: allowed
            if board_y < 0:
                continue

            # overlap with grid
            if self.grid[board_x][board_y] != 0:
                return False

        return True

    def can_move(self, dx, dy):
        return self.is_position_valid(dx, dy)

    def rotate_cw(self):
        self.current_piece.rotate_cw()

        # check if the new orientation is valid
        if not self.is_position_valid():
            # simple wall kick: try moving left or right by 1
            for offset in (-1, 1):
                if self.is_position_valid(dx=offset):
                    self.current_piece.x += offset
                    return
            # revert if all wall kicks failed
            self.current_piece.rotate_ccw()

    def rotate_ccw(self):
        self.current_piece.rotate_ccw()

        if not self.is_position_valid():
            for offset in (-1, 1):
                if self.is_position_valid(dx=offset):
                    self.current_piece.x += offset
                    return
            self.current_piece.rotate_cw()

    def lock_piece(self):
        for cell_x, cell_y, value in self.current_piece.iter_cells():
            if value == 0:
                continue

            board_x = self.current_piece.x + cell_x
            board_y = self.current_piece.y + cell_y

            if board_y < 0:
                # piece above the board — skip for now
                continue

            self.grid[board_x][board_y] = value

        # spawn a new piece
        self.current_piece = None