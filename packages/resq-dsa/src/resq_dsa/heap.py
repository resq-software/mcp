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

"""Bounded heap data structure for top-k queries.

This module provides a bounded min-heap implementation for maintaining
the k smallest (or largest) elements from a stream of data.
"""

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class BoundedHeap(Generic[T]):
    """Bounded min-heap for tracking top-k elements by distance.

    Maintains a fixed-size heap that keeps only the k smallest elements
    according to a provided distance/cost function. Useful for k-nearest
    neighbors, top-k queries, and streaming data processing.

    Attributes:
        _limit: Maximum number of elements to maintain.
        _dist: Function to compute distance/score for elements.
        _data: Internal heap storage.

    Example:
        >>> heap = BoundedHeap(limit=3, dist=lambda x: x)
        >>> for i in [5, 2, 8, 1, 9]:
        ...     heap.insert(i)
        >>> heap.to_sorted()
        [1, 2, 5]
    """

    def __init__(self, limit: int, dist: Callable[[T], float]) -> None:
        """Initialize the bounded heap.

        Args:
            limit: Maximum number of elements to maintain.
            dist: Function to compute the distance/score for ranking.

        Raises:
            ValueError: If limit is less than 1.

        Example:
            >>> heap = BoundedHeap(limit=5, dist=lambda x: abs(x - 10))
        """
        if limit < 1:
            raise ValueError(f"limit must be >= 1, got {limit}")
        self._limit = limit
        self._dist = dist
        self._data: list[T] = []

    def insert(self, entry: T) -> None:
        """Insert an element into the heap.

        If the heap is not full, the element is added. If the heap is full
        and the new element has a lower distance than the current maximum,
        the maximum is replaced with the new element.

        Args:
            entry: The element to insert.

        Example:
            >>> heap = BoundedHeap(limit=3, dist=lambda x: x)
            >>> heap.insert(5)
            >>> heap.insert(2)
        """
        if len(self._data) < self._limit:
            self._data.append(entry)
            self._sift_up(len(self._data) - 1)
        elif self._data and self._dist(entry) < self._dist(self._data[0]):
            self._data[0] = entry
            self._sift_down(0)

    def peek(self) -> T | None:
        """Return the element with minimum distance without removing it.

        Returns:
            The element with lowest distance, or None if heap is empty.

        Example:
            >>> heap = BoundedHeap(limit=3, dist=lambda x: x)
            >>> heap.insert(5)
            >>> heap.peek()
            5
        """
        return self._data[0] if self._data else None

    def to_sorted(self) -> list[T]:
        """Return the heap contents sorted by distance.

        Returns:
            List of elements sorted by distance (ascending).

        Example:
            >>> heap = BoundedHeap(limit=3, dist=lambda x: x)
            >>> heap.insert(5)
            >>> heap.insert(2)
            >>> heap.to_sorted()
            [2, 5]
        """
        return sorted(self._data, key=self._dist)

    @property
    def size(self) -> int:
        """Return the current number of elements in the heap.

        Returns:
            Number of elements currently stored.

        Example:
            >>> heap = BoundedHeap(limit=3, dist=lambda x: x)
            >>> heap.insert(1)
            >>> heap.insert(2)
            >>> heap.size
            2
        """
        return len(self._data)

    def _sift_up(self, i: int) -> None:
        """Move element up to maintain heap property."""
        while i > 0:
            p = (i - 1) >> 1
            if self._dist(self._data[p]) >= self._dist(self._data[i]):
                break
            self._data[p], self._data[i] = self._data[i], self._data[p]
            i = p

    def _sift_down(self, i: int) -> None:
        """Move element down to maintain heap property."""
        n = len(self._data)
        while True:
            largest, left, right = i, 2 * i + 1, 2 * i + 2
            if left < n and self._dist(self._data[left]) > self._dist(self._data[largest]):
                largest = left
            if right < n and self._dist(self._data[right]) > self._dist(self._data[largest]):
                largest = right
            if largest == i:
                break
            self._data[i], self._data[largest] = self._data[largest], self._data[i]
            i = largest
