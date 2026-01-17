import copy

import globals

from piece import Piece

from piece_data import PieceType, PIECE_SHAPES

class AIOpponent:
    """Improved Tetris AI with better I-piece well detection"""

    # Tuned weights
    WEIGHT_AGGREGATE_HEIGHT = -0.510066
    WEIGHT_COMPLETE_LINES = 0.760666
    WEIGHT_HOLES = -0.35663
    WEIGHT_BUMPINESS = -0.184483
    WEIGHT_MAX_HEIGHT = -0.5
    WEIGHT_WELLS = -0.32
    WEIGHT_ROW_TRANSITIONS = -0.15
    WEIGHT_COLUMN_TRANSITIONS = -0.12
    WEIGHT_PIT_DEPTH = -0.28

    # Strategic thresholds
    CRISIS_HEIGHT = 14
    TETRIS_WELL_MIN_DEPTH = 4
    LOOKAHEAD_DEPTH = 2
    LOOKAHEAD_TOP_N = 8  # Prune to top N moves in lookahead

    def __init__(self, board, piece_randomizer):
        self.board = board
        self.piece_randomizer = piece_randomizer
        self.move_delay = 0.0
        self.moves_per_second = 5
        self.current_plan = []
        self.thinking = False

        # Caching to prevent redundant searches
        self.last_piece_id = None  # Track which piece we planned for
        self.search_count = 0  # Debug counter

    def update(self, delta_time):
        """Update AI and execute moves"""
        lock_info = self.board.update(delta_time)

        if self.board.line_clear_animation:
            animation_result = self.board.update_line_clear_animation(delta_time)
            if animation_result and animation_result['lines_cleared'] > 0:
                self.handle_piece_lock(animation_result)
        elif lock_info['lines_cleared'] > 0:
            self.handle_piece_lock(lock_info)

        if self.board.current_piece is None and not self.board.line_clear_animation:
            self.spawn_piece()

        self.move_delay += delta_time

        # Only search for new moves when we need them
        if self.should_calculate_new_plan():
            self.thinking = True

            # Mark this piece as planned
            if self.board.current_piece:
                self.last_piece_id = id(self.board.current_piece)

            best_move = self.find_best_move_with_lookahead()
            if best_move:
                self.current_plan = self.calculate_move_sequence(best_move)

            self.search_count += 1
            self.thinking = False

        # Execute moves from the plan
        if self.current_plan and self.move_delay >= (1.0 / self.moves_per_second):
            action = self.current_plan.pop(0)
            self.execute_action(action)
            self.move_delay = 0.0

    def should_calculate_new_plan(self):
        """Determine if we need to calculate a new plan"""
        # Don't calculate if already thinking
        if self.thinking:
            return False

        # Don't calculate if no piece active
        if not self.board.current_piece:
            return False

        # Don't calculate if we already have a plan
        if self.current_plan:
            return False

        # Don't recalculate for the same piece
        current_piece_id = id(self.board.current_piece)
        if current_piece_id == self.last_piece_id:
            return False

        # All checks passed - we need a new plan
        return True

    def spawn_piece(self):
        """Spawn a new piece for the AI"""
        piece = Piece(piece_bit_size=16)
        if not self.board.place_piece(piece):
            print("AI Game Over!")
            print(f"Total searches performed: {self.search_count}")

    def handle_piece_lock(self, lock_info):
        """Handle piece locking for AI"""
        if lock_info["lines_cleared"] == 4:
            print("🎉 AI TETRIS!")
        elif lock_info["lines_cleared"] > 0:
            print(f"AI cleared {lock_info['lines_cleared']} lines")

    def find_best_move_with_lookahead(self):
        """Find best move with advanced I-piece handling and deeper search"""
        if not self.board.current_piece:
            return None

        current_piece = self.board.current_piece
        current_grid = self.board.grid

        # Calculate heights once and reuse
        heights = self.get_column_heights(current_grid)
        max_height = max(heights) if heights else 0
        in_crisis = max_height >= self.CRISIS_HEIGHT

        # Enhanced I-piece strategy
        if current_piece.piece_type == PieceType.I:
            print(f"\n🔵 I-PIECE - Max height: {max_height}, Crisis: {in_crisis}")
            wells = self.find_tetris_wells_fast(current_grid, heights)
            print(f"Tetris-ready wells found: {wells}")

            if wells and in_crisis:
                best_well_move = self.evaluate_i_piece_wells(wells, current_piece, current_grid)
                if best_well_move:
                    return best_well_move
            elif wells:
                best_well_move = self.evaluate_i_piece_wells(wells, current_piece, current_grid, min_lines=3)
                if best_well_move:
                    return best_well_move

        # Standard lookahead search
        return self.search_with_lookahead(current_piece, current_grid, depth=self.LOOKAHEAD_DEPTH)

    def find_tetris_wells_fast(self, grid, heights=None):
        """Find columns suitable for Tetris (optimized)"""
        if heights is None:
            heights = self.get_column_heights(grid)

        wells = []
        for col in range(len(heights)):
            left_height = heights[col - 1] if col > 0 else float('inf')
            right_height = heights[col + 1] if col < len(heights) - 1 else float('inf')

            if heights[col] + self.TETRIS_WELL_MIN_DEPTH <= min(left_height, right_height):
                well_depth = min(left_height, right_height) - heights[col]
                wells.append((col, int(well_depth)))

        return wells

    def evaluate_i_piece_wells(self, wells, piece, grid, min_lines=1):
        """Evaluate I-piece placement in wells - FIXED to try all rotations"""
        best_score = float('-inf')
        best_move = None

        for col, depth in wells:
            # Try all 4 rotations, not just vertical (1, 3)
            for rotation in range(4):
                test_piece = self.create_test_piece(PieceType.I, rotation, col)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if not self.is_valid_placement(test_piece, grid):
                    continue

                lines_cleared = self.count_cleared_lines(test_piece, grid)

                if lines_cleared >= min_lines:
                    test_grid = self.simulate_placement(test_piece, grid)
                    score = self.evaluate_grid(test_grid)
                    score += lines_cleared * 25.0

                    if lines_cleared == 4:
                        score += 150.0

                    print(f"  Well at col {col}, rot {rotation}: {lines_cleared} lines, score: {score:.1f}")

                    if score > best_score:
                        best_score = score
                        best_move = {'rotation': rotation, 'x': col, 'y': y}

        return best_move

    def count_cleared_lines(self, piece, grid):
        """Count cleared lines - optimized to check only affected rows"""
        min_y, max_y = piece.y, piece.y
        for x, y, val in piece.iter_cells():
            if val:
                gy = piece.y + y
                min_y = min(min_y, gy)
                max_y = max(max_y, gy)

        test_grid = [col[:] for col in grid]
        for x, y, val in piece.iter_cells():
            if val:
                gx = piece.x + x
                gy = piece.y + y
                if 0 <= gx < self.board.width and 0 <= gy < self.board.height:
                    test_grid[gx][gy] = int(piece.piece_type)

        lines = 0
        for y in range(max(0, min_y), min(self.board.height, max_y + 1)):
            if all(test_grid[x][y] != 0 for x in range(self.board.width)):
                lines += 1

        return lines

    def search_with_lookahead(self, piece, grid, depth=2, top_n=None):
        """Enhanced lookahead search with pruning - FIXED with top-N optimization"""
        if top_n is None:
            top_n = self.LOOKAHEAD_TOP_N

        if depth == 0:
            return self.find_best_single_move(piece, grid)

        next_pieces = self.piece_randomizer.next_pieces()
        if not next_pieces:
            return self.find_best_single_move(piece, grid)

        next_piece_type = next_pieces[0]

        # Pre-compute and score all first moves
        first_moves = []
        for rotation in range(4):
            for x in range(self.board.width):
                test_piece = self.create_test_piece(piece.piece_type, rotation, x)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if not self.is_valid_placement(test_piece, grid):
                    continue

                grid_after_first = self.simulate_placement(test_piece, grid)
                immediate_score = self.evaluate_grid(grid_after_first)

                first_moves.append({
                    'rotation': rotation,
                    'x': x,
                    'y': y,
                    'grid': grid_after_first,
                    'immediate_score': immediate_score
                })

        # Sort by immediate score and only evaluate top N
        first_moves.sort(key=lambda m: m['immediate_score'], reverse=True)
        first_moves = first_moves[:top_n]

        best_score = float('-inf')
        best_first_move = None

        # Evaluate with lookahead only for top candidates
        for move in first_moves:
            best_next_score = float('-inf')

            for next_rotation in range(4):
                for next_x in range(self.board.width):
                    next_test_piece = self.create_test_piece(next_piece_type, next_rotation, next_x)
                    if not next_test_piece:
                        continue

                    next_y = self.find_drop_position(next_test_piece, move['grid'])
                    next_test_piece.y = next_y

                    if not self.is_valid_placement(next_test_piece, move['grid']):
                        continue

                    grid_after_both = self.simulate_placement(next_test_piece, move['grid'])
                    score = self.evaluate_grid(grid_after_both)

                    if score > best_next_score:
                        best_next_score = score

            if best_next_score > best_score:
                best_score = best_next_score
                best_first_move = {'rotation': move['rotation'], 'x': move['x'], 'y': move['y']}

        return best_first_move

    def find_best_single_move(self, piece, grid):
        """Fallback: evaluate just current piece - FIXED with tie-breaking"""
        best_score = float('-inf')
        best_move = None
        best_tie_breaker = None

        for rotation in range(4):
            for x in range(self.board.width):
                test_piece = self.create_test_piece(piece.piece_type, rotation, x)
                if not test_piece:
                    continue

                y = self.find_drop_position(test_piece, grid)
                test_piece.y = y

                if not self.is_valid_placement(test_piece, grid):
                    continue

                test_grid = self.simulate_placement(test_piece, grid)
                score = self.evaluate_grid(test_grid)

                # Tie-breaker: prefer lower height, then more central placement, then lower rotation
                heights = self.get_column_heights(test_grid)
                max_height = max(heights) if heights else 0
                center_distance = abs(x - self.board.width // 2)
                tie_breaker = (-max_height, -center_distance, -rotation)

                if score > best_score or (score == best_score and (best_tie_breaker is None or tie_breaker > best_tie_breaker)):
                    best_score = score
                    best_move = {'rotation': rotation, 'x': x, 'y': y}
                    best_tie_breaker = tie_breaker

        return best_move

    def simulate_placement(self, piece, grid):
        """Simulate placement with line clearing"""
        new_grid = [col[:] for col in grid]

        for x, y, val in piece.iter_cells():
            if val:
                gx = piece.x + x
                gy = piece.y + y
                if 0 <= gx < self.board.width and 0 <= gy < self.board.height:
                    new_grid[gx][gy] = int(piece.piece_type)

        new_grid = self.clear_lines_from_grid(new_grid)
        return new_grid

    def clear_lines_from_grid(self, grid):
        """Remove complete lines - optimized"""
        lines_to_clear = []
        for y in range(self.board.height):
            if all(grid[x][y] != 0 for x in range(self.board.width)):
                lines_to_clear.append(y)

        if not lines_to_clear:
            return grid

        for y in sorted(lines_to_clear, reverse=True):
            for x in range(self.board.width):
                del grid[x][y]
                grid[x].insert(0, 0)

        return grid

    def evaluate_grid(self, grid):
        """Enhanced evaluation - FIXED hole detection logic"""
        heights = self.get_column_heights(grid)
        aggregate_height = sum(heights)
        max_height = max(heights) if heights else 0
        bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))

        # Count complete lines
        complete_lines = 0
        for y in range(self.board.height):
            if all(grid[x][y] != 0 for x in range(self.board.width)):
                complete_lines += 1

        # FIXED: Correct hole detection
        holes = 0
        for x in range(self.board.width):
            found_block = False
            for y in range(self.board.height):
                if grid[x][y] != 0:
                    found_block = True
                elif found_block and grid[x][y] == 0:
                    holes += 1

        # Wells using cached heights
        wells = 0
        for col in range(len(heights)):
            left_height = heights[col - 1] if col > 0 else 0
            right_height = heights[col + 1] if col < len(heights) - 1 else 0

            if heights[col] < left_height and heights[col] < right_height:
                well_depth = min(left_height, right_height) - heights[col]
                if well_depth > 1:
                    wells += well_depth * well_depth

        # Row transitions
        row_transitions = 0
        for y in range(self.board.height):
            for x in range(self.board.width - 1):
                if (grid[x][y] == 0) != (grid[x + 1][y] == 0):
                    row_transitions += 1

        # Column transitions
        column_transitions = 0
        for x in range(self.board.width):
            for y in range(self.board.height - 1):
                if (grid[x][y] == 0) != (grid[x][y + 1] == 0):
                    column_transitions += 1

        # Pit depth using cached heights
        pit_depth = 0
        for i in range(len(heights)):
            neighbors = []
            if i > 0:
                neighbors.append(heights[i - 1])
            if i < len(heights) - 1:
                neighbors.append(heights[i + 1])

            if neighbors:
                max_neighbor = max(neighbors)
                if heights[i] < max_neighbor:
                    pit_depth += max_neighbor - heights[i]

        score = (
            self.WEIGHT_AGGREGATE_HEIGHT * aggregate_height +
            self.WEIGHT_COMPLETE_LINES * complete_lines +
            self.WEIGHT_HOLES * holes +
            self.WEIGHT_BUMPINESS * bumpiness +
            self.WEIGHT_MAX_HEIGHT * max_height +
            self.WEIGHT_WELLS * wells +
            self.WEIGHT_ROW_TRANSITIONS * row_transitions +
            self.WEIGHT_COLUMN_TRANSITIONS * column_transitions +
            self.WEIGHT_PIT_DEPTH * pit_depth
        )

        return score

    def create_test_piece(self, piece_type, rotation, x):
        test_piece = Piece(piece_type, piece_bit_size=16)
        test_piece.rotation = rotation
        test_piece.shape = PIECE_SHAPES[piece_type][rotation]
        test_piece.x = x
        test_piece.y = 0
        return test_piece

    def find_drop_position(self, piece, grid):
        y = 0
        while self.is_valid_position(piece, piece.x, y + 1, grid):
            y += 1
        return y

    def is_valid_position(self, piece, x, y, grid):
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
        return self.is_valid_position(piece, piece.x, piece.y, grid)

    def get_column_heights(self, grid):
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
        moves = []

        current_rotation = self.board.current_piece.rotation
        target_rotation = target_move['rotation']
        rotations_needed = (target_rotation - current_rotation) % 4

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
        if action == 'move_left':
            self.board.move_left()
        elif action == 'move_right':
            self.board.move_right()
        elif action == 'rotate_cw':
            self.board.rotate_cw()
        elif action == 'hard_drop':
            lock_info = self.board.hard_drop()
            self.handle_piece_lock(lock_info)
            self.current_plan = []
