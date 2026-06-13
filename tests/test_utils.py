import random
import unittest

from utils.compression import compress, decompress
from utils.flatten import flatten
from utils.intersection import intersection
from utils.shuffle_if import shuffle_if
from utils.truncated_discrete_distribution import truncated_discrete_distribution
from utils.weighted_random import weighted_random

class TestFlatten(unittest.TestCase):
    def test_scalar(self):
        self.assertEqual(flatten(5), [5])

    def test_flat_list(self):
        self.assertEqual(flatten([1, 2, 3]), [1, 2, 3])

    def test_nested_lists_and_tuples(self):
        self.assertEqual(flatten([1, [2, (3, 4)], [[5]]]), [1, 2, 3, 4, 5])

    def test_bytes_are_flattened_to_ints(self):
        self.assertEqual(flatten(b"\x01\x02"), [1, 2])

    def test_strings_are_not_flattened(self):
        # strings are labels in the memory model and must stay intact
        self.assertEqual(flatten(["LABEL", 1]), ["LABEL", 1])

    def test_empty(self):
        self.assertEqual(flatten([]), [])

class TestCompression(unittest.TestCase):
    def assert_round_trip(self, data):
        self.assertEqual(decompress(compress(data)), data)

    def test_round_trip_repetitive_data(self):
        self.assert_round_trip([1, 2, 3] * 100)

    def test_round_trip_incompressible_data(self):
        rng = random.Random(42)
        self.assert_round_trip([rng.randrange(256) for _ in range(500)])

    def test_round_trip_runs(self):
        self.assert_round_trip([0] * 1000)

    def test_round_trip_mixed(self):
        data = list(range(256)) + [7] * 50 + list(range(0, 256, 2)) * 3
        self.assert_round_trip(data)

    def test_size_header(self):
        compressed = compress([1, 2, 3] * 10)
        size = int.from_bytes(bytes(compressed[:2]), "little")
        self.assertEqual(size, len(compressed))

    def test_oversized_output_raises(self):
        # incompressible data grows ~9/8x when compressed; this used to
        # print an error and return a truncated size header instead of raising
        rng = random.Random(42)
        data = [rng.randrange(256) for _ in range(60000)]
        with self.assertRaises(ValueError):
            compress(data)

class TestIntersection(unittest.TestCase):
    def test_intersection_preserves_first_list_order(self):
        self.assertEqual(intersection([3, 1, 2, 5], [2, 3]), [3, 2])

    def test_disjoint(self):
        self.assertEqual(intersection([1, 2], [3, 4]), [])

class TestWeightedRandom(unittest.TestCase):
    def test_returns_valid_index(self):
        rng_state = random.getstate()
        try:
            random.seed("weighted_random test")
            for _ in range(100):
                self.assertIn(weighted_random([1, 2, 3]), (0, 1, 2))
        finally:
            random.setstate(rng_state)

    def test_zero_weights_never_chosen(self):
        rng_state = random.getstate()
        try:
            random.seed("weighted_random test")
            for _ in range(100):
                self.assertEqual(weighted_random([0, 1, 0]), 1)
        finally:
            random.setstate(rng_state)

class TestTruncatedDiscreteDistribution(unittest.TestCase):
    def setUp(self):
        self._rng_state = random.getstate()
        random.seed("truncated_discrete_distribution test")

    def tearDown(self):
        random.setstate(self._rng_state)

    def test_respects_bounds(self):
        for _ in range(200):
            result = truncated_discrete_distribution(10, 5, 8, 12)
            self.assertTrue(8 <= result <= 12)

    def test_impossible_bounds_raise(self):
        # used to recurse forever; e.g. minimum above maximum
        with self.assertRaises(ValueError):
            truncated_discrete_distribution(10, 1, minimum = 110, maximum = 105)

class TestShuffleIf(unittest.TestCase):
    def test_only_matching_elements_move(self):
        rng_state = random.getstate()
        try:
            random.seed("shuffle_if test")
            values = list(range(20))
            original = list(values)
            is_even = lambda value : value % 2 == 0

            shuffle_if(values, is_even)

            # odd elements stay in place
            for index, value in enumerate(original):
                if not is_even(value):
                    self.assertEqual(values[index], value)
            # even elements are permuted amongst themselves
            self.assertEqual(sorted(v for v in values if is_even(v)),
                             sorted(v for v in original if is_even(v)))
        finally:
            random.setstate(rng_state)

if __name__ == "__main__":
    unittest.main()
