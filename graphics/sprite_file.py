from graphics.sprite import Sprite
from graphics.sprite_tile import SpriteTile

class SpriteFile(Sprite):
    def __init__(self, path, palette):
        self.path = path
        super().__init__([], palette)

        with open(path, "rb") as input_file:
            data = list(input_file.read())

        if not data or len(data) % SpriteTile.DATA_SIZE != 0:
            raise ValueError(f"SpriteFile: '{path}' size {len(data)} is not a positive multiple of {SpriteTile.DATA_SIZE} (8x8 tiles)")

        self.data = data
