import os
import tempfile
import unittest

from graphics.palette_file import PaletteFile
from graphics.sprite_file import SpriteFile

class FakeColor:
    def __init__(self, rgb):
        self.rgb = rgb

class FakePalette:
    def __init__(self):
        self.colors = [FakeColor([n, n, n]) for n in range(16)]

class GraphicsFileTestCase(unittest.TestCase):
    def write_temp(self, content):
        with tempfile.NamedTemporaryFile(delete = False) as temp_file:
            temp_file.write(content)
            self.temp_path = temp_file.name
        return self.temp_path

    def tearDown(self):
        os.unlink(self.temp_path)

class TestPaletteFile(GraphicsFileTestCase):
    def test_valid_palette(self):
        path = self.write_temp(bytes(32)) # 16 bgr15 colors
        palette = PaletteFile(path)
        self.assertEqual(len(palette), 16)

    def test_odd_size_rejected(self):
        path = self.write_temp(bytes(33))
        with self.assertRaises(ValueError):
            PaletteFile(path)

    def test_empty_rejected(self):
        path = self.write_temp(b"")
        with self.assertRaises(ValueError):
            PaletteFile(path)

class TestSpriteFile(GraphicsFileTestCase):
    def test_valid_sprite(self):
        path = self.write_temp(bytes(32 * 4)) # 4 tiles
        sprite = SpriteFile(path, FakePalette())
        self.assertEqual(sprite.tile_count, 4)

    def test_partial_tile_rejected(self):
        path = self.write_temp(bytes(32 * 4 + 1))
        with self.assertRaises(ValueError):
            SpriteFile(path, FakePalette())

    def test_empty_rejected(self):
        path = self.write_temp(b"")
        with self.assertRaises(ValueError):
            SpriteFile(path, FakePalette())

if __name__ == "__main__":
    unittest.main()
