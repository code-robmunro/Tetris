import pygame
import globals

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(globals.FONT, 48)
        self.font_medium = pygame.font.Font(globals.FONT, 32)
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
        title_rect = title_text.get_rect(center=(globals.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Draw menu options
        start_y = 280
        spacing = 70
        
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
        
        # Draw instructions
        small_font = pygame.font.Font(globals.FONT, 16)
        instructions = small_font.render("Use Arrow Keys / WASD to navigate, Enter to select", True, (150, 150, 150))
        instructions_rect = instructions.get_rect(center=(globals.SCREEN_WIDTH // 2, 550))
        self.screen.blit(instructions, instructions_rect)
        
        pygame.display.flip()
