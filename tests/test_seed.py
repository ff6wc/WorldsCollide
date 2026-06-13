import random
import string
import unittest

from seed import SEED_LENGTH, generate_seed, seed_rng

class TestGenerateSeed(unittest.TestCase):
    def test_length(self):
        self.assertEqual(len(generate_seed()), SEED_LENGTH)

    def test_charset(self):
        alpha_digits = set(string.ascii_lowercase + string.digits)
        for _ in range(20):
            self.assertTrue(set(generate_seed()) <= alpha_digits)

class TestSeedRng(unittest.TestCase):
    def setUp(self):
        self._rng_state = random.getstate()

    def tearDown(self):
        random.setstate(self._rng_state)

    def test_returns_given_seed(self):
        self.assertEqual(seed_rng("abc123", "-i -o"), "abc123")

    def test_generates_seed_when_none_given(self):
        seed = seed_rng(None, "")
        self.assertEqual(len(seed), SEED_LENGTH)

    def test_deterministic_for_same_seed_and_flags(self):
        # seed reproducibility is a core requirement: the same seed + flags
        # must always produce the same random stream
        seed_rng("abc123", "-flags")
        first = [random.random() for _ in range(10)]

        seed_rng("abc123", "-flags")
        second = [random.random() for _ in range(10)]

        self.assertEqual(first, second)

    def test_different_flags_produce_different_stream(self):
        seed_rng("abc123", "-flags one")
        first = random.random()

        seed_rng("abc123", "-flags two")
        second = random.random()

        self.assertNotEqual(first, second)

if __name__ == "__main__":
    unittest.main()
