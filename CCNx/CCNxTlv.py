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


import array

__author__ = 'mmosko'

class CCNxTlv(object):
    def __init__(self, type, length, value):
        self.__type = type
        self.__length = length
        self.__value = value

    def __str__(self):
        return "TLV(%r, %r, %r)" % (self.type, self.length, self.value)

    def __repr__(self):
        return "TLV(%r, %r, %r)" % (self.type, self.length, self.value)

    @property
    def type(self):
        return self.__type

    @property
    def length(self):
        return self.__length

    @property
    def value(self):
        return self.__value

    @length.setter
    def length(self, length):
        self.__length = length

    @staticmethod
    def number_to_array(n):
        """
        Convert a number to a byte array.  Typically used to add a number
        to a TLV with a variable length.

        :param n: A number
        :return: An array of bytes

        """
        if n < 0x100:
            byte_array = [n]
        elif n < 0x10000:
            byte_array = [n >> 8, n & 0xFF]
        elif n < 0x1000000:
            byte_array = [n >> 16, (n >> 8) & 0xFF, n & 0xFF]
        elif n < 0x100000000:
            byte_array = [n >> 24, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF]
        else:
            # skip to 8 bytes
            byte_array = [(n >> 56) & 0xFF, (n >> 48) & 0xFF, (n >> 40) & 0xFF, (n >> 32) & 0xFF,
                          (n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF]

        return array.array("B", byte_array)

    @staticmethod
    def array_to_number(a):
        n = 0
        for b in a:
            n = (n << 8) | b
        return n