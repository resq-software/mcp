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

from resq_dsa.heap import BoundedHeap


def make(id, d):
    return {"id": id, "distance": d}


def test_keeps_k_nearest():
    h = BoundedHeap(3, lambda x: x["distance"])
    for item in [
        make("a", 10),
        make("b", 2),
        make("c", 7),
        make("d", 1),
        make("e", 50),
    ]:
        h.insert(item)
    assert h.size == 3
    assert [x["id"] for x in h.to_sorted()] == ["d", "b", "c"]


def test_peek_is_max():
    h = BoundedHeap(2, lambda x: x["distance"])
    h.insert(make("x", 5))
    h.insert(make("y", 3))
    assert h.peek()["id"] == "x"
