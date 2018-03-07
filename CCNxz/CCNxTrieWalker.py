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
# We want to search the trie byte-by-byte, not pass a single long string in.
# This is an artifact of how we parse the wire format in to TLV tokens
#
# So, we cannot call a regular trie.search() method, as that wants to walk
# the tree on its own.

__author__ = 'mmosko'

class CCNxTrieWalker(object):
    Match = 1
    NoMatch = 2

    def __init__(self, trie):
        self.__trie = trie
        self.__last = None
        self.__current = self.__trie.root

    def reset(self):
        '''
        Start a new walk of the tree down the 'middle' path.

        :return: none
        '''
        self.__current = self.__trie.root
        self.__last = None

    def next(self, token):
        '''
        Matches token against the first 'equal' node

        :param token:
        :return: CCNxTrieWalker.Match or CCNxTrieWalker.NoMatch
        '''
        return self.__search(token)

    def value(self):
        '''
        Returns the Value of the last matching node

        :return: None (if no last match) or its value
        '''
        if self.__last is None:
            return None

        return self.__last.value

    def last_match(self):
        '''
        Returns the node that matched the last token

        :return: None or the CCNxTrieNode
        '''
        return self.__last

    def __search(self, token):
        if self.__current is not None:
            if token < self.__current.key:
                self.__current = self.__current.left
                return self.__search(token)
            elif token > self.__current.key:
                self.__current = self.__current.right
                return self.__search(token)
            else:
                # keys are equal
                #print "equals node: ", self.__current.key

                self.__last = self.__current
                self.__current = self.__current.middle
                return CCNxTrieWalker.Match

        self.__last = None
        return CCNxTrieWalker.NoMatch
