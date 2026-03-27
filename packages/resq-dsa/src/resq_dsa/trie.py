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

"""Trie data structure and string matching algorithms.

This module provides a prefix tree (Trie) implementation for efficient
string storage and retrieval, along with the Rabin-Karp string matching
algorithm for pattern search.

Classes:
    Trie: Prefix tree for word storage and prefix-based retrieval.

Functions:
    rabin_karp: Find all occurrences of a pattern in text using rolling hash.
"""


class _Node:
    """Internal node for Trie structure.

    Attributes:
        ch: Dictionary mapping characters to child nodes.
        is_end: Whether this node marks the end of a word.
    """

    __slots__ = ("ch", "is_end")

    def __init__(self) -> None:
        """Initialize a Trie node."""
        self.ch: dict[str, _Node] = {}
        self.is_end = False


class Trie:
    """Prefix tree for efficient string storage and retrieval.

    A Trie organizes strings by common prefixes, enabling fast lookup
    for word existence and autocomplete-style prefix searches.

    Attributes:
        _root: The root node of the Trie.

    Example:
        >>> trie = Trie()
        >>> trie.insert("hello")
        >>> trie.insert("help")
        >>> trie.search("hello")
        True
        >>> trie.starts_with("hel")
        ['hello', 'help']
    """

    def __init__(self) -> None:
        """Initialize an empty Trie."""
        self._root = _Node()

    def insert(self, word: str) -> None:
        """Insert a word into the Trie.

        Args:
            word: The word to insert.

        Example:
            >>> trie = Trie()
            >>> trie.insert("python")
        """
        n = self._root
        for c in word:
            n.ch.setdefault(c, _Node())
            n = n.ch[c]
        n.is_end = True

    def search(self, word: str) -> bool:
        """Check if a word exists in the Trie.

        Args:
            word: The word to search for.

        Returns:
            True if the word exists, False otherwise.

        Example:
            >>> trie = Trie()
            >>> trie.insert("test")
            >>> trie.search("test")
            True
            >>> trie.search("tes")
            False
        """
        n = self._root
        for c in word:
            if c not in n.ch:
                return False
            n = n.ch[c]
        return n.is_end

    def starts_with(self, prefix: str) -> list[str]:
        """Find all words in the Trie that start with a given prefix.

        Args:
            prefix: The prefix to search for.

        Returns:
            List of all words that have the given prefix.

        Example:
            >>> trie = Trie()
            >>> trie.insert("hello")
            >>> trie.insert("help")
            >>> trie.insert("hero")
            >>> trie.starts_with("he")
            ['hello', 'help', 'hero']
        """
        n = self._root
        for c in prefix:
            if c not in n.ch:
                return []
            n = n.ch[c]
        results: list[str] = []

        def dfs(node: _Node, acc: str) -> None:
            if node.is_end:
                results.append(acc)
            for c, child in node.ch.items():
                dfs(child, acc + c)

        dfs(n, prefix)
        return results


def rabin_karp(text: str, pattern: str) -> list[int]:
    """Find all starting positions where pattern occurs in text.

    Uses the Rabin-Karp algorithm with rolling hash for efficient string
    matching. Returns all positions where the pattern matches.

    Args:
        text: The text to search in.
        pattern: The pattern to search for.

    Returns:
        List of starting indices where pattern occurs in text.

    Example:
        >>> rabin_karp("ABABDABACDABABCABAB", "ABABCABAB")
        [10]
        >>> rabin_karp("hello world", "wor")
        [6]
        >>> rabin_karp("test", "xyz")
        []
    """
    n, m = len(text), len(pattern)
    if m > n or not m:
        return []
    BASE, MOD = 31, 1_000_000_007
    pw = [1] * m
    for i in range(1, m):
        pw[i] = pw[i - 1] * BASE % MOD

    def cv(s, i):
        return ord(s[i]) + 1

    ph = wh = 0
    for i in range(m):
        ph = (ph + cv(pattern, i) * pw[m - 1 - i]) % MOD
        wh = (wh + cv(text, i) * pw[m - 1 - i]) % MOD
    matches = [0] if wh == ph and text[:m] == pattern else []
    for i in range(1, n - m + 1):
        wh = (wh - cv(text, i - 1) * pw[m - 1] % MOD + MOD) % MOD
        wh = (wh * BASE + cv(text, i + m - 1)) % MOD
        if wh == ph and text[i : i + m] == pattern:
            matches.append(i)
    return matches
