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
    tetris_bit_background = load_image(globals.TETRIS_BIT_16_SHEET, 2)
    tetris_bit_play = load_image(globals.TETRIS_BIT_24_SHEET)
    play_area_vertical_border = load_image(globals.PLAY_AREA_VERTICAL_BORDER)
    play_area_horizontal_border = load_image(globals.PLAY_AREA_HORIZONTAL_BORDER)