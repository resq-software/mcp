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

"""Graph data structures and shortest path algorithms.

This module provides a graph representation with implementations of
Breadth-First Search, Dijkstra's algorithm, and A* pathfinding.
"""

import heapq
from collections import deque
from collections.abc import Callable


class Graph:
    """Directed weighted graph for pathfinding and traversal.

    Supports adding edges and computing shortest paths using BFS,
    Dijkstra's algorithm, and A* search.

    Attributes:
        _adj: Adjacency list representation.
        _counter: Counter for tiebreaking in priority queue.

    Example:
        >>> g = Graph()
        >>> g.add_edge("A", "B", 1.0)
        >>> g.add_edge("B", "C", 2.0)
        >>> g.bfs("A")
        ['A', 'B', 'C']
        >>> g.dijkstra("A", "C")
        {'path': ['A', 'B', 'C'], 'cost': 3.0}
    """

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._adj: dict = {}
        self._counter = 0

    def add_edge(self, from_: object, to: object, weight: float = 1.0) -> None:
        """Add a directed edge to the graph.

        Args:
            from_: Source node.
            to: Destination node.
            weight: Edge weight (default: 1.0).

        Example:
            >>> g = Graph()
            >>> g.add_edge("start", "end", 5.0)
        """
        self._adj.setdefault(from_, []).append((to, weight))

    def bfs(self, start: object) -> list:
        """Perform Breadth-First Search from start node.

        Returns nodes in order of distance from start (unweighted).

        Args:
            start: Starting node.

        Returns:
            List of nodes visited in BFS order.

        Example:
            >>> g = Graph()
            >>> g.add_edge("A", "B")
            >>> g.add_edge("A", "C")
            >>> g.bfs("A")
            ['A', 'B', 'C']
        """
        visited, queue, result = {start}, deque([start]), []
        while queue:
            node = queue.popleft()
            result.append(node)
            for nb, _ in self._adj.get(node, []):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return result

    def dijkstra(self, start: object, end: object) -> dict | None:
        """Find shortest path using Dijkstra's algorithm.

        Computes the minimum cost path between start and end nodes.

        Args:
            start: Starting node.
            end: Target node.

        Returns:
            Dictionary with 'path' (list of nodes) and 'cost' (float),
            or None if no path exists.

        Example:
            >>> g = Graph()
            >>> g.add_edge("A", "B", 1.0)
            >>> g.add_edge("B", "C", 2.0)
            >>> g.dijkstra("A", "C")
            {'path': ['A', 'B', 'C'], 'cost': 3.0}
        """
        dist: dict = {start: 0.0}
        prev: dict = {}
        self._counter += 1
        pq = [(0.0, self._counter, start)]
        while pq:
            d, _, u = heapq.heappop(pq)
            if u == end:
                break
            if d > dist.get(u, float("inf")):
                continue
            for v, w in self._adj.get(u, []):
                alt = d + w
                if alt < dist.get(v, float("inf")):
                    dist[v] = alt
                    prev[v] = u
                    self._counter += 1
                    heapq.heappush(pq, (alt, self._counter, v))
        if end not in dist:
            return None
        path, cur = [], end
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()
        return {"path": path, "cost": dist[end]}

    def astar(
        self, start: object, end: object, h: Callable[[object, object], float]
    ) -> dict | None:
        """Find shortest path using A* algorithm.

        Uses a heuristic function to guide the search toward the goal.

        Args:
            start: Starting node.
            end: Target node.
            h: Heuristic function estimating cost from node to goal.

        Returns:
            Dictionary with 'path' (list of nodes) and 'cost' (float),
            or None if no path exists.

        Example:
            >>> g = Graph()
            >>> g.add_edge("A", "B", 1.0)
            >>> g.add_edge("B", "C", 2.0)
            >>> h = lambda n, goal: abs(ord(goal) - ord(n))  # Simple heuristic
            >>> g.astar("A", "C", h)
            {'path': ['A', 'B', 'C'], 'cost': 3.0}
        """
        g: dict = {start: 0.0}
        prev: dict = {}
        self._counter += 1
        pq = [(h(start, end), 0.0, self._counter, start)]
        while pq:
            _, cost, _, u = heapq.heappop(pq)
            if u == end:
                path, cur = [], end
                while cur is not None:
                    path.append(cur)
                    cur = prev.get(cur)
                path.reverse()
                return {"path": path, "cost": g[end]}
            if cost > g.get(u, float("inf")):
                continue
            for v, w in self._adj.get(u, []):
                alt = cost + w
                if alt < g.get(v, float("inf")):
                    g[v] = alt
                    prev[v] = u
                    self._counter += 1
                    heapq.heappush(pq, (alt + h(v, end), alt, self._counter, v))
        return None
