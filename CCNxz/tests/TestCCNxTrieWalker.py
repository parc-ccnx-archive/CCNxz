#!/usr/bin/python

#
# Copyright (c) 2016-2018, Xerox Corporation (Xerox) and Palo Alto Research Center, Inc (PARC)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL XEROX OR PARC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


__author__ = 'mmosko'

import unittest
from CCNxz.CCNxTrie import *
from CCNxz.CCNxTrieWalker import *

class TestCCNxTrieWalker(unittest.TestCase):

    def test_search(self):
        trie = CCNxTrie()

        token_string = "abcd"
        value = "foo"
        trie.insert(token_string, value)

        walker = CCNxTrieWalker(trie)
        test_value = None
        success = True
        for i in range(0,len(token_string)):
            token = token_string[i]
            result = walker.next(token)
            if result == CCNxTrieWalker.NoMatch:
                success = False
                break

        self.assertTrue(success)
        self.assertTrue(walker.value() == value)

    def test_search_too_short(self):
        trie = CCNxTrie()

        trie.insert("abcd", "foo")

        token_string = "abc"
        walker = CCNxTrieWalker(trie)
        test_value = None
        success = True
        for i in range(0,len(token_string)):
            token = token_string[i]
            result = walker.next(token)
            if result == CCNxTrieWalker.NoMatch:
                success = False
                break

        self.assertTrue(success)
        self.assertTrue(walker.value() is None)


    def test_search_too_long(self):
        trie = CCNxTrie()

        trie.insert("abcd", "foo")

        token_string = "abcde"
        walker = CCNxTrieWalker(trie)
        test_value = None
        success = True
        for i in range(0,len(token_string)):
            token = token_string[i]
            result = walker.next(token)
            if result == CCNxTrieWalker.NoMatch:
                success = False
                break

        self.assertFalse(success)
        self.assertTrue(walker.value() is None)

    def test_search_left(self):
        trie = CCNxTrie()
        trie.insert("abcd", "foo")
        trie.insert("aba", "apple")

        token_string = "aba"
        walker = CCNxTrieWalker(trie)
        test_value = None
        success = True
        for i in range(0,len(token_string)):
            token = token_string[i]
            result = walker.next(token)
            if result == CCNxTrieWalker.NoMatch:
                success = False
                break

        self.assertTrue(success)
        self.assertTrue(walker.value() == "apple")

    def test_search_right(self):
        trie = CCNxTrie()
        trie.insert("abcd", "foo")
        trie.insert("abd", "donut")

        token_string = "abd"
        walker = CCNxTrieWalker(trie)
        test_value = None
        success = True
        for i in range(0,len(token_string)):
            token = token_string[i]
            result = walker.next(token)
            if result == CCNxTrieWalker.NoMatch:
                success = False
                break

        self.assertTrue(success)
        self.assertTrue(walker.value() == "donut")

if __name__ == "__main__":
    unittest.main()
