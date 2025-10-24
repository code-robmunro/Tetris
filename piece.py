from piece_randomizer import PieceRandomizer
from piece_data import PieceType, PIECE_SHAPES
import globals
from enum import Enum, auto

class PieceState(Enum):
    SPAWNING = auto()
    FALLING = auto()
    GROUNDED = auto()
    LOCKED = auto()

class Piece:
    randomizer = PieceRandomizer()
    MAX_LOCK_RESETS = 15
    LOCK_DELAY_FRAMES = 30  # ~0.5 sec at 60fps

    def __init__(self, piece_type=None):
        self.piece_type = piece_type or self.randomizer.next_piece()
        self.rotation = 0
        self.shape = PIECE_SHAPES[self.piece_type][self.rotation]

        if self.piece_type.name in ("I", "O"):
            self.x = int((globals.BOARD_WIDTH / 2) - 2)
        else:
            self.x = int((globals.BOARD_WIDTH / 2) - 1)
        self.y = -2

        self.last_x = self.x
        self.last_y = self.y

        self.state = PieceState.SPAWNING
        print("------\nSPAWNING")
        self.lock_timer = 0
        self.lock_resets = 0

    def iter_cells(self):
        """Yield x, y, and value for each cell in x-first order."""
        for x in range(len(self.shape[0])):  # columns
            for y in range(len(self.shape)):  # rows
                yield x, y, self.shape[y][x]

    def rotate_cw(self):
        self.rotation = (self.rotation + 1) % 4
        self.shape = PIECE_SHAPES[self.piece_type][self.rotation]

    def rotate_ccw(self):
        self.rotation = (self.rotation - 1) % 4
        self.shape = PIECE_SHAPES[self.piece_type][self.rotation]

    # -----------------------------
    # Gravity and lock handling
    # -----------------------------
    def can_move_down(self, board):
        """Return True if piece can move down by 1 without collision."""
        for x, y, val in self.iter_cells():
            if not val:
                continue
            board_x = self.x + x
            board_y = self.y + y + 1

            # skip cells above the board
            if board_y < 0:
                continue

            # bottom boundary
            if board_y >= globals.BOARD_HEIGHT:
                return False

            # x-major grid collision check
            if board.grid[board_x][board_y] != 0:
                return False

        return True
    
    def is_grounded(self, board):
        """Return True if the piece cannot move down (any bottom-most cell collides)."""
        for x in range(len(self.shape[0])):  # each column
            for y in reversed(range(len(self.shape))):  # bottom-to-top
                if self.shape[y][x] == 0:
                    continue
                board_x = self.x + x
                board_y = self.y + y + 1
                if board_y >= globals.BOARD_HEIGHT:
                    return True  # bottom of board
                if board.grid[board_x][board_y] != 0:
                    return True  # collision with stack
                break  # stop at first filled cell in this column
        return False

    def update(self, board, moved=False, rotated=False):
        """Call each frame to handle gravity, lock delay, and locking."""
        # Store previous frame position
        self.last_x = self.x
        self.last_y = self.y

        if self.state in (PieceState.SPAWNING, PieceState.FALLING):
            if self.is_grounded(board):
                self.state = PieceState.GROUNDED
                self.lock_timer = 0
                print("GROUNDED")
            else:
                if self.state != PieceState.FALLING:
                    print("FALLING")
                self.state = PieceState.FALLING

        elif self.state == PieceState.GROUNDED:
            self.lock_timer += 1

            # Reset lock timer only if piece moved/rotated meaningfully
            if (moved or rotated) and self.lock_resets < self.MAX_LOCK_RESETS:
                if self.x != self.last_x or self.y != self.last_y:
                    self.lock_timer = 0
                    self.lock_resets += 1
                    print(f"Lock timer reset ({self.lock_resets}/{self.MAX_LOCK_RESETS})")

            # Only lock if actually still grounded
            if self.is_grounded(board) and self.lock_timer >= self.LOCK_DELAY_FRAMES:
                self.state = PieceState.LOCKED
                print("LOCKED")
            # No ungrounding here — rotations already handle it
