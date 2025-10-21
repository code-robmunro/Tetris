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

# Sprite sheet indexing offsets
PIECE_COLOR_OFFSETS = {
    PieceType.O: 0,
    PieceType.S: globals.TETRIS_BIT_24_WIDTH,
    PieceType.T: globals.TETRIS_BIT_24_WIDTH * 2,
    PieceType.J: globals.TETRIS_BIT_24_WIDTH * 3,
    PieceType.L: globals.TETRIS_BIT_24_WIDTH * 4,
    PieceType.Z: globals.TETRIS_BIT_24_WIDTH * 5,
    PieceType.I: globals.TETRIS_BIT_24_WIDTH * 6,
}

PIECE_SHAPES = {
    PieceType.O:  [
        [0, 0, 0, 0],
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 0],
    ],
    PieceType.S: [
        [0, 2, 0],
        [2, 2, 0],
        [2, 0, 0],
    ],
    PieceType.T: [
        [0, 3, 0],
        [3, 3, 0],
        [0, 3, 0],
    ],
    PieceType.J: [
        [4, 4, 0],
        [0, 4, 0],
        [0, 4, 0],
    ],
    PieceType.L: [
        [0, 5, 0],
        [0, 5, 0],
        [5, 5, 0],
    ],
    PieceType.Z: [
        [6, 0, 0],
        [6, 6, 0],
        [0, 6, 0],
    ],
    PieceType.I: [
        [0, 7, 0, 0],
        [0, 7, 0, 0],
        [0, 7, 0, 0],
        [0, 7, 0, 0],
    ],
}