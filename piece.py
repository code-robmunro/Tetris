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
        self.PIECE_SHAPES = PIECE_SHAPES

        # Spawn position
        if self.piece_type.name in ("I", "O"):
            self.x = int((globals.BOARD_WIDTH / 2) - 2)
        else:
            self.x = int((globals.BOARD_WIDTH / 2) - 1)
        self.y = -2

        self.last_x = self.x
        self.last_y = self.y

        self.state = PieceState.SPAWNING
        self.lock_timer = 0
        self.lock_resets = 0

    def update(self, board, moved=False, rotated=False):
        """Call each frame to handle gravity, grounding, lock delay, and locking."""
        # Store previous frame position
        self.last_x = self.x
        self.last_y = self.y

        # Gravity / Grounding
        if self.state in (PieceState.SPAWNING, PieceState.FALLING):
            if self.is_grounded(board):
                self.state = PieceState.GROUNDED
                self.lock_timer = 0
            else:
                self.state = PieceState.FALLING

        # Lock handling
        elif self.state == PieceState.GROUNDED:
            self.lock_timer += 1

            # Reset lock timer if moved/rotated meaningfully
            if (moved or rotated) and self.lock_resets < self.MAX_LOCK_RESETS:
                if self.x != self.last_x or self.y != self.last_y:
                    self.lock_timer = 0
                    self.lock_resets += 1

            # Lock if grounded and timer exceeded
            if self.is_grounded(board) and self.lock_timer >= self.LOCK_DELAY_FRAMES:
                self.state = PieceState.LOCKED

    def iter_cells(self):
        """Yield x, y, value for each occupied cell (x-major)."""
        for x in range(len(self.shape[0])):
            for y in range(len(self.shape)):
                yield x, y, self.shape[y][x]

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def rotate_cw(self):
        self.rotation = (self.rotation + 1) % 4
        self.shape = self.PIECE_SHAPES[self.piece_type][self.rotation]

    def rotate_ccw(self):
        self.rotation = (self.rotation - 1) % 4
        self.shape = self.PIECE_SHAPES[self.piece_type][self.rotation]

    # -----------------------------
    # Gravity / Lock Helpers
    # -----------------------------
    def can_move_down(self, board):
        for x, y, val in self.iter_cells():
            if val == 0:
                continue
            bx = self.x + x
            by = self.y + y + 1
            if by >= globals.BOARD_HEIGHT:
                return False
            if by >= 0 and board.grid[bx][by] != 0:
                return False
        return True

    def is_grounded(self, board):
        """True if the piece cannot move down safely."""
        for x in range(len(self.shape[0])):
            for y in reversed(range(len(self.shape))):
                if self.shape[y][x] == 0:
                    continue
                bx = self.x + x
                by = self.y + y + 1
                if by >= globals.BOARD_HEIGHT:
                    return True
                if by >= 0 and board.grid[bx][by] != 0:
                    return True
                break
        return False