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
from CCNxz.CCNxTrieNode import *

class TestCCNxTrieNode(unittest.TestCase):
    def setUp(self):
        self.key = 33
        self.node = CCNxTrieNode(self.key)

    def test_init(self):
        self.assertEqual(self.node.key, self.key)
        self.assertEqual(self.node.left, None)
        self.assertEqual(self.node.right, None)
        self.assertEqual(self.node.middle, None)
        self.assertEqual(self.node.value, None)

    def test_value(self):
        value = "foo"
        self.node.value = value
        self.assertEqual(self.node.value, value)

    def test_left(self):
        left = CCNxTrieNode(77)
        self.node.left = left
        self.assertEqual(self.node.left, left)

    def test_right(self):
        right = CCNxTrieNode(77)
        self.node.right = right
        self.assertEqual(self.node.right, right)

    def test_middle(self):
        middle = CCNxTrieNode(77)
        self.node.middle = middle
        self.assertEqual(self.node.middle, middle)

if __name__ == "__main__":
    unittest.main()
