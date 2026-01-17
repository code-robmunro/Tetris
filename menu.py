import pygame
import globals

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(globals.FONT, 48)
        self.font_medium = pygame.font.Font(globals.FONT, 32)
        self.font_small = pygame.font.Font(globals.FONT, 18)
        self.font_tiny = pygame.font.Font(globals.FONT, 14)
        self.selected_index = 0
        self.options = ["Single Player", "Vs. AI", "Multiplayer", "Exit"]
        self.running = True

    def handle_input(self):
        """Handle menu navigation input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "EXIT"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.options[self.selected_index].upper().replace(" ", "_")
                elif event.key == pygame.K_ESCAPE:
                    return "EXIT"
        return None

    def draw(self):
        """Draw the menu"""
        # Fill background with black
        self.screen.fill((0, 0, 0))

        # Draw title
        title_text = self.font_large.render("TETRIS", True, (100, 200, 255))
        title_rect = title_text.get_rect(center=(globals.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)

        # Draw menu options
        start_y = 200
        spacing = 60

        for i, option in enumerate(self.options):
            # Highlight selected option
            if i == self.selected_index:
                color = (255, 255, 0)  # Yellow for selected
                prefix = "> "
            else:
                color = (255, 255, 255)  # White for unselected
                prefix = "  "

            text = self.font_medium.render(f"{prefix}{option}", True, color)
            text_rect = text.get_rect(center=(globals.SCREEN_WIDTH // 2, start_y + i * spacing))
            self.screen.blit(text, text_rect)

        # Draw navigation instructions
        nav_y = 430
        nav_text = self.font_small.render("↑↓ / W S - Navigate    Enter / Space - Select    ESC - Exit", True, (150, 150, 150))
        nav_rect = nav_text.get_rect(center=(globals.SCREEN_WIDTH // 2, nav_y))
        self.screen.blit(nav_text, nav_rect)

        # Draw gameplay controls header
        controls_header = self.font_small.render("GAMEPLAY CONTROLS:", True, (100, 200, 255))
        controls_header_rect = controls_header.get_rect(center=(globals.SCREEN_WIDTH // 2, nav_y + 35))
        self.screen.blit(controls_header, controls_header_rect)

        # Draw gameplay controls in two columns
        controls_left = [
            "← → / A D - Move",
            "↑ / W E - Rotate CW",
            "Q Z - Rotate CCW"
        ]
        
        controls_right = [
            "↓ / S - Soft Drop",
            "Space - Hard Drop",
            "Shift - Hold Piece"
        ]

        left_x = globals.SCREEN_WIDTH // 2 - 150
        right_x = globals.SCREEN_WIDTH // 2 + 150
        controls_start_y = nav_y + 60

        for i, control in enumerate(controls_left):
            text = self.font_tiny.render(control, True, (200, 200, 200))
            text_rect = text.get_rect(center=(left_x, controls_start_y + i * 20))
            self.screen.blit(text, text_rect)

        for i, control in enumerate(controls_right):
            text = self.font_tiny.render(control, True, (200, 200, 200))
            text_rect = text.get_rect(center=(right_x, controls_start_y + i * 20))
            self.screen.blit(text, text_rect)

        pygame.display.flip()
