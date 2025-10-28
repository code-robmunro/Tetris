import globals
import pygame

class SoundManager:
    def __init__(self):
        pygame.mixer.init()

        self.sounds = {
            "move": pygame.mixer.Sound(globals.MOVE_SOUND),
            "rotate": pygame.mixer.Sound(globals.ROTATE_SOUND),
            "line_clear": pygame.mixer.Sound(globals.LINE_CLEAR_SOUND),
        }

        self.sounds["move"].set_volume(0.5)
        self.sounds["rotate"].set_volume(0.5)
        self.sounds["line_clear"].set_volume(0.25)
        
        self.background_music = globals.TETRIS_SONG

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self, loop=True, volume=0.1, fade_ms=1000):
        pygame.mixer.music.load(self.background_music)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=-1 if loop else 0, fade_ms=fade_ms)

    def stop_music(self, fade_ms=500):
        pygame.mixer.music.fadeout(fade_ms)
