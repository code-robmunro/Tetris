import pygame

from eventbus import EventBus
from piece import Piece, PieceState
from piece_data import PieceType, WALL_KICKS
import globals
import assets


class Board:
    MAX_LOCK_RESETS = 15

    def __init__(self, event_bus: EventBus, piece_randomizer):
        self.event_bus = event_bus
        self.piece_randomizer = piece_randomizer
        self.moved_this_frame = False
        self.rotated_this_frame = False
        self.recently_used_hold = False
        self.line_clear_animation = None  # Stores animation state
        self.animation_timer = 0
        self.animation_duration = 0.4  # 400ms animation

        # x-major grid
        self.grid = [[0 for _ in range(globals.BOARD_HEIGHT)] for _ in range(globals.BOARD_WIDTH)]
        self.piece_bits = assets.load_piece_sprites(globals.TETRIS_BIT_24_SHEET)
        self.play_area = pygame.Surface(
            (globals.BOARD_WIDTH * globals.TETRIS_BIT_24_WIDTH,
             globals.BOARD_HEIGHT * globals.TETRIS_BIT_24_HEIGHT)
        )

        self.current_piece = None
        self.held_piece = None

        # Cache ghost piece position
        self.cached_ghost_offset = 0
        self.last_piece_x = None
        self.last_piece_y = None
        self.last_piece_rotation = None

        # Rotation spin bug
        # self.setup_t_or_z_spin()

    # -----------------------------
    # Update / Draw
    # -----------------------------

    def update(self, delta_time):
        lock_info = {
            "lines_cleared": 0,
            "board_full": False,
        }

        if self.current_piece:
            self.current_piece.update(
                board=self,
                moved=self.moved_this_frame,
                rotated=self.rotated_this_frame
            )

            if self.current_piece.state == PieceState.LOCKED:
                lock_info = self.lock_piece()

        self.moved_this_frame = False
        self.rotated_this_frame = False
        return lock_info

    def draw(self, screen):
        """Draw the board with line clear animations"""
        self.play_area.fill((0, 0, 0))

        # Draw normal blocks
        for x, col in enumerate(self.grid):
            for y, val in enumerate(col):
                if val:
                    # Check if this row is being animated
                    if self.line_clear_animation and y in self.line_clear_animation['rows']:
                        self.draw_animated_bit(val, x, y)
                    else:
                        self.draw_bit(val, x, y)

        # Draw ghost piece (with caching)
        if self.current_piece:
            ghost_offset = self.get_cached_ghost_offset()
            self.current_piece.draw(self.play_area, y_offset=ghost_offset, ghost=True)
            self.current_piece.draw(self.play_area)

        screen.blit(self.play_area, globals.PLAY_AREA_BOX_RECT.topleft)

    # -----------------------------
    # Utility
    # -----------------------------

    def draw_bit(self, val, grid_x, grid_y, ghost=False):
        surf = self.piece_bits[val - 1]
        if ghost:
            surf = surf.copy()
            surf.set_alpha(64)
        self.play_area.blit(
            surf,
            (grid_x * globals.TETRIS_BIT_24_WIDTH,
             grid_y * globals.TETRIS_BIT_24_HEIGHT)
        )

    def draw_animated_bit(self, val, gridx, gridy):
        """Draw a bit with animation effects during line clear"""
        surf = self.piece_bits[val - 1].copy()
        anim = self.line_clear_animation

        if anim['phase'] == 0:  # Flash phase
            # Alternate between white flash and normal every 3 frames
            flash_cycle = int(anim['timer'] * 60) % 6  # 60 fps
            if flash_cycle < 3:
                # Create white flash overlay
                white_overlay = pygame.Surface((globals.TETRIS_BIT_24_WIDTH, globals.TETRIS_BIT_24_HEIGHT))
                white_overlay.fill((255, 255, 255))
                surf.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_ADD)

        elif anim['phase'] == 1:  # Fade phase
            # Fade out
            progress = (anim['timer'] - 0.2) / 0.15  # 0.0 to 1.0
            alpha = int(255 * (1 - progress))
            surf.set_alpha(alpha)

        self.play_area.blit(
            surf,
            (gridx * globals.TETRIS_BIT_24_WIDTH, gridy * globals.TETRIS_BIT_24_HEIGHT)
        )

    # -----------------------------
    # Placement / Validation
    # -----------------------------

    def place_piece(self, piece: Piece):
        if self.current_piece is not None:
            print(f"[DEBUG] place_piece FAILED: current_piece is not None! current_piece={self.current_piece.piece_type if self.current_piece else None}")
            return False  # Explicitly return False instead of None
        self.current_piece = piece
        is_valid = self.is_position_valid()
        print(f"[DEBUG] place_piece: Placing {piece.piece_type} at ({piece.x}, {piece.y}), valid={is_valid}")
        return is_valid

    def can_move(self, dx, dy):
        return self.is_position_valid(self.current_piece, dx, dy)

    def is_position_valid(self, piece=None, dx=0, dy=0):
        if piece is None:
            piece = self.current_piece

        for cell_x, cell_y, value in piece.iter_cells():
            if value == 0:
                continue

            board_x = piece.x + cell_x + dx
            board_y = piece.y + cell_y + dy

            if board_x < 0 or board_x >= globals.BOARD_WIDTH:
                return False
            if board_y >= globals.BOARD_HEIGHT:
                return False
            if board_y < 0:
                continue  # allow above board
            if self.grid[board_x][board_y] != 0:
                return False

        return True

    def find_lowest_valid_move(self):
        y = 1
        while self.can_move(0, y):
            y += 1
        offset = y - 1
        return offset

    def get_cached_ghost_offset(self):
        """Get ghost piece offset, only recalculating if piece has moved"""
        if not self.current_piece:
            return 0

        # Check if piece position or rotation has changed
        piece_changed = (
            self.current_piece.x != self.last_piece_x or
            self.current_piece.y != self.last_piece_y or
            self.current_piece.rotation_state != self.last_piece_rotation
        )

        if piece_changed:
            # Recalculate ghost position
            self.cached_ghost_offset = self.find_lowest_valid_move()
            self.last_piece_x = self.current_piece.x
            self.last_piece_y = self.current_piece.y
            self.last_piece_rotation = self.current_piece.rotation_state

        return self.cached_ghost_offset

    # -----------------------------
    # Locking / Clearing
    # -----------------------------

    def lock_piece(self):
        locked_piece_type = self.current_piece.piece_type
        for x, y, val in self.current_piece.iter_cells():
            if val == 0:
                continue
            bx = self.current_piece.x + x
            by = self.current_piece.y + y
            if 0 <= bx < globals.BOARD_WIDTH and 0 <= by < globals.BOARD_HEIGHT:
                self.grid[bx][by] = val

        self.current_piece = None
        print(f"[DEBUG] lock_piece: Locked {locked_piece_type}, set current_piece to None")
        self.recently_used_hold = False
        return self.clear_lines()

    def clear_lines(self):
        """Detect complete lines and start clear animation"""
        complete_lines = self.detect_complete_lines()

        if complete_lines:
            # Start the animation
            self.line_clear_animation = {
                'rows': complete_lines,
                'phase': 0,  # 0=flash, 1=fade, 2=remove
                'timer': 0
            }
            return {"lines_cleared": 0, "board_full": False}  # Don't count yet

        return {"lines_cleared": 0, "board_full": False}

    def update_line_clear_animation(self, delta_time):
        """Update the line clear animation state"""
        if self.line_clear_animation is None:
            return None

        anim = self.line_clear_animation
        anim['timer'] += delta_time

        # Phase 0: Flash effect (0-0.2s)
        if anim['timer'] < 0.2:
            anim['phase'] = 0
        # Phase 1: Fade out effect (0.2-0.35s)
        elif anim['timer'] < 0.35:
            anim['phase'] = 1
        # Phase 2: Remove lines (0.35-0.4s)
        else:
            anim['phase'] = 2
            # Actually remove the lines (from bottom to top to preserve indices)
            # for row in sorted(anim['rows'], reverse=True):
            #     self.remove_row(row)

            # Actually remove the lines
            for row in anim['rows']:
                self.remove_row(row)

            # Return the clear info
            result = {"lines_cleared": len(anim['rows']), "board_full": False}
            self.line_clear_animation = None
            return result

        return None

    def detect_complete_lines(self):
        complete_lines = []
        for y in range(globals.BOARD_HEIGHT):
            if all(self.grid[x][y] != 0 for x in range(globals.BOARD_WIDTH)):
                complete_lines.append(y)
        return complete_lines

    def remove_row(self, row):
        for x in range(globals.BOARD_WIDTH):
            del self.grid[x][row]
            self.grid[x].insert(0, 0)

    # -----------------------------
    # Movement / Rotation
    # -----------------------------

    def move_left(self):
        if not self.current_piece:
            return False
        if self.can_move(-1, 0):
            self.current_piece.move(-1, 0)
            self.moved_this_frame = True
            return True
        return False

    def move_right(self):
        if not self.current_piece:
            return False
        if self.can_move(1, 0):
            self.current_piece.move(1, 0)
            self.moved_this_frame = True
            return True
        return False

    def move_down(self):
        if not self.current_piece:
            return False
        if self.can_move(0, 1):
            self.current_piece.move(0, 1)
            self.moved_this_frame = True
            return True
        return False

    def rotate_cw(self):
        return self._rotate(True)

    def rotate_ccw(self):
        return self._rotate(False)

    def _rotate(self, clockwise=True):
        if not self.current_piece:
            return False
        piece = self.current_piece
        old_rot = piece.rotation
        old_x, old_y = piece.x, piece.y
        grounded_before = piece.state == PieceState.GROUNDED

        if clockwise:
            piece.rotate_cw()
            new_rot = piece.rotation
        else:
            piece.rotate_ccw()
            new_rot = piece.rotation

        # Try wall kicks
        for dx, dy in WALL_KICKS.get(piece.piece_type, {}).get((old_rot, new_rot), [(0, 0)]):
            piece.x = old_x + dx
            piece.y = old_y + dy

            if self.is_position_valid(piece):
                # Clamp bottom if necessary
                max_y = max((cy for _, cy, val in piece.iter_cells() if val), default=0)
                if piece.y + max_y >= globals.BOARD_HEIGHT:
                    piece.y = globals.BOARD_HEIGHT - (max_y + 1)

                if grounded_before and piece.y < old_y:
                    piece.state = PieceState.FALLING
                    piece.lock_timer = 0
                    piece.lock_resets = 0

                self.rotated_this_frame = True
                return True

        # Revert if no kick worked
        piece.rotation = old_rot
        piece.shape = piece.PIECE_SHAPES[piece.piece_type][old_rot]
        piece.x, piece.y = old_x, old_y
        return False

    # -----------------------------
    # Hard Drop
    # -----------------------------

    def hard_drop(self):
        if not self.current_piece:
            return {"lines_cleared": 0, "board_full": False}

        offset = self.find_lowest_valid_move()
        self.current_piece.move(0, offset)
        self.current_piece.state = PieceState.LOCKED
        lock_info = self.lock_piece()  # capture the lines cleared / board state
        return lock_info

    def hold_piece(self):
        if not self.recently_used_hold:
            if self.held_piece:
                self.current_piece, self.held_piece = self.held_piece, self.current_piece
                self.current_piece.set_default_values()
                self.event_bus.emit("piece_held_or_swapped", self.held_piece)
            else:
                self.held_piece, self.current_piece = self.current_piece, None
                self.event_bus.emit("piece_held_or_swapped", self.held_piece)

            self.recently_used_hold = True

    def setup_t_or_z_spin(self):
        self.current_piece = Piece(PieceType.T, randomizer=self.piece_randomizer)
        self.grid[2][19] = int(PieceType.T)
        self.grid[1][18] = int(PieceType.T)
        self.grid[2][18] = int(PieceType.T)
        self.grid[2][17] = int(PieceType.T)
        self.grid[6][19] = int(PieceType.Z)
        self.grid[5][18] = int(PieceType.Z)
        self.grid[6][18] = int(PieceType.Z)
        self.grid[5][17] = int(PieceType.Z)
