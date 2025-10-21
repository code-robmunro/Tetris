import random
from piece_data import PieceType

class PieceRandomizer:
    def __init__(self):
        self.bag = []
        self._refill_bag()

    def _refill_bag(self):
        self.bag = list(PieceType)
        random.shuffle(self.bag)

    def next_piece(self):
        if not self.bag:
            self._refill_bag()
        return self.bag.pop()