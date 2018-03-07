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

"""
Read in a two column file of (symbol, weight) and generate a huffman tree
"""

__author__ = 'mmosko'

import sys
import re
import types

class TreeNode(object):
    def __init__(self, symbol, weight):
        self.__symbol = symbol
        self.__weight = int(weight)

    def __lt__(self, other):
        if self.__weight > other.__weight:
            return True
        elif self.__weight > other.__weight and self.__symbol < other.symbol:
            return True
        else:
            return False

    def __str__(self):
        return "({}, {})".format(self.__symbol, self.__weight)

    def __repr__(self):
        return self.__str__()

    @property
    def weight(self):
        return self.__weight

    @property
    def symbol(self):
        return self.__symbol


class HuffmanTree(object):
    def __init__(self, symbols):
        self.__symbols = symbols

    def generate_tree(self):
        while len(self.__symbols) >= 2:
            # pop 2 symbols from end of list
            a = self.__symbols.pop()
            b = self.__symbols.pop()

            print [a, b]

            tree_node = TreeNode([b, a], a.weight + b.weight)
            self.__symbols.append(tree_node)
            self.__symbols.sort()
            self.generate_tree()

    def print_tree(self):
        print "__symbols = ", self.__symbols
        self.__print(self.__symbols[0], [])

    def __print(self, symbol, code):
        s = symbol.symbol
        if type(s) == types.ListType:
            #print "code = {} symbols = {}".format(code, symbol)
            left = s.pop()
            left_code = list(code)
            left_code.append(0)
            self.__print(left, left_code)

            right = s.pop()
            right_code = list(code)
            right_code.append(1)
            self.__print(right, right_code)
        else:
            print "{}, \"{}\"".format(symbol.symbol, self.__code_string(code))

    @staticmethod
    def __code_string(code):
        string = ""
        for v in code:
            string += chr(ord('0') + v)
        return string

    @property
    def symbols(self):
        return self.__symbols

if len(sys.argv) == 2:
    fh = open(sys.argv[1],"r")
    symbols = []
    for f in fh:
        tokens = re.split("[ \t]", f.strip())
        tree_node = TreeNode(tokens[0], int(tokens[1]))
        symbols.append(tree_node)
else:
    symbols = [
        TreeNode('A', 10),
        TreeNode('B', 5),
        TreeNode('C', 3),
        TreeNode('D', 3),
        TreeNode('E', 1)
    ]

symbols.sort()
print symbols

print "Building huffman tree"
tree = HuffmanTree(symbols)
tree.generate_tree()

print "Final tree, len = ", len(tree.symbols)
print tree.print_tree()
