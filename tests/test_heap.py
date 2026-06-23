import unittest

from memory.errors import RomSpaceError
from memory.heap import Block, Heap

class TestBlock(unittest.TestCase):
    def test_size_is_inclusive_of_both_ends(self):
        self.assertEqual(Block(0, 0).size, 1)
        self.assertEqual(Block(0, 9).size, 10)

    def test_swapped_bounds_are_normalized(self):
        block = Block(9, 0)
        self.assertEqual(block.start, 0)
        self.assertEqual(block.end, 9)
        self.assertEqual(block.size, 10)

class TestHeap(unittest.TestCase):
    def setUp(self):
        self.heap = Heap()

    def test_allocate_from_empty_heap_raises(self):
        with self.assertRaises(RomSpaceError):
            self.heap.allocate(1)

    def test_allocate_raises_memory_error_for_backward_compatibility(self):
        with self.assertRaises(MemoryError):
            self.heap.allocate(1)

    def test_free_then_allocate(self):
        self.heap.free(0x100, 0x1ff)
        self.assertEqual(self.heap.available, 0x100)

        start = self.heap.allocate(0x10)
        self.assertEqual(start, 0x100)
        self.assertEqual(self.heap.available, 0xf0)

    def test_allocate_uses_best_fit_block(self):
        self.heap.free(0, 99)       # 100 byte block
        self.heap.free(200, 219)    # 20 byte block

        start = self.heap.allocate(20)
        self.assertEqual(start, 200) # exact fit preferred over larger block
        self.assertEqual(self.heap.available, 100)

    def test_allocate_more_than_largest_block_raises(self):
        self.heap.free(0, 99)
        self.heap.free(200, 219)
        with self.assertRaises(RomSpaceError):
            self.heap.allocate(101) # 120 bytes available but largest block is 100

    def test_free_merges_adjacent_blocks(self):
        self.heap.free(0, 9)
        self.heap.free(10, 19)
        self.assertEqual(self.heap.available, 20)
        self.assertEqual(len(self.heap.blocks), 1)
        self.assertEqual(self.heap.allocate(20), 0)

    def test_free_merges_overlapping_blocks(self):
        self.heap.free(0, 14)
        self.heap.free(10, 19)
        self.assertEqual(self.heap.available, 20)
        self.assertEqual(len(self.heap.blocks), 1)

    def test_free_inside_existing_block_changes_nothing(self):
        self.heap.free(0, 99)
        self.heap.free(40, 59)
        self.assertEqual(self.heap.available, 100)
        self.assertEqual(len(self.heap.blocks), 1)

    def test_reserve_splits_free_block(self):
        self.heap.free(0, 99)
        self.heap.reserve(40, 59)
        self.assertEqual(self.heap.available, 80)

        # neither remaining block can hold more than 40 bytes
        with self.assertRaises(RomSpaceError):
            self.heap.allocate(41)
        self.assertEqual(self.heap.allocate(40), 0)
        self.assertEqual(self.heap.allocate(40), 60)

    def test_reserve_trims_overlapping_block(self):
        self.heap.free(0, 99)
        self.heap.reserve(50, 120)
        self.assertEqual(self.heap.available, 50)
        self.assertEqual(self.heap.allocate(50), 0)

    def test_reserve_consumes_fully_covered_block(self):
        self.heap.free(10, 19)
        self.heap.reserve(0, 29)
        self.assertEqual(self.heap.available, 0)
        self.assertEqual(len(self.heap.blocks), 0)

if __name__ == "__main__":
    unittest.main()
