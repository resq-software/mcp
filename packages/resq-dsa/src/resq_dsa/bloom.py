# Copyright 2026 ResQ Software
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bloom Filter probabilistic data structure.

This module provides a Bloom Filter implementation for set membership
testing with configurable false positive rate and space efficiency.
"""

import hashlib
import math


class BloomFilter:
    """Space-efficient probabilistic set membership data structure.

       A Bloom Filter can test whether an element is possibly in a set
       or definitely not in the set. It may return false positives but
       never false negatives.

       Attributes:
           _m: Number of bits        _k: in the filter.
    Number of hash functions.
           _bits: Bit array storage.

       Example:
           >>> bf = BloomFilter(capacity=1000)
           >>> bf.add("hello")
           >>> bf.add("world")
           >>> bf.has("hello")
           True
           >>> bf.has("missing")
           False
    """

    def __init__(self, capacity: int, error_rate: float = 0.01) -> None:
        """Initialize the Bloom Filter.

        Args:
            capacity: Expected number of elements to be added.
            error_rate: Desired false positive rate (default: 0.01 = 1%).

        Raises:
            ValueError: If error_rate is not in (0, 1) or capacity < 1.

        Example:
            >>> bf = BloomFilter(capacity=1000, error_rate=0.05)
        """
        if error_rate <= 0 or error_rate >= 1:
            raise ValueError(f"error_rate must be in (0, 1), got {error_rate}")
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        m = math.ceil(-capacity * math.log(error_rate) / math.log(2) ** 2)
        k = max(1, round((m / capacity) * math.log(2)))
        self._m, self._k = m, k
        self._bits = bytearray(math.ceil(m / 8))

    def _hashes(self, item: str) -> list[int]:
        """Generate k hash values for an item.

        Uses double hashing technique with SHA-256 for generating
        multiple independent hash values from a single hash function.

        Args:
            item: The string to hash.

        Returns:
            List of k hash values modulo m.

        Example:
            >>> bf = BloomFilter(capacity=100)
            >>> bf._hashes("test")
            [123, 456, 789]  # Example values
        """
        return [
            int.from_bytes(hashlib.sha256(f"{i}:{item}".encode()).digest()[:4], "little") % self._m
            for i in range(self._k)
        ]

    def add(self, item: str) -> None:
        """Add an item to the Bloom Filter.

        Args:
            item: The string item to add.

        Example:
            >>> bf = BloomFilter(capacity=100)
            >>> bf.add("new_item")
        """
        for idx in self._hashes(item):
            self._bits[idx >> 3] |= 1 << (idx & 7)

    def has(self, item: str) -> bool:
        """Check if an item might be in the set.

        Returns True if the item may have been added (possibly a false
        positive), False if definitely not in the set.

        Args:
            item: The item to check.

        Returns:
            True if possibly in set, False if definitely not.

        Example:
            >>> bf = BloomFilter(capacity=100)
            >>> bf.add("present")
            >>> bf.has("present")
            True
            >>> bf.has("absent")
            False
        """
        return all(self._bits[idx >> 3] & (1 << (idx & 7)) for idx in self._hashes(item))
