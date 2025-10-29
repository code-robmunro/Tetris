import pygame

def get_sprite(sheet, x, y, width, height):
    """Return a single sprite from a sprite sheet."""
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)
    sprite.blit(sheet, (0, 0), pygame.Rect(x, y, width, height))
    return sprite