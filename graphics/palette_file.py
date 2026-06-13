from graphics.palette import Palette
from graphics.bgr15 import BGR15

class PaletteFile(Palette):
    def __init__(self, path):
        self.path = path
        super().__init__()

        with open(path, "rb") as input_file:
            data = list(input_file.read())

        if not data or len(data) % BGR15.DATA_SIZE != 0:
            raise ValueError(f"PaletteFile: '{path}' size {len(data)} is not a positive multiple of {BGR15.DATA_SIZE} (bgr15 colors)")

        self.data = data
