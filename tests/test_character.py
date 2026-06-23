import unittest

from data.character import Character

def make_character():
    init_data = [0] * 22
    name_data = [0xff] * 6 # padding bytes only, i.e. an empty name
    return Character(0, init_data, name_data)

class TestInitRunSuccess(unittest.TestCase):
    # run success is stored inverted in 2 bits of init_data[21]:
    # 0b11 = 2, 0b10 = 3, 0b01 = 4, 0b00 = 5 (run_value = 5 - bit_value)
    def test_getter_decodes_stored_bits(self):
        character = make_character()
        for raw, expected in ((0b11, 2), (0b10, 3), (0b01, 4), (0b00, 5)):
            character._init_run_success = raw
            self.assertEqual(character.init_run_success, expected)

    def test_setter_round_trip(self):
        # regression test: the setter used to store (value - MAX) instead of
        # (MAX - value), corrupting the bit-packed init data byte
        character = make_character()
        for value in range(Character.MIN_RUN_SUCCESS, Character.MAX_RUN_SUCCESS + 1):
            character.init_run_success = value
            self.assertEqual(character.init_run_success, value)
            self.assertIn(character._init_run_success, (0b00, 0b01, 0b10, 0b11))

    def test_setter_rejects_out_of_range(self):
        character = make_character()
        with self.assertRaises(ValueError):
            character.init_run_success = Character.MIN_RUN_SUCCESS - 1
        with self.assertRaises(ValueError):
            character.init_run_success = Character.MAX_RUN_SUCCESS + 1

class TestInitLevelFactor(unittest.TestCase):
    def test_round_trip(self):
        character = make_character()
        for adjustment in (0, 2, 5, -3):
            character.init_level_factor = adjustment
            self.assertEqual(character.init_level_factor, adjustment)

if __name__ == "__main__":
    unittest.main()
