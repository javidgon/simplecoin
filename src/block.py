import hashlib as hasher
from typing import Dict


class Block:
    def __init__(self, index: int, timestamp: float, data: Dict, previous_block = None) -> None:
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_block = previous_block


    @property
    def previous_hash(self):
        return self.previous_block.get_hash() if self.previous_block else '0' * 64


    def get_hash(self) -> str:
        sha = hasher.sha256()
        sha.update(
            (
                str(self.index) +
                str(self.timestamp) +
                str(self.data) +
                str(self.previous_hash)
            ).encode()
        )
        return sha.hexdigest()
