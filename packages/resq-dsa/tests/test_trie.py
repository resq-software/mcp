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

from resq_dsa.trie import Trie, rabin_karp


def test_insert_search():
    t = Trie()
    t.insert("drone")
    t.insert("droning")
    assert t.search("drone") and not t.search("dron")


def test_starts_with():
    t = Trie()
    for w in ["alert", "alerting", "alarm", "base"]:
        t.insert(w)
    assert sorted(t.starts_with("al")) == ["alarm", "alert", "alerting"]


def test_rabin_karp():
    assert rabin_karp("ababab", "ab") == [0, 2, 4]
    assert rabin_karp("hello", "xyz") == []
