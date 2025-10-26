import pygame
from piece import Piece, PieceState
from piece_data import PieceType, WALL_KICKS
import globals
import assets
import sprite_utils

class Board:
    MAX_LOCK_RESETS = 15
    
    def __init__(self):
        self.moved_this_frame = False
        self.rotated_this_frame = False

        # grid[x][y] - x-major storage
        self.grid = [[0 for _ in range(globals.BOARD_HEIGHT)] for _ in range(globals.BOARD_WIDTH)]
        self.piece_bits = self.load_piece_bits()
        self.play_area = pygame.Surface((globals.BOARD_WIDTH * globals.TETRIS_BIT_24_WIDTH,
                                         globals.BOARD_HEIGHT * globals.TETRIS_BIT_24_HEIGHT))
        self.current_piece = None

        self.lock_delay = 0.5          # how long a grounded piece waits before locking
        self.lock_elapsed = 0           # timer counting up
        self.grounded_last_frame = False  # was the piece grounded last frame?
        self.lock_resets = 0

        # # Preset pieces for testing
        # self.grid[0][19] = int(PieceType.L)
        # self.grid[1][19] = int(PieceType.L)
        # self.grid[2][19] = int(PieceType.L)
        # self.grid[2][18] = int(PieceType.L)
        # self.grid[4][19] = int(PieceType.O)
        # self.grid[5][19] = int(PieceType.O)
        # self.grid[4][18] = int(PieceType.O)
        # self.grid[5][18] = int(PieceType.O)

    def update(self, delta_time):
        if self.current_piece:
            self.current_piece.update(
                board=self,
                moved=self.moved_this_frame,
                rotated=self.rotated_this_frame
            )

            # Handle piece locking
            if self.current_piece.state == PieceState.LOCKED:
                self.lock_piece()

        # Reset flags after update
        self.moved_this_frame = False
        self.rotated_this_frame = False

    def draw(self, screen):
        self.play_area.fill((0,0,0))
        for x, row in enumerate(self.grid):
            for y, cell_value in enumerate(row):
                if cell_value:
                    self.draw_bit(cell_value, x, y)

        ghost_offset = self.find_lowest_valid_move()
        for x, y, value in self.current_piece.iter_cells():
            self.draw_bit(value, x + self.current_piece.x, y + self.current_piece.y + ghost_offset, ghost=True)

        for x, y, value in self.current_piece.iter_cells():
            self.draw_bit(value, x + self.current_piece.x, y + self.current_piece.y)

        screen.blit(self.play_area, (280, 64))

    # -----------------------------
    # Utility / Helper methods
    # -----------------------------
    def load_piece_bits(self):
        piece_bit_sheet = assets.load_image(globals.TETRIS_BIT_24_SHEET)
        piece_bits = []
        for i in range(7):
            piece_bits.append(sprite_utils.get_sprite(piece_bit_sheet, i * 24, 0, 24, 24))

        return piece_bits
    
    def draw_bit(self, cell_value, grid_x, grid_y, ghost=False):
        if cell_value == 0:
            return

        # Get the surface
        surf = self.piece_bits[cell_value - 1]

        # If ghost flag is set, make a transparent copy
        if ghost:
            surf = surf.copy()
            surf.set_alpha(64)  # 25% opacity (255 * 0.25 ≈ 64)

        self.play_area.blit(
            surf,
            (
                grid_x * globals.TETRIS_BIT_24_WIDTH,
                grid_y * globals.TETRIS_BIT_24_HEIGHT,
            )
        )

    def place_piece(self, piece: Piece):
        self.current_piece = piece
        if not self.is_position_valid():
            return False
        return True

    # -----------------------------
    # Logic methods
    # -----------------------------
    def can_move(self, dx, dy):
        """Return True if the current piece can move by (dx, dy)."""
        return self.is_position_valid(self.current_piece, dx, dy)

    def is_position_valid(self, piece=None, dx=0, dy=0):
        """Return True if `piece` at (piece.x+dx, piece.y+dy) is within bounds and not colliding."""
        if piece is None:
            piece = self.current_piece

        for cell_x, cell_y, value in piece.iter_cells():
            if value == 0:
                continue

            board_x = piece.x + cell_x + dx
            board_y = piece.y + cell_y + dy

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

    def find_lowest_valid_move(self):
        y = 1
        while self.can_move(0, y):
            y += 1

        return y - 1
    
    def lock_piece(self):
        for cell_x, cell_y, value in self.current_piece.iter_cells():
            if value == 0:
                continue

            board_x = self.current_piece.x + cell_x
            board_y = self.current_piece.y + cell_y

            if board_y < 0:
                # piece above the board — skip (game over will be handled in Game)
                continue

            self.grid[board_x][board_y] = value

        # clear timers
        self.lock_elapsed = 0
        self.grounded_last_frame = False

        self.clear_lines()

        # spawn a new piece
        self.current_piece = None

    def clear_lines(self):
        complete_lines = self.detect_complete_lines()
        if not complete_lines:
            return
        self.remove_lines(complete_lines)

    def detect_complete_lines(self):
        complete_lines = []
        for i in range(len(self.grid[0])):
            row = [col[i] for col in self.grid]
            for cell in row:
                if cell == 0:
                    break
            else:
                complete_lines.append(i)

        return complete_lines

    def remove_lines(self, complete_lines):
        for i in complete_lines:
            self.remove_row(i)
            
    def remove_row(self, row_index):
        for col in self.grid:
            del col[row_index]
            col.insert(0, 0)    

    # -----------------------------
    # Movement / rotation methods
    # -----------------------------
    def move_left(self):
        if self.can_move(-1, 0):
            self.current_piece.x -= 1
            self.moved_this_frame = True
                
    def move_right(self):
        if self.can_move(1, 0):
            self.current_piece.x += 1
            self.moved_this_frame = True

    def move_down(self):
        if self.can_move(0, 1):
            self.current_piece.y += 1
            self.moved_this_frame = True

    def rotate_cw(self):
        piece = self.current_piece
        old_rot = piece.rotation
        old_x, old_y = piece.x, piece.y
        grounded_before = piece.state == PieceState.GROUNDED

        piece.rotate_cw()
        new_rot = piece.rotation

        for dx, dy in WALL_KICKS[piece.piece_type].get((old_rot, new_rot), [(0, 0)]):
            if self.is_position_valid(dx=dx, dy=dy):
                piece.x += dx
                piece.y += dy

                # Only unground if rotation actually lifted the piece
                if grounded_before and piece.y < old_y:
                    piece.state = PieceState.FALLING
                    piece.lock_timer = 0
                    piece.lock_resets = 0
                    print("UNGROUNDED -> FALLING (rotation)")

                self.rotated_this_frame = True
                return

        # No valid kick worked — revert
        piece.rotate_ccw()
        piece.rotation = old_rot
        piece.x = old_x
        piece.y = old_y

    def rotate_ccw(self):
        piece = self.current_piece
        old_rot = piece.rotation
        old_x, old_y = piece.x, piece.y
        grounded_before = piece.state == PieceState.GROUNDED

        piece.rotate_ccw()
        new_rot = piece.rotation

        for dx, dy in WALL_KICKS[piece.piece_type].get((old_rot, new_rot), [(0, 0)]):
            if self.is_position_valid(dx=dx, dy=dy):
                piece.x += dx
                piece.y += dy

                # Only unground if rotation actually lifted the piece
                if grounded_before and piece.y < old_y:
                    piece.state = PieceState.FALLING
                    piece.lock_timer = 0
                    piece.lock_resets = 0
                    print("UNGROUNDED -> FALLING (rotation)")

                self.rotated_this_frame = True
                return

        # No valid kick worked — revert
        piece.rotate_cw()
        piece.rotation = old_rot
        piece.x = old_x
        piece.y = old_y

    def hard_drop(self):
        if not self.current_piece:
            return
        offset = self.find_lowest_valid_move()
        self.current_piece.y += offset
        self.moved_this_frame = True

        # Lock instantly
        self.current_piece.state = PieceState.LOCKED
        self.lock_piece()
        self.current_piece = None
