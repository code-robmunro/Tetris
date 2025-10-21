from piece_randomizer import PieceRandomizer
from piece_data import PieceType, PIECE_SHAPES
import globals

class Piece:
    def __init__(self, piece_type=None):
        self.randomizer = PieceRandomizer()
        self.piece_type = piece_type or self.randomizer.next_piece()
        self.shape = PIECE_SHAPES[self.piece_type]
        self.rotation = 0
        if len(self.shape) == 4:
            self.x = (globals.BOARD_WIDTH / 2) - 2
        else:
            self.x = (globals.BOARD_WIDTH / 2) - 1
        self.y = -2
    
    def rotate_cw(piece):
        n = len(piece.shape)
        rotated = [[0]*n for _ in range(n)]
        for y in range(n):
            for x in range(n):
                rotated[x][n-1-y] = piece.shape[y][x]

        piece.shape = rotated
        return piece
    
    def rotate_ccw(piece):
        n = len(piece.shape)
        rotated = [[0]*n for _ in range(n)]
        for y in range(n):
            for x in range(n):
                rotated[n-1-x][y] = piece.shape[y][x]
        
        piece.shape = rotated
        return piece