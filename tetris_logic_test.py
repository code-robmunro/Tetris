# tetris_logic_test.py
from piece_data import PieceType, PIECE_SHAPES, WALL_KICKS
from piece import Piece, PieceState
from board import Board

def minimal_board_setup():
    """Create a board without graphics, just the grid."""
    board = Board.__new__(Board)  # bypass __init__
    board.grid = [[0 for _ in range(20)] for _ in range(10)]
    board.current_piece = None
    board.moved_this_frame = False
    board.rotated_this_frame = False
    return board

def test_hard_drop_and_lock():
    board = minimal_board_setup()
    piece = Piece(PieceType.T)
    piece.x = 4
    piece.y = 0

    board.current_piece = piece

    # Simulate a hard drop
    offset = board.find_lowest_valid_move()
    print(f"Hard drop offset: {offset}")
    piece.move(0, offset)
    piece.state = PieceState.LOCKED
    board.lock_piece()

    # Verify piece cells are in grid
    for x, y, val in piece.iter_cells():
        if val == 0:
            continue
        bx, by = piece.x + x, piece.y + y
        assert board.grid[bx][by] != 0, f"Cell {bx},{by} not locked properly"

    print("Hard drop and lock test passed!")

def test_wall_kick():
    board = minimal_board_setup()
    piece = Piece(PieceType.J)
    piece.x = 0  # near left wall
    piece.y = 0

    board.current_piece = piece

    old_x, old_y = piece.x, piece.y
    piece.rotate_cw()
    success = False
    for dx, dy in WALL_KICKS[piece.piece_type].get((0, 1), [(0, 0)]):
        if board.is_position_valid(piece, dx=dx, dy=dy):
            piece.move(dx, dy)
            success = True
            break

    print(f"Wall kick rotation success: {success}")
    assert success, "Wall kick failed"

    print("Wall kick test passed!")

if __name__ == "__main__":
    test_hard_drop_and_lock()
    test_wall_kick()
