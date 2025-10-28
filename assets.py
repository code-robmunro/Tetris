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
    piece_bit = load_image(globals.TETRIS_BIT_24_SHEET)

    background = load_image(globals.BACKGROUND)

    # play_area_box = load_image(globals.PLAY_AREA_BOX)
    play_area_border = load_image(globals.PLAY_AREA_BORDER)

    # level_txt_box = load_image(globals.LEVEL_TXT_BOX)
    level_txt_border = load_image(globals.LEVEL_TXT_BORDER)

    # next_piece_box = load_image(globals.NEXT_PIECE_BOX)
    next_piece_border = load_image(globals.NEXT_PIECE_BORDER)

    # next_txt_box = load_image(globals.NEXT_TXT_BOX)
    next_txt_border = load_image(globals.NEXT_TXT_BORDER)

    # next_piece_secondary_box = load_image(globals.NEXT_PIECE_SECONDARY_BOX)
    next_piece_secondary_border = load_image(globals.NEXT_PIECE_SECONDARY_BORDER)

    # held_piece_box = load_image(globals.HELD_PIECE_BOX)
    held_piece_border = load_image(globals.HELD_PIECE_BORDER)

    # cpu_play_area_box = load_image(globals.CPU_PLAY_AREA_BOX)
    cpu_play_area_border = load_image(globals.CPU_PLAY_AREA_BORDER)

    cpu_avatar_box = load_image(globals.CPU_AVATAR_BOX)
    cpu_avatar_border = load_image(globals.CPU_AVATAR_BORDER)
    cpu_avatar_cat = load_image(globals.CPU_AVATAR_CAT)    

    # score_box = load_image(globals.SCORE_BOX)
    score_border = load_image(globals.SCORE_BORDER)
