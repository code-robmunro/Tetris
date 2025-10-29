import pygame
import sys
import asyncio
import globals
from ui import UI
from soundmanager import SoundManager
from board import Board
from piece import Piece

class Game:
    GRAVITY_TIMER_GROWTH_FACTOR = 1.1
    ENTRY_DELAY = 0.5 # Before next piece enters
    DELAYED_AUTO_SHIFT = 0.17 # Before holding L/R results in repeated movement
    SOFT_DROP_MULTIPLIER = 20

    def __init__(self, screen):
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.running = True
        self.delta_time = self.clock.get_time() / 1000
        self.paused = False
        self.font = pygame.font.SysFont(None, 36)  # None = default font, 36 = size

        self.ui = UI()
        self.on_level_change_callback = self.ui.handle_level_change
        self.on_lines_change_callback = self.ui.handle_lines_change
        self.on_score_change_callback = self.ui.handle_score_change

        self.sound = SoundManager()
        self.sound.play_music()
        self.board = Board()

        self.state = "PLAYING"
        self.level = 5
        self.lines_cleared = 0
        self.score = 0
        self.spawn_piece()

        self.last_lock_info = {
            "lines_cleared": 0,
            "board_full": False,
        }

        self.gravity_time = 0
        self.seconds_per_row = globals.LEVEL_SPEEDS[min(self.level - 1, len(globals.LEVEL_SPEEDS) - 1)]
        self.lock_delay = 0.5 # Grounded slide / wall kick - Level 1
        self.soft_drop_timer = 0
        self.soft_drop_active = False 

    async def run(self):
        while self.running:
            self.handle_input()

            if not self.paused:
                self.update()
            self.draw()  # always draw so you can see the paused frame

            # Optional: draw pause text
            if self.paused:
                pause_text = self.font.render("PAUSED", True, (255, 255, 0))
                self.screen.blit(pause_text, (100, 100))
                
            pygame.display.flip()

            self.clock.tick(60)
            await asyncio.sleep(0)  # keep async flow for pygbag/browser

        pygame.quit()
        sys.exit()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                    self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.move_left()
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.move_right()
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.soft_drop_active = True
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif event.key == pygame.K_w or event.key == pygame.K_e or event.key == pygame.K_UP:
                    self.rotate_cw()
                elif event.key == pygame.K_q or event.key == pygame.K_z:
                    self.rotate_ccw()
                elif event.key == pygame.K_LSHIFT:
                    self.hold_piece()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"Paused: {self.paused}")
                elif event.key == pygame.K_b:
                    breakpoint()

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    self.soft_drop_active = False  # stop soft drop

    def update(self):
        self.delta_time = self.clock.tick(60) / 1000

        # Update gravity
        if self.soft_drop_active:
            self.gravity_time += self.delta_time * self.SOFT_DROP_MULTIPLIER
        else:
            self.gravity_time += self.delta_time

        # Move piece down based on gravity
        while self.gravity_time >= self.seconds_per_row:
            self.move_down(from_input=self.soft_drop_active)  # gravity movement, no sound
            self.gravity_time -= self.seconds_per_row

        lock_info = self.board.update(self.delta_time)
        if lock_info["lines_cleared"] > 0:
            self.handle_piece_lock(lock_info)

        self.ui.update()

        # Spawn a new piece if needed
        if self.board.current_piece is None:
            self.spawn_piece()

    def draw(self):
        self.ui.draw(self.screen)
        self.board.draw(self.screen)

    def spawn_piece(self):
        piece = Piece()

        if not self.board.place_piece(piece):
            self.state = "GAME_OVER"
            return

    def handle_piece_lock(self, lock_info):
        if lock_info["lines_cleared"] > 0:
            self.sound.play("line_clear")
            self.lines_cleared += lock_info["lines_cleared"]
            self.on_lines_change()
            self.calculate_level()
            self.score += self.calculate_score_score(lock_info["lines_cleared"])
        
        if lock_info["board_full"]:
            self.state = "GAME_OVER"
        else:
            self.spawn_piece()

    def total_lines_for_level(self, level):
        # Returns cumulative total lines needed to reach the given level
        # Level 1 → 2 requires 20 lines
        return 10 * (level * (level + 1) // 2) - 10

    def calculate_level(self):
        while self.lines_cleared >= self.total_lines_for_level(self.level + 1):
            self.level += 1
            self.on_level_change()
            self.seconds_per_row = globals.LEVEL_SPEEDS[min(self.level - 1, len(globals.LEVEL_SPEEDS) - 1)]

    def calculate_score_score(self, lines_cleared):
        return 0

    # -----------------------------
    # Input event handlers
    # -----------------------------
    def move_down(self, from_input=False):
        moved = self.board.move_down()
        
        if from_input and moved:
            self.sound.play("move")

        if self.soft_drop_active == True:
            self.gravity_time = 0        

    def move_left(self):
        if self.board.move_left():
            self.sound.play("move")

    def move_right(self):
        if self.board.move_right():
            self.sound.play("move")

    def hard_drop(self):
        lock_info = self.board.hard_drop()
        self.handle_piece_lock(lock_info)  

    def rotate_cw(self):
        if self.board.rotate_cw():
            self.sound.play("rotate")

    def rotate_ccw(self):
        if self.board.rotate_ccw():
            self.sound.play("rotate")

    def hold_piece(self):
        pass

    # -----------------------------
    # Callbacks
    # -----------------------------
    def on_level_change(self):
        if self.on_level_change_callback:
            self.on_level_change_callback(self.level)
            print(f"Leveled - {self.level - 1} to {self.level} with {self.lines_cleared}")

    def on_lines_change(self):
        if self.on_lines_change_callback:
            self.on_lines_change_callback(self.lines_cleared)

    def on_score_change(self):
        if self.on_score_change_callback:
            self.on_score_change_callback(self.score)