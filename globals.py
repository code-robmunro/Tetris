import pygame

# screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

TETRIS_BIT_24_SHEET = "assets/graphics/tetris_bit_24.png"
TETRIS_BIT_24_WIDTH = 24
TETRIS_BIT_24_HEIGHT = 24
TETRIS_BIT_24_SHEET_LENGTH = 11

BACKGROUND = "assets/graphics/background.png"

# PLAY_AREA_BOX = "assets/graphics/play_area_box.png"
PLAY_AREA_BOX_RECT = pygame.Rect(280, 66, 240, 480)
PLAY_AREA_BORDER = "assets/graphics/play_area_border.png"
PLAY_AREA_BORDER_RECT = pygame.Rect(274, 60, 252, 492)

# LEVEL_TXT_BOX = "assets/graphics/level_txt_box.png"
LEVEL_TXT_BOX_RECT = pygame.Rect(289, 19, 221, 36)
LEVEL_TXT_BORDER = "assets/graphics/level_txt_border.png"
LEVEL_TXT_BORDER_RECT = pygame.Rect(285, 15, 229, 44)

# NEXT_PIECE_BOX = "assets/graphics/next_piece_box.png"
NEXT_PIECE_BOX_RECT = pygame.Rect(547, 91, 80, 64)
NEXT_PIECE_BORDER = "assets/graphics/next_piece_border.png"
NEXT_PIECE_BORDER_RECT = pygame.Rect(543, 87, 88, 72)

# NEXT_TXT_BOX = "assets/graphics/next_txt_box.png"
NEXT_TXT_BOX_RECT = pygame.Rect(550, 65, 74, 20)
NEXT_TXT_BORDER = "assets/graphics/next_txt_border.png" 
NEXT_TXT_BORDER_RECT = pygame.Rect(546, 61, 82, 28)

# NEXT_PIECE_SECONDARY_BOX = "assets/graphics/next_piece_seconary_box.png"
NEXT_PIECE_SECONDARY_BOX_RECT = pygame.Rect(550, 158, 74, 226)
NEXT_PIECE_SECONDARY_BORDER = "assets/graphics/next_piece_secondary_border.png"
NEXT_PIECE_SECONDARY_BORDER_RECT = pygame.Rect(547, 155, 80, 232)

# HELD_PIECE_BOX = "assets/graphics/held_piece_box.png"
HELD_PIECE_BOX_RECT = pygame.Rect(653, 91, 80, 64)
HELD_PIECE_BORDER = "assets/graphics/held_piece_border.png"
HELD_PIECE_BORDER_RECT = pygame.Rect(650, 87, 88, 72)

# HELD_TXT_BOX = "assets/graphics/next_txt_box.png"
HELD_TXT_BOX_RECT = pygame.Rect(656, 65, 74, 20)
HELD_TXT_BORDER = "assets/graphics/held_txt_border.png"
HELD_TXT_BORDER_RECT = pygame.Rect(652, 61, 82, 28)

# CPU_PLAY_AREA_BOX = "assets/graphics/cpu_play_area_box.png"
CPU_PLAY_AREA_BOX_RECT = pygame.Rect(57, 146, 160, 320)
CPU_PLAY_AREA_BORDER = "assets/graphics/cpu_play_area_border.png"
CPU_PLAY_AREA_BORDER_RECT = pygame.Rect(51, 140, 172, 332)

CPU_AVATAR_BOX = "assets/graphics/cpu_avatar_box.png"
CPU_AVATAR_BOX_RECT = pygame.Rect(82, 66, 109, 85)

CPU_AVATAR_BORDER = "assets/graphics/cpu_avatar_border.png"
CPU_AVATAR_BORDER_RECT = pygame.Rect(78, 62, 117, 93)

CPU_AVATAR_CAT = "assets/graphics/cpu_avatar_cat.png"
CPU_AVATAR_CAT_RECT = pygame.Rect(105, 73, 62, 71)

# SCORE_BOX = "assets/graphics/score_box.png"
SCORE_BOX_RECT = pygame.Rect(550, 430, 187, 116)
SCORE_BORDER = "assets/graphics/score_border.png"
SCORE_BORDER_RECT = pygame.Rect(546, 426, 195, 124)

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

TETRIS_SONG = "assets/sound/tetris.ogg"
MOVE_SOUND = "assets/sound/move.ogg"
ROTATE_SOUND = "assets/sound/rotate.ogg"
LINE_CLEAR_SOUND = "assets/sound/line_clear.ogg"