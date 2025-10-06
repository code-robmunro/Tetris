import pygame

def load_sprite(path, scale=None):
    sprite = pygame.image.load(path).convert_alpha()
    if scale is not None:
        sprite = pygame.transform.scale(sprite, (sprite.get_width * scale, sprite.get_height * scale))
    return sprite

def get_sprite(sheet, x, y, width, height):
    """Return a single sprite from a sprite sheet."""
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)
    sprite = pygame.transform.scale(sprite, (32, 32))
    sprite.blit(sheet, (0, 0), pygame.Rect(x, y, width, height))
    return sprite