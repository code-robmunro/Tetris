import random

class Piece:
    def __init__(self, shape):
        self.shape = shape
    
    @staticmethod
    def random():
        # Simple placeholder - returns a basic piece
        return Piece([[1, 1], [1, 1]])

