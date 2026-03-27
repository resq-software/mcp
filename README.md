# ResQ PyPI Packages

[![CI](https://img.shields.io/github/actions/workflow/status/resq-software/pypi/ci.yml?branch=main&label=CI&style=flat-square)](https://github.com/resq-software/pypi/actions)
[![resq-mcp](https://img.shields.io/pypi/v/resq-mcp?style=flat-square&label=resq-mcp)](https://pypi.org/project/resq-mcp/)
[![resq-dsa](https://img.shields.io/pypi/v/resq-dsa?style=flat-square&label=resq-dsa)](https://pypi.org/project/resq-dsa/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square)](LICENSE)

Repository for all ResQ Python packages published to [PyPI](https://pypi.org/).

## Packages

| Package | Description | Version |
|---|---|---|
| [`resq-mcp`](packages/resq-mcp/) | FastMCP server exposing ResQ platform capabilities to AI agents | [![PyPI](https://img.shields.io/pypi/v/resq-mcp?style=flat-square)](https://pypi.org/project/resq-mcp/) |
| [`resq-dsa`](packages/resq-dsa/) | Zero-dependency data structures & algorithms | [![PyPI](https://img.shields.io/pypi/v/resq-dsa?style=flat-square)](https://pypi.org/project/resq-dsa/) |

---

## resq-dsa

Production-grade data structures and algorithms. Python 3.11+, zero dependencies.

### Installation

```bash
pip install resq-dsa
# or
uv add resq-dsa
```

### Usage

#### BloomFilter

Probabilistic set membership with configurable false positive rate.

```python
from resq_dsa import BloomFilter

bf = BloomFilter(capacity=10_000, error_rate=0.01)
bf.add("drone-001")
bf.add("drone-002")

bf.has("drone-001")  # True
bf.has("drone-999")  # False (probably)
```

#### CountMinSketch

Probabilistic frequency estimation.

```python
from resq_dsa import CountMinSketch

cms = CountMinSketch(epsilon=0.01, delta=0.01)
cms.increment("sensor-reading", 5)
cms.increment("sensor-reading", 3)

cms.estimate("sensor-reading")  # ~8
```

#### Graph

Directed weighted graph with BFS, Dijkstra, and A* pathfinding.

```python
from resq_dsa import Graph

g = Graph()
g.add_edge("base", "wp-1", weight=100)
g.add_edge("wp-1", "wp-2", weight=50)
g.add_edge("base", "wp-2", weight=200)

# Breadth-first traversal
g.bfs("base")  # ['base', 'wp-1', 'wp-2']

# Shortest path (Dijkstra)
result = g.dijkstra("base", "wp-2")
# {'path': ['base', 'wp-1', 'wp-2'], 'cost': 150}

# A* with heuristic
result = g.astar("base", "wp-2", heuristic=lambda n: 0)
```

#### BoundedHeap

Bounded min-heap for top-k tracking by distance function.

```python
from resq_dsa import BoundedHeap

heap = BoundedHeap(limit=3, dist=lambda x: x["priority"])
heap.insert({"name": "alpha", "priority": 5.0})
heap.insert({"name": "bravo", "priority": 1.0})
heap.insert({"name": "charlie", "priority": 3.0})
heap.insert({"name": "delta", "priority": 0.5})  # evicts highest

heap.peek()       # lowest priority item
heap.to_sorted()  # sorted by distance
heap.size         # 3
```

#### Trie

Prefix tree for string operations.

```python
from resq_dsa import Trie

trie = Trie()
trie.insert("disaster")
trie.insert("dispatch")
trie.insert("distance")

trie.search("disaster")       # True
trie.search("disast")         # False
trie.starts_with("dis")       # ['disaster', 'dispatch', 'distance']
```

#### Rabin-Karp

Rolling hash string pattern matching. Returns list of starting indices.

```python
from resq_dsa import rabin_karp

rabin_karp("the quick brown fox", "quick")  # [4]
rabin_karp("abcabcabc", "abc")              # [0, 3, 6]
```

---

## resq-mcp

FastMCP server connecting AI agents to ResQ's drone fleet, predictive intelligence, and digital twin systems. See the [resq-mcp README](packages/resq-mcp/README.md) for full documentation.

```bash
pip install resq-mcp
resq-mcp  # Start in STDIO mode
```

---

## Development

Each package is independent with its own `pyproject.toml` and virtual environment.

```bash
# resq-dsa
cd packages/resq-dsa
uv sync
uv run pytest                    # Run tests
uv run ruff check src/ tests/   # Lint

# resq-mcp
cd packages/resq-mcp
uv sync
uv run pytest                    # Run tests (unit + integration + property)
uv run ruff check src/ tests/   # Lint
uv run mypy src/                 # Type check
```

## Contributing

1. Fork the repo and create a feature branch
2. Make changes in the appropriate `packages/` directory
3. Run tests and linting for the affected package
4. Open a PR against `main`

## License

Apache-2.0. See [LICENSE](LICENSE) for details.
