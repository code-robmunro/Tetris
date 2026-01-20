import pygame
import assets
import globals
from piece import Piece
from piece_data import PieceType


class UI:
    def __init__(self, event_bus, piece_randomizer):
        self.event_bus = event_bus
        self.randomizer = piece_randomizer
        self.event_bus.on("level_change", self.handle_level_change)
        self.event_bus.on("lines_change", self.handle_lines_change)
        self.event_bus.on("score_change", self.handle_score_change)
        self.event_bus.on("piece_held_or_swapped", self.handle_piece_held_or_swapped)

        self.ui = pygame.Surface((globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT))
        self.font_20 = pygame.font.Font(globals.FONT, 20)
        self.font_16 = pygame.font.Font(globals.FONT, 16)

        self.current_level = 5  # 1
        self.current_lines = 140  # 0
        self.current_score = 0
        self.top_score = 0
        self.next_pieces = []
        self.held_piece = None

        # Cache static background layout (only rendered once)
        self.static_layout = None
        self.paint_static_layout()

        # Track dirty flags for dynamic elements and cache text surfaces
        self.level_dirty = True
        self.lines_dirty = True
        self.score_dirty = True
        self.cached_level_text = None
        self.cached_lines_text = None
        self.cached_score_text = None

    def update(self):
        self.next_pieces = self.randomizer.next_pieces()

    def draw(self, screen):
        # Start with cached static layout
        self.ui.blit(self.static_layout, (0, 0))

        # Update only dynamic parts
        self.update_dynamic_text()
        self.draw_next_pieces()
        self.draw_held_piece()

        screen.blit(self.ui, (0, 0))

    def paint_static_layout(self):
        """Render static UI elements once and cache them"""
        self.static_layout = pygame.Surface((globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT))

        background = assets.load_image(globals.BACKGROUND)
        self.static_layout.blit(background, (0, 0))

        play_area_border = assets.load_image(globals.PLAY_AREA_BORDER)
        self.static_layout.blit(play_area_border, globals.PLAY_AREA_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.PLAY_AREA_BOX_RECT)

        level_txt_border = assets.load_image(globals.LEVEL_TXT_BORDER)
        self.static_layout.blit(level_txt_border, globals.LEVEL_TXT_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.LEVEL_TXT_BOX_RECT)

        # Paint secondary first, so it is underneath primary
        next_piece_secondary_border = assets.load_image(globals.NEXT_PIECE_SECONDARY_BORDER)
        self.static_layout.blit(next_piece_secondary_border, globals.NEXT_PIECE_SECONDARY_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.NEXT_PIECE_SECONDARY_BOX_RECT)

        next_piece_border = assets.load_image(globals.NEXT_PIECE_BORDER)
        self.static_layout.blit(next_piece_border, globals.NEXT_PIECE_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.NEXT_PIECE_BOX_RECT)

        next_txt_border = assets.load_image(globals.NEXT_TXT_BORDER)
        self.static_layout.blit(next_txt_border, globals.NEXT_TXT_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.NEXT_TXT_BOX_RECT)
        next_txt = self.font_16.render(globals.NEXT_TXT, True, (255, 255, 255))
        self.static_layout.blit(next_txt, (567, 64))

        held_piece_border = assets.load_image(globals.HELD_PIECE_BORDER)
        self.static_layout.blit(held_piece_border, globals.HELD_PIECE_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.HELD_PIECE_BOX_RECT)

        held_txt_border = assets.load_image(globals.HELD_TXT_BORDER)
        self.static_layout.blit(held_txt_border, globals.HELD_TXT_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.HELD_TXT_BOX_RECT)
        held_txt = self.font_16.render(globals.HELD_TXT, True, (255, 255, 255))
        self.static_layout.blit(held_txt, (672, 64))

        cpu_play_area_border = assets.load_image(globals.CPU_PLAY_AREA_BORDER)
        self.static_layout.blit(cpu_play_area_border, globals.CPU_PLAY_AREA_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.CPU_PLAY_AREA_BOX_RECT)

        cpu_avatar_border = assets.load_image(globals.CPU_AVATAR_BORDER)
        self.static_layout.blit(cpu_avatar_border, globals.CPU_AVATAR_BORDER_RECT.topleft)

        cpu_avatar_box = assets.load_image(globals.CPU_AVATAR_BOX)
        self.static_layout.blit(cpu_avatar_box, globals.CPU_AVATAR_BOX_RECT.topleft)

        cpu_avatar = assets.load_image(globals.CPU_AVATAR_CAT)
        self.static_layout.blit(cpu_avatar, globals.CPU_AVATAR_CAT_RECT.topleft)

        score_border = assets.load_image(globals.SCORE_BORDER)
        self.static_layout.blit(score_border, globals.SCORE_BORDER_RECT.topleft)
        self.static_layout.fill((0, 0, 0), globals.SCORE_BOX_RECT)

    def update_dynamic_text(self):
        """Update only the text that changes (level, lines, score)"""
        # Re-render text surfaces only when values change
        if self.level_dirty:
            self.cached_level_text = self.font_20.render((globals.LEVEL_TXT + str(self.current_level)), True, (255, 255, 255))
            self.level_dirty = False

        if self.lines_dirty:
            self.cached_lines_text = self.font_20.render((globals.LINES_TXT + str(self.current_lines)), True, (255, 255, 255))
            self.lines_dirty = False

        if self.score_dirty:
            self.cached_score_text = self.font_20.render((globals.SCORE_TXT + str(self.current_score)), True, (255, 255, 255))
            self.score_dirty = False

        # Always blit the cached text surfaces every frame
        if hasattr(self, 'cached_level_text') and self.cached_level_text:
            self.ui.blit(self.cached_level_text, (365, 25))

        if hasattr(self, 'cached_lines_text') and self.cached_lines_text:
            self.ui.blit(self.cached_lines_text, (560, 436))

        if hasattr(self, 'cached_score_text') and self.cached_score_text:
            self.ui.blit(self.cached_score_text, (560, 471))

        # Top score (always render)
        top_score_txt = self.font_20.render((globals.TOP_SCORE_TXT + str(self.top_score)), True, (255, 255, 255))
        self.ui.blit(top_score_txt, (560, 507))

    def draw_next_pieces(self):
        for i, piece_type in enumerate(self.next_pieces):
            piece = Piece(piece_type, piece_bit_size=16, randomizer=self.randomizer)

            if piece.piece_type in (PieceType.S, PieceType.T, PieceType.J, PieceType.L, PieceType.Z):
                x = globals.NEXT_PIECE_BOX_RECT.centerx - 24
                y = globals.NEXT_PIECE_BOX_RECT.centery - 16
            elif piece.piece_type == PieceType.O:
                x = globals.NEXT_PIECE_BOX_RECT.centerx - 32
                y = globals.NEXT_PIECE_BOX_RECT.centery - 32
            else:  # the PieceType is 'I'
                x = globals.NEXT_PIECE_BOX_RECT.centerx - 32
                y = globals.NEXT_PIECE_BOX_RECT.centery - 24

            if i > 0:
                y = y + 22 + (50 * i)

            piece.draw(self.ui, x_offset=x, y_offset=y, use_grid=False)

    def draw_held_piece(self):
        if self.held_piece:
            piece = Piece(self.held_piece.piece_type, piece_bit_size=16, randomizer=self.randomizer)

            if piece.piece_type in (PieceType.S, PieceType.T, PieceType.J, PieceType.L, PieceType.Z):
                x = globals.HELD_PIECE_BOX_RECT.centerx - 24
                y = globals.HELD_PIECE_BOX_RECT.centery - 16
            elif piece.piece_type == PieceType.O:
                x = globals.HELD_PIECE_BOX_RECT.centerx - 32
                y = globals.HELD_PIECE_BOX_RECT.centery - 32
            else:  # the PieceType is 'I'
                x = globals.HELD_PIECE_BOX_RECT.centerx - 32
                y = globals.HELD_PIECE_BOX_RECT.centery - 24

            piece.draw(self.ui, x_offset=x, y_offset=y, use_grid=False)

    def handle_level_change(self, level):
        self.current_level = level
        self.level_dirty = True

    def handle_lines_change(self, lines):
        self.current_lines = lines
        self.lines_dirty = True

    def handle_score_change(self, score):
        self.current_score = score
        self.score_dirty = True

    def handle_piece_held_or_swapped(self, piece: Piece):
        self.held_piece = piece
