import pygame

def get_sprite(sheet, x, y, width, height):
    """Return a single sprite from a sprite sheet."""
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)
    sprite = pygame.transform.scale(sprite, (32, 32))
    sprite.blit(sheet, (0, 0), pygame.Rect(x, y, width, height))
    return sprite