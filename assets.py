import pygame
import globals

# Global cache dictionary
_assets = {}

def load_image(path, scale=None):
    if path not in _assets:
        _assets[path] = pygame.image.load(path).convert_alpha()
        if scale is not None:
            _assets[path] = pygame.transform.scale(_assets[path], (_assets[path].get_width() * scale, _assets[path].get_height() * scale))
    
    return _assets[path]

def preload():    
    # preload commonly used graphics
    cat_sprite = load_image("assets/cat.png", 0.5)
    tetris_bit = load_image(globals.TETRIS_BIT_SHEET)