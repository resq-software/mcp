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

from resq_dsa.graph import Graph


def test_bfs():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    assert g.bfs("A") == ["A", "B", "C", "D"]


def test_dijkstra():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("A", "C", 4)
    g.add_edge("B", "C", 2)
    g.add_edge("C", "D", 1)
    r = g.dijkstra("A", "D")
    assert r["path"] == ["A", "B", "C", "D"]
    assert r["cost"] == 4.0


def test_dijkstra_unreachable():
    g = Graph()
    g.add_edge("A", "B")
    assert g.dijkstra("A", "Z") is None


def test_astar():
    g = Graph()
    g.add_edge(0, 1, 1)
    g.add_edge(1, 2, 1)
    g.add_edge(0, 3, 10)
    g.add_edge(3, 2, 1)
    r = g.astar(0, 2, lambda a, b: abs(a - b))
    assert r["path"] == [0, 1, 2]
    assert r["cost"] == 2.0
