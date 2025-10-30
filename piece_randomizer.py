# piece_randomizer.py
import random, time
random.seed(time.time())
from piece_data import PieceType

class PieceRandomizer:
    _instance = None  # static variable for singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.bag = []
        self._refill_bag()

    def _refill_bag(self):
        new_pieces = list(PieceType)
        random.shuffle(new_pieces)
        self.bag[:0] = new_pieces

    def next_piece(self):
        if len(self.bag) <= 5:
            self._refill_bag()
        return self.bag.pop()
        
    def next_pieces(self):
        return self.bag[-5:][::-1]
