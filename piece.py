from piece_randomizer import PieceRandomizer
from piece_data import PieceType, PIECE_SHAPES
import globals

class Piece:
    randomizer = PieceRandomizer()

    def __init__(self, piece_type=None):
        self.piece_type = piece_type or self.randomizer.next_piece()
        self.rotation = 0
        self.shape = PIECE_SHAPES[self.piece_type][self.rotation]

        if self.piece_type.name == "I" or self.piece_type.name == "O":
            self.x = int((globals.BOARD_WIDTH / 2) - 2)
        else:
            self.x = int((globals.BOARD_WIDTH / 2) - 1)
        self.y = -2
    
    def iter_cells(self):
        """Yield x, y, and value for each cell in x-first order."""
        for x in range(len(self.shape[0])):       # columns
            for y in range(len(self.shape)):      # rows
                yield x, y, self.shape[y][x]

    def rotate_cw(self):
        self.rotation = (self.rotation + 1) % 4
        self.shape = PIECE_SHAPES[self.piece_type][self.rotation]
    
    def rotate_ccw(self):
        self.rotation = (self.rotation - 1) % 4
        self.shape = PIECE_SHAPES[self.piece_type][self.rotation]