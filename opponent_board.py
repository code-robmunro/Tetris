import pygame
import globals
import assets
from piece_data import PieceType, PIECE_SHAPES

class OpponentBoard:
    """Display-only board for showing opponent's game state from websocket data"""
    
    def __init__(self):
        # Use 16x16 blocks for opponent
        self.block_size = globals.TETRIS_BIT_16_WIDTH
        self.width = 10
        self.height = 20
        self.play_area_rect = globals.CPU_PLAY_AREA_BOX_RECT

        # Load 16x16 sprite sheet
        self.piece_bits = assets.load_piece_sprites(
            globals.TETRIS_BIT_16_SHEET,
            sprite_size=self.block_size
        )

        # Create surface for opponent play area (160x320 pixels)
        self.play_area = pygame.Surface(
            (self.width * self.block_size, self.height * self.block_size)
        )

        # Grid state (will be updated from websocket data)
        self.grid = [[0 for _ in range(self.height)] for _ in range(self.width)]

        # Current piece state (from websocket)
        self.current_piece_data = None  # {x, y, shape, piece_type}

        # Opponent stats
        self.opponent_score = 0
        self.opponent_level = 1
        self.opponent_lines = 0

        # Cache font for stats rendering
        self.stats_font = pygame.font.Font(None, 20)

        # Cache rendered text surfaces (update only when values change)
        self.cached_score_text = None
        self.cached_level_text = None
        self.cached_lines_text = None
        self.last_score = -1
        self.last_level = -1
        self.last_lines = -1

        # Don't initialize test pieces for multiplayer - will be populated from network
    
    def setup_test_pieces(self):
        """Add some test pieces to the grid for display testing"""
        # T-piece at bottom
        t_shape = PIECE_SHAPES[PieceType.T][0]  # rotation 0
        self.add_test_piece_to_grid(t_shape, PieceType.T, x=1, y=17)
        
        # I-piece horizontal
        i_shape = PIECE_SHAPES[PieceType.I][0]  # rotation 0
        self.add_test_piece_to_grid(i_shape, PieceType.I, x=5, y=18)
        
        # L-piece
        l_shape = PIECE_SHAPES[PieceType.L][0]  # rotation 0
        self.add_test_piece_to_grid(l_shape, PieceType.L, x=3, y=14)
        
        # S-piece
        s_shape = PIECE_SHAPES[PieceType.S][0]  # rotation 0
        self.add_test_piece_to_grid(s_shape, PieceType.S, x=6, y=15)
        
        # O-piece (square)
        o_shape = PIECE_SHAPES[PieceType.O][0]  # rotation 0
        self.add_test_piece_to_grid(o_shape, PieceType.O, x=0, y=12)
        
        # Add a falling piece (J-piece)
        j_shape = PIECE_SHAPES[PieceType.J][0]
        self.current_piece_data = {
            'x': 4,
            'y': 8,
            'shape': j_shape,
            'piece_type': int(PieceType.J)
        }
    
    def add_test_piece_to_grid(self, shape, piece_type, x, y):
        """Helper to add a piece shape to the grid at given position"""
        for row_idx, row in enumerate(shape):
            for col_idx, val in enumerate(row):
                if val:
                    grid_x = x + col_idx
                    grid_y = y + row_idx
                    # Check bounds
                    if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                        self.grid[grid_x][grid_y] = int(piece_type)
    
    def update_from_network(self, data):
        """Update board state from received websocket data"""
        # Only update grid if it's present AND not null (delta compression)
        if 'grid' in data and data['grid'] is not None:
            self.grid = data['grid']

        if 'current_piece' in data:
            self.current_piece_data = data['current_piece']
        else:
            self.current_piece_data = None

        # Store opponent stats for display
        self.opponent_score = data.get('score', 0)
        self.opponent_level = data.get('level', 1)
        self.opponent_lines = data.get('lines', 0)
    
    def draw(self, screen):
        """Draw the opponent's board and stats"""
        self.play_area.fill((0, 0, 0))

        # Draw locked blocks from grid
        for x, col in enumerate(self.grid):
            for y, val in enumerate(col):
                if val:
                    self.draw_bit(val, x, y)

        # Draw current piece if data exists
        if self.current_piece_data:
            self.draw_piece(self.current_piece_data)

        # Blit to screen at opponent position
        screen.blit(self.play_area, self.play_area_rect.topleft)

        # Draw opponent stats (below board) - only re-render if changed
        stats_y = self.play_area_rect.bottom + 10

        # Update cached text only if values changed
        if self.opponent_score != self.last_score:
            self.cached_score_text = self.stats_font.render(f"Score: {self.opponent_score}", True, (255, 255, 255))
            self.last_score = self.opponent_score

        if self.opponent_level != self.last_level:
            self.cached_level_text = self.stats_font.render(f"Level: {self.opponent_level}", True, (255, 255, 255))
            self.last_level = self.opponent_level

        if self.opponent_lines != self.last_lines:
            self.cached_lines_text = self.stats_font.render(f"Lines: {self.opponent_lines}", True, (255, 255, 255))
            self.last_lines = self.opponent_lines

        # Blit cached text surfaces
        if self.cached_score_text:
            screen.blit(self.cached_score_text, (self.play_area_rect.left, stats_y))
        if self.cached_level_text:
            screen.blit(self.cached_level_text, (self.play_area_rect.left, stats_y + 25))
        if self.cached_lines_text:
            screen.blit(self.cached_lines_text, (self.play_area_rect.left, stats_y + 50))
    
    def draw_bit(self, val, grid_x, grid_y):
        """Draw a single block"""
        surf = self.piece_bits[val - 1]
        self.play_area.blit(
            surf,
            (grid_x * self.block_size, grid_y * self.block_size)
        )
    
    def draw_piece(self, piece_data):
        """Draw the current falling piece from received data"""
        x = piece_data['x']
        y = piece_data['y']
        shape = piece_data['shape']
        piece_type = piece_data['piece_type']
        
        # Iterate through shape matrix (y-major as stored)
        for row_idx, row in enumerate(shape):
            for col_idx, val in enumerate(row):
                if val:
                    draw_x = x + col_idx
                    draw_y = y + row_idx
                    # Only draw if within bounds
                    if 0 <= draw_x < self.width and draw_y >= 0 and draw_y < self.height:
                        self.draw_bit(piece_type, draw_x, draw_y)
