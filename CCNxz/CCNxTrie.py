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


#
# A simple search trie
#
# Based on Sedgewick's ternary search trie.
# See "Ternary Search Trees" by Jon Bentley and Robert Sedgewick
# in the April, 1998, Dr. Dobb's Journal.
#
# Each node has 3 children: left (less), middle (equal), right (greater)
#
# Each node has one data element so if the search string ends there
# that value is returned

__author__ = 'mmosko'

from CCNxTrieNode import *

class CCNxTrie(object):
    def __init__(self):
        self.__root = None

    @property
    def root(self):
        return self.__root

    def search(self, token_string):
        '''
        Searches the tree for the token_string and returns the Value
        of the node that matches the last byte.  It will return None if
        the string is not found.

        :param token_string:
        :return: The Value or None
        '''

        return self.__search(self.__root, token_string, 0)

    def insert(self, token_string, value):
        '''
        Insert a string into the trie and associate it with a value

        Each byte of token_string is a tree node.

        It is an error to insert duplicates, will raise ValueError.

        :param token_string: The byte string to insert
        :param value: The value to associate with the final 'equals' node
        :return: none
        '''

        self.__root = self.__insert(self.__root, token_string, 0, value)

    def __insert(self, node, token_string, offset, value):
        key = token_string[offset]

        if node is None:
            # If this is the case, then we will automatically fall in to the equals condition
            node = CCNxTrieNode(key)
            #print "Create node key = ", key

        if key < node.key:
            node.left = self.__insert(node.left, token_string, offset, value)
            pass
        elif key > node.key:
            node.right = self.__insert(node.right, token_string, offset, value)
            pass
        else:
            self.__keyEqual(node, token_string, offset, value)

        return node

    def __keyEqual(self, node, token_string, offset, value):
        isLastToken = (offset + 1) == len(token_string)
        if isLastToken:
            if node.value is not None:
                # We are at the end of the token string, so it equals
                # the current node.  However, the node already has a value.
                # So, we are trying to insert a duplicate
                raise ValueError("Duplicate key: ", token_string)

            node.value = value
        else:
            # Otherwise, go down the 'middle' path
            node.middle = self.__insert(node.middle, token_string, offset + 1, value)

    def __search(self, node, token_string, offset):
        if node is None:
            return None

        key = token_string[offset]

        if key < node.key:
            return self.__search(node.left, token_string, offset)
        elif key > node.key:
            return self.__search(node.right, token_string, offset)
        else:
            isLastToken = (offset + 1) == len(token_string)
            if isLastToken:
                return node.value
            else:
                return self.__search(node.middle, token_string, offset + 1)

