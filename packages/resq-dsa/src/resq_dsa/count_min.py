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

"""Count-Min Sketch probabilistic data structure.

This module provides a Count-Min Sketch implementation for frequency
estimation of elements in a data stream. Useful for top-k queries and
heavy hitter detection with sub-linear space.
"""

import math


class CountMinSketch:
    """Probabilistic data structure for frequency estimation.

    The Count-Min Sketch uses multiple hash tables to estimate the count
    of elements in a stream with guaranteed error bounds. It provides
    an upper bound on frequencies (never underestimates, but may overestimate).

    Attributes:
        _w: Number of columns in the sketch (width).
        _d: Number of rows in the sketch (depth).
        _table: The hash table storage.

    Example:
        >>> sketch = CountMinSketch(epsilon=0.1, delta=0.01)
        >>> sketch.increment("item1")
        >>> sketch.increment("item1")
        >>> sketch.increment("item2")
        >>> sketch.estimate("item1")  # Returns at least 2
        2
        >>> sketch.estimate("item2")  # Returns at least 1
        1
    """

    def __init__(self, epsilon: float, delta: float) -> None:
        """Initialize the Count-Min Sketch.

        Args:
            epsilon: Error parameter. The error in estimation is at most epsilon
                with probability delta. Must be in (0, 1).
            delta: Confidence parameter. Must be in (0, 1).

        Raises:
            ValueError: If epsilon or delta are not in (0, 1).

        Example:
            >>> sketch = CountMinSketch(epsilon=0.1, delta=0.01)
        """
        if epsilon <= 0 or epsilon >= 1:
            raise ValueError(f"epsilon must be in (0, 1), got {epsilon}")
        if delta <= 0 or delta >= 1:
            raise ValueError(f"delta must be in (0, 1), got {delta}")
        w = math.ceil(math.e / epsilon)
        d = math.ceil(math.log(1 / delta))
        self._w, self._d = w, d
        self._table = [[0] * w for _ in range(d)]

    def _hash(self, key: str, seed: int) -> int:
        """Compute hash value for a key with given seed.

        Uses FNV-1a hash variant for good distribution.

        Args:
            key: The string to hash.
            seed: Seed value for hash diversification.

        Returns:
            Hash value modulo the table width.
        """
        h = (2166136261 ^ seed) & 0xFFFFFFFF
        for b in key.encode():
            h ^= b
            h = (h * 16777619) & 0xFFFFFFFF
        return h % self._w

    def increment(self, key: str, count: int = 1) -> None:
        """Increment the count for a key.

        Args:
            key: The key to increment.
            count: Amount to increment by (default: 1).

        Example:
            >>> sketch = CountMinSketch(epsilon=0.1, delta=0.01)
            >>> sketch.increment("error")
            >>> sketch.increment("error", 5)
        """
        for i in range(self._d):
            self._table[i][self._hash(key, i * 0x9E3779B9)] += count

    def estimate(self, key: str) -> int:
        """Estimate the count for a key.

        Returns the minimum across all hash table rows, providing an
        upper bound on the true count.

        Args:
            key: The key to estimate.

        Returns:
            Estimated count (upper bound).

        Example:
            >>> sketch = CountMinSketch(epsilon=0.1, delta=0.01)
            >>> sketch.increment("event")
            >>> sketch.estimate("event")
            1
        """
        return min(self._table[i][self._hash(key, i * 0x9E3779B9)] for i in range(self._d))
