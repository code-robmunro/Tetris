import random
import time
from piece_data import PieceType

class PieceRandomizer:
    def __init__(self, seed=None):
        if seed is None:
            seed = time.time()
        self.random = random.Random(seed)
        self.bag = []
        self._refill_bag()

    def set_seed(self, seed):
        """Initialize randomizer with specific seed for multiplayer sync"""
        self.random = random.Random(seed)
        # Clear and refill bag with seeded randomness
        self.bag.clear()
        self._refill_bag()

    def _refill_bag(self):
        new_pieces = list(PieceType)
        self.random.shuffle(new_pieces)
        self.bag[:0] = new_pieces
    
    def next_piece(self):
        if len(self.bag) <= 5:
            self._refill_bag()
        return self.bag.pop()
    
    def next_pieces(self):
        return self.bag[-5:][::-1]
