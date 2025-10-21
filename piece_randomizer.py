# piece_randomizer.py
import random
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
        self.bag = list(PieceType)
        random.shuffle(self.bag)

    def next_piece(self):
        if not self.bag:
            self._refill_bag()
        return self.bag.pop()
