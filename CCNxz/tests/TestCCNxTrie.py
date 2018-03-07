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

class TestCCNxTrie(unittest.TestCase):

    def test_insert(self):
        trie = CCNxTrie()

        token_string = "abcd"
        value = "foo"
        trie.insert(token_string, value)

        truth = "[ (key : a) (value : None) (left : None) (middle : [ (key : b) (value : None) (left : None) (middle : [ (key : c) (value : None) (left : None) (middle : [ (key : d) (value : foo) (left : None) (middle : None) (right : None) ]) (right : None) ]) (right : None) ]) (right : None) ]"
        test = str(trie.root).replace('\n','')

        self.assertTrue(truth == test)

    def test_insert_right(self):
        trie = CCNxTrie()
        trie.insert("abcd", "foo")
        trie.insert("abe", "elephant")

        truth = "[ (key : a) (value : None) (left : None) (middle : [ (key : b) (value : None) (left : None) (middle : [ (key : c) (value : None) (left : None) (middle : [ (key : d) (value : foo) (left : None) (middle : None) (right : None) ]) (right : [ (key : e) (value : elephant) (left : None) (middle : None) (right : None) ]) ]) (right : None) ]) (right : None) ]"
        test = str(trie.root).replace('\n','')

        self.assertTrue(truth == test)

    def test_insert_left(self):
        trie = CCNxTrie()
        trie.insert("abcd", "foo")
        trie.insert("abb", "bar")

        truth = "[ (key : a) (value : None) (left : None) (middle : [ (key : b) (value : None) (left : None) (middle : [ (key : c) (value : None) (left : [ (key : b) (value : bar) (left : None) (middle : None) (right : None) ]) (middle : [ (key : d) (value : foo) (left : None) (middle : None) (right : None) ]) (right : None) ]) (right : None) ]) (right : None) ]"
        test = str(trie.root).replace('\n','')

        self.assertTrue(truth == test)

    def test_search(self):
        trie = CCNxTrie()

        value = "foo"
        trie.insert("abcd", value)

        test = trie.search("abcd")
        self.assertTrue(test == value)


    def test_search_too_short(self):
        trie = CCNxTrie()
        trie.insert("abcd", "foo")

        test = trie.search("abc")
        self.assertTrue(test == None)

    def test_search_too_long(self):
        trie = CCNxTrie()
        trie.insert("abcd", "foo")

        test = trie.search("abcde")
        self.assertTrue(test == None)

    def test_search_left(self):
        trie = CCNxTrie()

        trie.insert("abcd", "foo")
        trie.insert("aba", "apple")

        test = trie.search("aba")
        self.assertTrue(test == "apple")

    def test_search_right(self):
        trie = CCNxTrie()

        trie.insert("abcd", "foo")
        trie.insert("abe", "egg")

        test = trie.search("abe")
        self.assertTrue(test == "egg")

if __name__ == "__main__":
    unittest.main()
