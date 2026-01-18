import globals

from piece import Piece

from piece_data import PieceType, PIECE_SHAPES

# Set to True to enable verbose AI debugging
AI_DEBUG = False


def debug_print(*args, **kwargs):
    """Print only if AI_DEBUG is enabled"""
    if AI_DEBUG:
        print(*args, **kwargs)


class AIOpponent:
    """Advanced Tetris AI with T-spin detection and better decision making"""

    # Optimized weights based on genetic algorithm tuning from Tetris research
    WEIGHT_AGGREGATE_HEIGHT = -0.66569
    WEIGHT_COMPLETE_LINES = 0.96
    WEIGHT_HOLES = -0.46544
    WEIGHT_BUMPINESS = -0.24077
    WEIGHT_MAX_HEIGHT = -0.62
    WEIGHT_WELLS = -0.18
    WEIGHT_ROW_TRANSITIONS = -0.19
    WEIGHT_COLUMN_TRANSITIONS = -0.14
    WEIGHT_PIT_DEPTH = -0.22
    WEIGHT_COVERED_HOLES = -0.65
    WEIGHT_HOLE_DEPTH = -0.35

    # Bonus weights for special moves
    WEIGHT_TETRIS = 2.5
    WEIGHT_TSPIN_SINGLE = 0.8
    WEIGHT_TSPIN_DOUBLE = 1.6
    WEIGHT_TSPIN_TRIPLE = 2.4
    WEIGHT_COMBO = 0.35
    WEIGHT_PERFECT_CLEAR = 5.0

    # Strategic weights
    WEIGHT_WELL_POSITION = 0.15
    WEIGHT_FLATNESS = 0.12
    WEIGHT_I_PIECE_READINESS = 0.25

    # Strategic thresholds
    CRISIS_HEIGHT = 14
    DANGER_HEIGHT = 16
    TETRIS_WELL_MIN_DEPTH = 3
    LOOKAHEAD_DEPTH = 2
    LOOKAHEAD_TOP_N = 10

    def __init__(self, board, piece_randomizer):
        self.board = board
        self.piece_randomizer = piece_randomizer
        self.move_delay = 0.0
        self.moves_per_second = 8
        self.current_plan = []
        self.thinking = False

        # Caching to prevent redundant searches
        self.last_piece_id = None
        self.search_count = 0

        # Strategy state
        self.combo_count = 0
        self.last_clear_was_tetris = False
        self.preferred_well_column = 9

        # Debug tracking
        self.pieces_placed = 0
        self.last_debug_state = None
        self.frames_without_action = 0

        debug_print("[AI] Initialized")

    def debug_state(self):
        """Return current state for debugging"""
        piece_info = "None"
        if self.board.current_piece:
            p = self.board.current_piece
            piece_info = f"{p.piece_type.name} at ({p.x}, {p.y}) rot={p.rotation}"

        return {
            'piece': piece_info,
            'plan': self.current_plan.copy() if self.current_plan else [],
            'plan_len': len(self.current_plan),
            'thinking': self.thinking,
            'last_piece_id': self.last_piece_id,
            'current_piece_id': id(self.board.current_piece) if self.board.current_piece else None,
            'pieces_placed': self.pieces_placed,
            'line_clear_anim': self.board.line_clear_animation is not None,
        }

    def update(self, delta_time):
        """Update AI and execute moves"""
        # Track frames without action to detect halts
        had_action = False

        lock_info = self.board.update(delta_time)

        if self.board.line_clear_animation:
            animation_result = self.board.update_line_clear_animation(delta_time)
            if animation_result and animation_result['lines_cleared'] > 0:
                self.handle_piece_lock(animation_result)
                had_action = True
        elif lock_info['lines_cleared'] > 0:
            self.handle_piece_lock(lock_info)
            had_action = True

        if self.board.current_piece is None and not self.board.line_clear_animation:
            debug_print(f"[AI] Spawning new piece (pieces_placed={self.pieces_placed})")
            self.spawn_piece()
            had_action = True

        self.move_delay += delta_time

        if self.should_calculate_new_plan():
            self.thinking = True
            had_action = True

            piece_type = self.board.current_piece.piece_type.name if self.board.current_piece else "None"
            debug_print(f"[AI] Calculating plan for piece {piece_type}")

            best_move = self.find_best_move()
            if best_move:
                if self.board.current_piece:
                    self.last_piece_id = id(self.board.current_piece)
                self.current_plan = self.calculate_move_sequence(best_move)
                debug_print(f"[AI] Found move: rot={best_move['rotation']}, x={best_move['x']}, score={best_move.get('score', 'N/A'):.1f}")
                debug_print(f"[AI] Plan: {self.current_plan}")
            else:
                debug_print(f"[AI] WARNING: find_best_move returned None!")
                if self.board.current_piece:
                    debug_print(f"[AI] Trying fallback move...")
                    fallback = self.get_fallback_move()
                    if fallback:
                        self.last_piece_id = id(self.board.current_piece)
                        self.current_plan = self.calculate_move_sequence(fallback)
                        debug_print(f"[AI] Fallback move: rot={fallback['rotation']}, x={fallback['x']}")
                        debug_print(f"[AI] Fallback plan: {self.current_plan}")
                    else:
                        debug_print(f"[AI] CRITICAL: Fallback also failed!")
                        self.print_debug_info()

            self.search_count += 1
            self.thinking = False

        if self.current_plan and self.move_delay >= (1.0 / self.moves_per_second):
            action = self.current_plan.pop(0)
            debug_print(f"[AI] Executing: {action} (remaining: {self.current_plan})")
            self.execute_action(action)
            self.move_delay = 0.0
            had_action = True

        # Detect potential halts
        if had_action:
            self.frames_without_action = 0
        else:
            self.frames_without_action += 1

        # If no action for ~2 seconds (120 frames at 60fps), print debug info
        if self.frames_without_action == 120:
            debug_print(f"\n[AI] WARNING: No action for 120 frames!")
            self.print_debug_info()
        elif self.frames_without_action > 0 and self.frames_without_action % 300 == 0:
            debug_print(f"[AI] Still halted after {self.frames_without_action} frames")
            self.print_debug_info()

    def print_debug_info(self):
        """Print comprehensive debug information (only if AI_DEBUG enabled)"""
        if not AI_DEBUG:
            return
        print("=" * 50)
        print("[AI DEBUG INFO]")
        state = self.debug_state()
        for key, value in state.items():
            print(f"  {key}: {value}")

        print(f"  board.current_piece: {self.board.current_piece}")
        print(f"  board.line_clear_animation: {self.board.line_clear_animation}")

        if self.board.current_piece:
            p = self.board.current_piece
            print(f"  piece.state: {p.state}")
            print(f"  piece.piece_type: {p.piece_type}")

        # Check why should_calculate_new_plan might return False
        print(f"  --- should_calculate_new_plan checks ---")
        print(f"  thinking: {self.thinking}")
        print(f"  has current_piece: {self.board.current_piece is not None}")
        print(f"  has current_plan: {len(self.current_plan) > 0}")
        if self.board.current_piece:
            current_id = id(self.board.current_piece)
            print(f"  current_piece_id: {current_id}")
            print(f"  last_piece_id: {self.last_piece_id}")
            print(f"  ids match: {current_id == self.last_piece_id}")
        print("=" * 50)

    def should_calculate_new_plan(self):
        """Determine if we need to calculate a new plan"""
        if self.thinking:
            return False
        if not self.board.current_piece:
            return False
        if self.current_plan:
            return False
        current_piece_id = id(self.board.current_piece)
        if current_piece_id == self.last_piece_id:
            return False
        return True

    def spawn_piece(self):
        """Spawn a new piece for the AI"""
        piece = Piece(piece_bit_size=16)
        result = self.board.place_piece(piece)
        if not result:
            # Always print game over
            print("[AI] Game Over!")
            print(f"[AI] Total pieces placed: {self.pieces_placed}")
            print(f"[AI] Total searches performed: {self.search_count}")
        else:
            debug_print(f"[AI] Spawned {piece.piece_type.name} at ({piece.x}, {piece.y})")

    def handle_piece_lock(self, lock_info):
        """Handle piece locking and track combos"""
        lines = lock_info["lines_cleared"]
        self.pieces_placed += 1

        if lines > 0:
            self.combo_count += 1
            if lines == 4:
                self.last_clear_was_tetris = True
                # Always print TETRIS
                print(f"[AI] TETRIS! (Combo: {self.combo_count}, pieces: {self.pieces_placed})")
            else:
                self.last_clear_was_tetris = False
                if self.combo_count > 1:
                    debug_print(f"[AI] Cleared {lines} lines (Combo: {self.combo_count})")
        else:
            if self.combo_count > 2:
                debug_print(f"[AI] Combo ended at {self.combo_count}")
            self.combo_count = 0
            self.last_clear_was_tetris = False

    def get_fallback_move(self):
        """Get a simple fallback move when main search fails"""
        if not self.board.current_piece:
            debug_print("[AI] get_fallback_move: no current piece")
            return None

        piece = self.board.current_piece
        grid = self.board.grid
        valid_count = 0

        for rotation in range(4):
            for x in range(self.board.width):
                test_piece = self.create_test_piece(piece.piece_type, rotation, x)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if self.is_valid_placement(test_piece, grid):
                    valid_count += 1
                    debug_print(f"[AI] Fallback found valid: rot={rotation}, x={x}, y={y}")
                    return {
                        'rotation': rotation,
                        'x': x,
                        'y': y,
                        'score': 0
                    }

        debug_print(f"[AI] get_fallback_move: no valid placements found! (checked all rotations/positions)")
        return None

    def find_best_move(self):
        """Find the best move using lookahead search"""
        if not self.board.current_piece:
            debug_print("[AI] find_best_move: no current piece")
            return None

        current_piece = self.board.current_piece
        current_grid = self.board.grid
        heights = self.get_column_heights(current_grid)
        max_height = max(heights) if heights else 0
        in_crisis = max_height >= self.CRISIS_HEIGHT
        in_danger = max_height >= self.DANGER_HEIGHT

        if in_crisis:
            debug_print(f"[AI] In crisis mode (max_height={max_height})")
        if in_danger:
            debug_print(f"[AI] In danger mode (max_height={max_height})")

        best_move = self.evaluate_all_moves(
            current_piece.piece_type, current_grid, heights, in_crisis, in_danger
        )

        if best_move is None:
            debug_print(f"[AI] evaluate_all_moves returned None for {current_piece.piece_type.name}")

        return best_move

    def evaluate_all_moves(self, piece_type, grid, heights, in_crisis, in_danger):
        """Evaluate all possible moves for a given piece type"""
        best_score = float('-inf')
        best_move = None

        # Special handling for I-piece
        if piece_type == PieceType.I and not in_danger:
            wells = self.find_tetris_wells(grid, heights)
            if wells:
                well_move = self.evaluate_i_piece_for_wells(wells, grid, heights)
                if well_move and well_move['score'] > best_score:
                    best_score = well_move['score']
                    best_move = well_move

        # Evaluate all placements
        if in_crisis:
            move = self.find_best_single_move(piece_type, grid, heights, in_danger)
            if move and (best_move is None or move['score'] > best_score):
                return move
            return best_move
        else:
            move = self.search_with_lookahead(piece_type, grid, heights)
            if move and (best_move is None or move['score'] > best_score):
                return move
            return best_move

    def find_tetris_wells(self, grid, heights):
        """Find columns suitable for Tetris"""
        wells = []
        for col in range(len(heights)):
            left_height = heights[col - 1] if col > 0 else 20
            right_height = heights[col + 1] if col < len(heights) - 1 else 20

            if heights[col] + self.TETRIS_WELL_MIN_DEPTH <= min(left_height, right_height):
                well_depth = min(left_height, right_height) - heights[col]
                edge_bonus = 1 if (col == 0 or col == len(heights) - 1) else 0
                wells.append((col, int(well_depth), edge_bonus))

        wells.sort(key=lambda w: (w[1] + w[2] * 2), reverse=True)
        return wells

    def evaluate_i_piece_for_wells(self, wells, grid, heights):
        """Evaluate I-piece placement in wells"""
        best_score = float('-inf')
        best_move = None

        for col, depth, edge_bonus in wells:
            for rotation in [1, 3]:
                test_piece = self.create_test_piece(PieceType.I, rotation, col)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if not self.is_valid_placement(test_piece, grid):
                    continue

                lines_cleared = self.count_cleared_lines(test_piece, grid)

                if lines_cleared >= 1:
                    test_grid = self.simulate_placement(test_piece, grid)
                    base_score = self.evaluate_grid(test_grid)

                    if lines_cleared == 4:
                        base_score += self.WEIGHT_TETRIS * 100

                    base_score += edge_bonus * 10

                    if base_score > best_score:
                        best_score = base_score
                        best_move = {
                            'rotation': rotation,
                            'x': col,
                            'y': y,
                            'score': best_score
                        }

        return best_move

    def search_with_lookahead(self, piece_type, grid, heights):
        """Search with lookahead to find the best move"""
        next_pieces = self.piece_randomizer.next_pieces()

        if not next_pieces:
            debug_print("[AI] search_with_lookahead: no next_pieces, falling back to single move")
            return self.find_best_single_move(piece_type, grid, heights, False)

        next_piece_type = next_pieces[0]

        # Evaluate all first moves
        first_moves = []
        for rotation in range(4):
            for x in range(self.board.width):
                test_piece = self.create_test_piece(piece_type, rotation, x)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if not self.is_valid_placement(test_piece, grid):
                    continue

                grid_after = self.simulate_placement(test_piece, grid)
                immediate_score = self.evaluate_grid(grid_after)

                tspin_bonus = 0
                if piece_type == PieceType.T:
                    tspin_bonus = self.detect_tspin_bonus(test_piece, grid, grid_after)

                first_moves.append({
                    'rotation': rotation,
                    'x': x,
                    'y': y,
                    'grid': grid_after,
                    'immediate_score': immediate_score + tspin_bonus
                })

        if not first_moves:
            debug_print(f"[AI] search_with_lookahead: no valid first moves for {piece_type.name}!")
            return None

        # Prune to top N
        first_moves.sort(key=lambda m: m['immediate_score'], reverse=True)
        first_moves = first_moves[:self.LOOKAHEAD_TOP_N]

        best_score = float('-inf')
        best_move = None

        # Evaluate with lookahead
        for move in first_moves:
            best_next_score = None

            for next_rotation in range(4):
                for next_x in range(self.board.width):
                    next_piece = self.create_test_piece(next_piece_type, next_rotation, next_x)
                    if not next_piece:
                        continue

                    next_y = self.find_drop_position(next_piece, move['grid'])
                    next_piece.y = next_y

                    if not self.is_valid_placement(next_piece, move['grid']):
                        continue

                    grid_after_both = self.simulate_placement(next_piece, move['grid'])
                    score = self.evaluate_grid(grid_after_both)

                    if best_next_score is None or score > best_next_score:
                        best_next_score = score

            # If no valid next placement, use immediate score only
            if best_next_score is None:
                combined_score = move['immediate_score']
            else:
                combined_score = move['immediate_score'] * 0.4 + best_next_score * 0.6

            if combined_score > best_score:
                best_score = combined_score
                best_move = {
                    'rotation': move['rotation'],
                    'x': move['x'],
                    'y': move['y'],
                    'score': best_score
                }

        return best_move

    def find_best_single_move(self, piece_type, grid, heights, in_danger):
        """Find best move without lookahead"""
        best_score = float('-inf')
        best_move = None
        valid_count = 0

        for rotation in range(4):
            for x in range(self.board.width):
                test_piece = self.create_test_piece(piece_type, rotation, x)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if not self.is_valid_placement(test_piece, grid):
                    continue

                valid_count += 1
                test_grid = self.simulate_placement(test_piece, grid)
                score = self.evaluate_grid(test_grid)

                if in_danger:
                    lines = self.count_cleared_lines(test_piece, grid)
                    score += lines * 50

                if piece_type == PieceType.T:
                    score += self.detect_tspin_bonus(test_piece, grid, test_grid)

                new_heights = self.get_column_heights(test_grid)
                max_height = max(new_heights) if new_heights else 0

                if score > best_score:
                    best_score = score
                    best_move = {
                        'rotation': rotation,
                        'x': x,
                        'y': y,
                        'score': best_score,
                        '_max_height': max_height
                    }
                elif score == best_score and best_move is not None:
                    if max_height < best_move.get('_max_height', 999):
                        best_move = {
                            'rotation': rotation,
                            'x': x,
                            'y': y,
                            'score': best_score,
                            '_max_height': max_height
                        }

        if best_move is None:
            debug_print(f"[AI] find_best_single_move: no valid moves! valid_count={valid_count}")

        return best_move

    def detect_tspin_bonus(self, piece, grid, grid_after):
        """Detect if the placement is a T-spin and return bonus"""
        if piece.piece_type != PieceType.T:
            return 0

        center_x = piece.x + 1
        center_y = piece.y + 1

        corners = [
            (center_x - 1, center_y - 1),
            (center_x + 1, center_y - 1),
            (center_x - 1, center_y + 1),
            (center_x + 1, center_y + 1)
        ]

        filled_corners = 0
        for cx, cy in corners:
            if cx < 0 or cx >= self.board.width or cy >= self.board.height:
                filled_corners += 1
            elif cy >= 0 and grid[cx][cy] != 0:
                filled_corners += 1

        if filled_corners >= 3:
            lines_cleared = self.count_cleared_lines(piece, grid)
            if lines_cleared == 1:
                return self.WEIGHT_TSPIN_SINGLE * 50
            elif lines_cleared == 2:
                return self.WEIGHT_TSPIN_DOUBLE * 50
            elif lines_cleared == 3:
                return self.WEIGHT_TSPIN_TRIPLE * 50

        return 0

    def evaluate_grid(self, grid):
        """Enhanced evaluation function"""
        heights = self.get_column_heights(grid)
        aggregate_height = sum(heights)
        max_height = max(heights) if heights else 0
        bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))

        complete_lines = sum(
            1 for y in range(self.board.height)
            if all(grid[x][y] != 0 for x in range(self.board.width))
        )

        holes = 0
        covered_holes = 0
        hole_depth_sum = 0

        for x in range(self.board.width):
            found_block = False
            blocks_above = 0
            for y in range(self.board.height):
                if grid[x][y] != 0:
                    found_block = True
                    if y < self.board.height - 1:
                        blocks_above += 1
                elif found_block:
                    holes += 1
                    covered_holes += blocks_above
                    hole_depth_sum += self.board.height - y

        well_sum = 0
        for col in range(len(heights)):
            left_h = heights[col - 1] if col > 0 else 20
            right_h = heights[col + 1] if col < len(heights) - 1 else 20

            if heights[col] < left_h and heights[col] < right_h:
                well_depth = min(left_h, right_h) - heights[col]
                well_sum += well_depth * (well_depth + 1) // 2

                if col == 0 or col == len(heights) - 1:
                    well_sum -= well_depth

        row_transitions = 0
        for y in range(self.board.height):
            for x in range(self.board.width - 1):
                if (grid[x][y] == 0) != (grid[x + 1][y] == 0):
                    row_transitions += 1

        col_transitions = 0
        for x in range(self.board.width):
            for y in range(self.board.height - 1):
                if (grid[x][y] == 0) != (grid[x][y + 1] == 0):
                    col_transitions += 1

        pit_depth = 0
        for i, h in enumerate(heights):
            neighbors = []
            if i > 0:
                neighbors.append(heights[i - 1])
            if i < len(heights) - 1:
                neighbors.append(heights[i + 1])
            if neighbors:
                max_neighbor = max(neighbors)
                if h < max_neighbor:
                    pit_depth += max_neighbor - h

        flatness = len(heights) - len(set(heights))

        i_piece_ready = 0
        for col in range(len(heights)):
            left_h = heights[col - 1] if col > 0 else 20
            right_h = heights[col + 1] if col < len(heights) - 1 else 20
            if heights[col] + 4 <= min(left_h, right_h):
                i_piece_ready = 1
                break

        is_empty = all(grid[x][y] == 0 for x in range(self.board.width)
                      for y in range(self.board.height))
        perfect_clear_bonus = self.WEIGHT_PERFECT_CLEAR * 100 if is_empty else 0

        score = (
            self.WEIGHT_AGGREGATE_HEIGHT * aggregate_height +
            self.WEIGHT_COMPLETE_LINES * complete_lines * 100 +
            self.WEIGHT_HOLES * holes +
            self.WEIGHT_COVERED_HOLES * covered_holes +
            self.WEIGHT_HOLE_DEPTH * hole_depth_sum +
            self.WEIGHT_BUMPINESS * bumpiness +
            self.WEIGHT_MAX_HEIGHT * max_height +
            self.WEIGHT_WELLS * well_sum +
            self.WEIGHT_ROW_TRANSITIONS * row_transitions +
            self.WEIGHT_COLUMN_TRANSITIONS * col_transitions +
            self.WEIGHT_PIT_DEPTH * pit_depth +
            self.WEIGHT_FLATNESS * flatness * 10 +
            self.WEIGHT_I_PIECE_READINESS * i_piece_ready * 20 +
            self.WEIGHT_COMBO * self.combo_count * 10 +
            perfect_clear_bonus
        )

        return score

    def count_cleared_lines(self, piece, grid):
        """Count how many lines would be cleared by this placement"""
        test_grid = [col[:] for col in grid]

        for x, y, val in piece.iter_cells():
            if val:
                gx = piece.x + x
                gy = piece.y + y
                if 0 <= gx < self.board.width and 0 <= gy < self.board.height:
                    test_grid[gx][gy] = int(piece.piece_type)

        lines = 0
        for y in range(self.board.height):
            if all(test_grid[x][y] != 0 for x in range(self.board.width)):
                lines += 1

        return lines

    def simulate_placement(self, piece, grid):
        """Simulate placement with line clearing"""
        new_grid = [col[:] for col in grid]

        for x, y, val in piece.iter_cells():
            if val:
                gx = piece.x + x
                gy = piece.y + y
                if 0 <= gx < self.board.width and 0 <= gy < self.board.height:
                    new_grid[gx][gy] = int(piece.piece_type)

        lines_to_clear = []
        for y in range(self.board.height):
            if all(new_grid[x][y] != 0 for x in range(self.board.width)):
                lines_to_clear.append(y)

        for y in sorted(lines_to_clear, reverse=True):
            for x in range(self.board.width):
                del new_grid[x][y]
                new_grid[x].insert(0, 0)

        return new_grid

    def create_test_piece(self, piece_type, rotation, x):
        """Create a test piece for simulation"""
        test_piece = Piece(piece_type, piece_bit_size=16)
        test_piece.rotation = rotation
        test_piece.shape = PIECE_SHAPES[piece_type][rotation]
        test_piece.x = x
        test_piece.y = 0
        return test_piece

    def find_drop_position(self, piece, grid):
        """Find the y position where the piece would land"""
        y = 0
        while self.is_valid_position(piece, piece.x, y + 1, grid):
            y += 1
        return y

    def is_valid_position(self, piece, x, y, grid):
        """Check if a position is valid for the piece"""
        for cell_x, cell_y, value in piece.iter_cells():
            if value == 0:
                continue

            board_x = x + cell_x
            board_y = y + cell_y

            if board_x < 0 or board_x >= self.board.width:
                return False
            if board_y >= self.board.height:
                return False
            if board_y < 0:
                continue
            if grid[board_x][board_y] != 0:
                return False

        return True

    def is_valid_placement(self, piece, grid):
        """Check if the piece's current position is valid"""
        return self.is_valid_position(piece, piece.x, piece.y, grid)

    def get_column_heights(self, grid):
        """Get the height of each column"""
        heights = []
        for x in range(self.board.width):
            height = 0
            for y in range(self.board.height):
                if grid[x][y] != 0:
                    height = self.board.height - y
                    break
            heights.append(height)
        return heights

    def calculate_move_sequence(self, target_move):
        """Calculate the sequence of moves to reach the target position"""
        moves = []

        if not self.board.current_piece:
            debug_print("[AI] calculate_move_sequence: no current piece!")
            return moves

        current_rotation = self.board.current_piece.rotation
        target_rotation = target_move['rotation']
        rotations_needed = (target_rotation - current_rotation) % 4

        if rotations_needed == 3:
            moves.append('rotate_ccw')
        else:
            for _ in range(rotations_needed):
                moves.append('rotate_cw')

        current_x = self.board.current_piece.x
        target_x = target_move['x']

        if target_x < current_x:
            for _ in range(current_x - target_x):
                moves.append('move_left')
        elif target_x > current_x:
            for _ in range(target_x - current_x):
                moves.append('move_right')

        moves.append('hard_drop')
        return moves

    def execute_action(self, action):
        """Execute a single action"""
        if action == 'move_left':
            result = self.board.move_left()
            if not result:
                debug_print(f"[AI] WARNING: move_left failed!")
        elif action == 'move_right':
            result = self.board.move_right()
            if not result:
                debug_print(f"[AI] WARNING: move_right failed!")
        elif action == 'rotate_cw':
            result = self.board.rotate_cw()
            if not result:
                debug_print(f"[AI] WARNING: rotate_cw failed!")
        elif action == 'rotate_ccw':
            result = self.board.rotate_ccw()
            if not result:
                debug_print(f"[AI] WARNING: rotate_ccw failed!")
        elif action == 'hard_drop':
            if not self.board.current_piece:
                debug_print(f"[AI] WARNING: hard_drop called with no current piece!")
                return
            lock_info = self.board.hard_drop()
            self.handle_piece_lock(lock_info)
            self.current_plan = []
            # Clear last_piece_id so the next piece is recognized as new
            # (Python may reuse the same memory address for the new piece object)
            self.last_piece_id = None
