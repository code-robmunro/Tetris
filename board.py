class Board:
    def __init__(self):
        self.width = 10
        self.height = 20
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def draw(self, screen):
        pass