#!/usr/bin/pyton
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

from CCNxz.CCNxCompressorContextID import *
import itertools


class TextCCNxCompressorContextID(unittest.TestCase):
    def test_encode(self):
        vectors = [
            {'context_id': 0x00, 'byte_array': [0b10000110]},
            {'context_id': 0x07, 'byte_array': [0b10111000]},
            {'context_id': 0x08, 'byte_array': [0b11000100, 0b01110100]},
            {'context_id': 0x3F, 'byte_array': [0b11011111, 0b11000011]}
        ]

        for v in vectors:
            test = CCNxCompressorContextID.encode(v['context_id'])
            self.assertTrue(v['byte_array'] == test, "context_id {} expected {} got {}".format(hex(v['context_id']),
                                                                                               v['byte_array'], test))

    def test_decode(self):
        # byte_array is the input here, so extend it with an extra byte to make sure
        # we are not consuming too many bytes.
        vectors = [
            {'context_id': 0x00, 'byte_array': [0b10000110, 0xFF]},
            {'context_id': 0x07, 'byte_array': [0b10111000, 0xFF]},
            {'context_id': 0x08, 'byte_array': [0b11000100, 0b01110100, 0xFF]},
            {'context_id': 0x3F, 'byte_array': [0b11011111, 0b11000011, 0xFF]},
        ]

        for v in vectors:
            test = CCNxCompressorContextID.decode(v['byte_array'])
            self.assertTrue(len(v['byte_array']) == 1,
                            "Byte array wrong length, expected 1 got ".format(len(v['byte_array'])))
            self.assertTrue(v['context_id'] == test,
                            "context_id expected {} got {}".format(hex(v['context_id']), hex(test)))

        

if __name__ == "__main__":
    unittest.main()
