from enum import IntEnum
import globals

class PieceType(IntEnum):
    O = 1
    S = 2
    T = 3
    J = 4
    L = 5
    Z = 6
    I = 7

PIECE_COLOR_OFFSETS = {
    PieceType.O: 0,
    PieceType.S: globals.TETRIS_BIT_16_WIDTH,
    PieceType.T: globals.TETRIS_BIT_16_WIDTH * 2,
    PieceType.J: globals.TETRIS_BIT_16_WIDTH * 3,
    PieceType.L: globals.TETRIS_BIT_16_WIDTH * 4,
    PieceType.Z: globals.TETRIS_BIT_16_WIDTH * 5,
    PieceType.I: globals.TETRIS_BIT_16_WIDTH * 6
}