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
A decomporessor for working with uncompressed wire format.
"""

__author__ = 'mmosko'

class CCNxNullDecompressor(object):
    @staticmethod
    def decompress_fixed_header(byte_array):
        """
        Returns a list of bytes that is the fixed header

        :param byte_array: Input byte stream
        :return: List of bytes or None
        """
        if not CCNxNullDecompressor.is_uncompressed_fixed_header(byte_array):
            raise ValueError("Uncompressed fixed header must start with 0b0000")

        output = byte_array[0:8]
        del(byte_array[0:8])

        return output

    @staticmethod
    def decompress_type_length(byte_array):
        output = byte_array[0:4]
        del(byte_array[0:4])
        return output

    @staticmethod
    def is_uncompressed_fixed_header(byte_array):
        byte0 = byte_array[0]
        if byte0 & 0x80 == 0x00:
            return True
        return False

