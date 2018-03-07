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
# A node in a ternary search trie

__author__ = 'mmosko'

class CCNxTrieNode(object):
    def __init__(self, key):
        self.__left = None
        self.__middle = None
        self.__right = None
        self.__value = None
        self.__key = key

    def __eq__(self, other):
        return self.__key == other.__key

    def __str__(self):
        return "\n[ (key : {}) (value : {}) (left : {}) (middle : {}) (right : {}) ]".format(self.key, self.value, self.left, self.middle, self.right)

    __repr__ = __str__

    @property
    def left(self):
        return self.__left

    @property
    def middle(self):
        return self.__middle

    @property
    def right(self):
        return self.__right


    @property
    def value(self):
        return self.__value


    @property
    def key(self):
        return self.__key

    @left.setter
    def left(self, node):
        self.__left = node

    @middle.setter
    def middle(self, node):
        self.__middle = node

    @right.setter
    def right(self, node):
        self.__right = node

    @value.setter
    def value(self, node):
         self.__value = node
