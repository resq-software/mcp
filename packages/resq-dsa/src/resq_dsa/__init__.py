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

"""ResQ Data Structures and Algorithms Library.

This package provides performant data structures and algorithms
commonly used in the ResQ disaster response system.

Classes:
    BoundedHeap: Bounded min-heap for top-k queries.
    Graph: Directed weighted graph with pathfinding algorithms.
    Trie: Prefix tree for efficient string operations.
    BloomFilter: Probabilistic set membership structure.
    CountMinSketch: Probabilistic frequency estimation.

Functions:
    rabin_karp: Rabin-Karp string pattern matching algorithm.

Example:
    >>> from resq_dsa import BoundedHeap, Trie, BloomFilter
    >>> trie = Trie()
    >>> trie.insert("disaster")
    >>> bloom = BloomFilter(capacity=1000)
    >>> bloom.add("emergency")
    >>> bloom.has("emergency")
    True
"""

from .bloom import BloomFilter
from .count_min import CountMinSketch
from .graph import Graph
from .heap import BoundedHeap
from .trie import Trie, rabin_karp

__all__ = [
    "BloomFilter",
    "BoundedHeap",
    "CountMinSketch",
    "Graph",
    "Trie",
    "rabin_karp",
]
