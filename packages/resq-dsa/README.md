# resq-dsa

Production-grade data structures and algorithms for Python 3.11+ with zero dependencies.

## Data Structures

- **BloomFilter** -- Space-efficient probabilistic set membership testing
- **CountMinSketch** -- Probabilistic frequency estimation for data streams
- **Graph** -- Directed weighted graph with BFS, Dijkstra, and A* pathfinding
- **BoundedHeap** -- Bounded min-heap for top-k queries
- **Trie** -- Prefix tree for efficient string storage and retrieval

## Algorithms

- **rabin_karp** -- Rabin-Karp rolling hash string pattern matching

## Installation

```bash
pip install resq-dsa
```

## Usage

```python
from resq_dsa import BloomFilter, Graph, Trie, BoundedHeap, rabin_karp

# Bloom filter for deduplication
bf = BloomFilter(capacity=10_000)
bf.add("seen-id-1")
assert bf.has("seen-id-1")

# Graph pathfinding
g = Graph()
g.add_edge("A", "B", 1.0)
g.add_edge("B", "C", 2.0)
result = g.dijkstra("A", "C")  # {'path': ['A', 'B', 'C'], 'cost': 3.0}

# Trie prefix search
trie = Trie()
trie.insert("alert")
trie.insert("alarm")
trie.starts_with("al")  # ['alert', 'alarm']

# Pattern matching
rabin_karp("ababab", "ab")  # [0, 2, 4]
```

## License

Apache-2.0
