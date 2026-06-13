import unittest

from graphics.sprite import Sprite
from graphics.sprite_tile import SpriteTile

class FakeColor:
    def __init__(self, rgb):
        self.rgb = rgb

class FakePalette:
    def __init__(self):
        # 16 colors; color id n -> rgb (n, n, n) for easy assertions
        self.colors = [FakeColor([n, n, n]) for n in range(16)]

def make_sprite(tile_count = 4):
    sprite = Sprite([], FakePalette())
    # tile n filled entirely with color id n via the data setter
    data = []
    for n in range(tile_count):
        tile = SpriteTile()
        tile.colors = [[n] * SpriteTile.COL_COUNT for _ in range(SpriteTile.ROW_COUNT)]
        data.extend(tile.data)
    sprite.data = data
    return sprite

class TestSprite(unittest.TestCase):
    def test_data_round_trip(self):
        sprite = make_sprite()
        self.assertEqual(sprite.tile_count, 4)
        self.assertEqual(sprite.tiles[2].colors[0][0], 2)

    def test_rgb_data_single_tile(self):
        sprite = make_sprite()
        rgb = sprite.rgb_data([[1]])
        self.assertEqual(len(rgb), SpriteTile.ROW_COUNT * SpriteTile.COL_COUNT * 3)
        self.assertEqual(set(rgb), {1}) # tile 1 is solid color id 1 -> rgb 1,1,1

    def test_rgb_data_2x2_layout(self):
        sprite = make_sprite()
        pose = [[0, 1], [2, 3]]
        rgb = sprite.rgb_data(pose)
        width = SpriteTile.COL_COUNT * 2
        height = SpriteTile.ROW_COUNT * 2
        self.assertEqual(len(rgb), width * height * 3)

        # top-left pixel from tile 0, top-right from tile 1
        self.assertEqual(rgb[0], 0)
        self.assertEqual(rgb[(width - 1) * 3], 1)
        # bottom-left from tile 2, bottom-right from tile 3
        self.assertEqual(rgb[(height - 1) * width * 3], 2)
        self.assertEqual(rgb[(height * width - 1) * 3], 3)

    def test_get_ppm_header(self):
        sprite = make_sprite()
        ppm = bytes(sprite.get_ppm([[0]]))
        self.assertTrue(ppm.startswith(b"P6"))

if __name__ == "__main__":
    unittest.main()
