import pygame
import globals
from board import Board
from piece import Piece, PieceState
from piece_data import PieceType
import assets

# -----------------------------
# Minimal globals for testing
# -----------------------------
globals.BOARD_WIDTH = 10
globals.BOARD_HEIGHT = 20
globals.TETRIS_BIT_24_WIDTH = 24
globals.TETRIS_BIT_24_HEIGHT = 24
globals.TETRIS_BIT_24_SHEET = "dummy.png"

# Patch assets.load_image to avoid file loading
assets.load_image = lambda path: pygame.Surface((globals.BOARD_WIDTH*24, globals.BOARD_HEIGHT*24))

# -----------------------------
# Helper functions
# -----------------------------
def check_no_overlap(board):
    """Return True if current piece does not overlap locked cells."""
    if not board.current_piece:
        return True
    for x, y, val in board.current_piece.iter_cells():
        if val == 0:
            continue
        bx = board.current_piece.x + x
        by = board.current_piece.y + y
        if 0 <= by < globals.BOARD_HEIGHT:
            if board.grid[bx][by] != 0:
                return False
    return True

def check_in_bounds(board):
    """Return True if piece is entirely within horizontal bounds and not below floor."""
    piece = board.current_piece
    if not piece:
        return True
    for x, y, val in piece.iter_cells():
        if val == 0:
            continue
        bx = piece.x + x
        by = piece.y + y
        if bx < 0 or bx >= globals.BOARD_WIDTH or by >= globals.BOARD_HEIGHT:
            return False
    return True

# -----------------------------
# Automated test routine
# -----------------------------
def test_wall_kick_and_lock():
    board = Board()

    # Fill bottom row to test collision
    for x in range(globals.BOARD_WIDTH):
        board.grid[x][globals.BOARD_HEIGHT-1] = 1

    # Spawn T piece near left wall
    piece = Piece(PieceType.T)
    piece.x = 0
    piece.y = 16
    board.place_piece(piece)

    # Rotate CW (should perform wall kick)
    board.rotate_cw()
    assert check_no_overlap(board), "Overlap detected after rotation CW near left wall"
    assert check_in_bounds(board), "Piece out of bounds after rotation CW near left wall"

    # Move piece right 3 and rotate CCW
    board.move_right()
    board.move_right()
    board.move_right()
    board.rotate_ccw()
    assert check_no_overlap(board), "Overlap detected after rotation CCW near stack"
    assert check_in_bounds(board), "Piece out of bounds after rotation CCW near stack"

    # Soft drop until grounded
    while board.can_move(0, 1):
        board.move_down()
        piece.update(board)
        assert check_no_overlap(board), "Overlap detected during soft drop"

    # Verify piece is grounded
    piece.update(board)
    assert piece.state in (PieceState.GROUNDED, PieceState.LOCKED), "Piece not grounded properly"

    # Hard drop and lock
    board.hard_drop()
    for x, y, val in piece.iter_cells():
        if val == 0:
            continue
        bx = piece.x + x
        by = piece.y + y
        if 0 <= by < globals.BOARD_HEIGHT:
            assert board.grid[bx][by] != 0, "Piece did not lock correctly"

    print("All automated wall kick and lock tests passed.")

if __name__ == "__main__":
    pygame.init()
    test_wall_kick_and_lock()
    pygame.quit()
