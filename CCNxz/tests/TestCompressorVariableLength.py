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

from CCNxz.CCNxCompressorVariableLength import *
from CCNx.CCNxTlv import *


class TestCCNxCompressorVariableLength_Compress(unittest.TestCase):

    def test_pattern_3_4(self):
        tlv = CCNxTlv(0x0001, 0x000F, "0123456789abcdef")

        encoded = CCNxCompressorVariableLength.compress(tlv)
        self.assertTrue(encoded is not None)
        self.assertTrue(encoded == [ 0x1F ])

    def test_pattern_4_9(self):
        tlv = CCNxTlv(0x0001, 0x01FF, "apple pie...")
        truth = [0xC3, 0xFF]
        encoded = CCNxCompressorVariableLength.compress(tlv)

        self.assertTrue(encoded is not None)
        self.assertTrue(encoded == truth)

    def test_compress_15_5(self):
        """15-bit T with length over 5 bits compacted, not compressed"""
        tlv = CCNxTlv(0x4000, 0x0020, "apple pie...")
        encoded = CCNxCompressorVariableLength.compress(tlv)
        self.assertTrue(encoded is None)

    def test_compress_16_10(self):
        """16 bit T's not compressed, they are compacted"""
        tlv = CCNxTlv(0x8000, 0x0001, "apple pie...")
        encoded = CCNxCompressorVariableLength.compress(tlv)
        self.assertTrue(encoded is None)

    def test_pattern_15_5(self):
        tlv = CCNxTlv(0x7FFE, 0x001F, "apple pie...")
        truth = [0xEF, 0xFF, 0xDF]

        encoded = CCNxCompressorVariableLength.compact(tlv)
        self.assertTrue(encoded == truth)

    def test_pattern_16_10(self):
        tlv = CCNxTlv(0x8686, 0x03FF, "apple pie...")
        truth = [0xFA, 0x1A, 0x1B, 0xFF]
        encoded = CCNxCompressorVariableLength.compact(tlv)
        self.assertTrue(encoded == truth)

    def test_pattern_16_16(self):
        tlv = CCNxTlv(0x8686, 0x83FF, "apple pie...")
        truth = [0xFF, 0x86, 0x86, 0x83, 0xFF]
        encoded = CCNxCompressorVariableLength.compact(tlv)
        self.assertTrue(encoded == truth)

class TestCCNxCompressorVariableLength_Decompress(unittest.TestCase):

    def test_pattern_3_4(self):
        input = [0x1F, 0x00]
        truth = [0x00, 0x01, 0x00, 0x0F]
        test = CCNxCompressorVariableLength.decompress(input)
        self.assertTrue(test == truth)
        self.assertTrue(len(input) == 1)

    def test_pattern_4_9(self):
        input = [0xC3, 0xFF, 0x00]
        truth = [0x00, 0x01, 0x01, 0xFF]
        test = CCNxCompressorVariableLength.decompress(input)
        self.assertTrue(test == truth)
        self.assertTrue(len(input) == 1)

    def test_pattern_15_5(self):
        input = [0xEF, 0xFF, 0xDF, 0x00]
        truth = [0x7F, 0xFE, 0x00, 0x1F]
        test = CCNxCompressorVariableLength.decompress(input)
        self.assertTrue(test == truth)
        self.assertTrue(len(input) == 1)

    def test_pattern_16_10(self):
        input = [0xFA, 0x1A, 0x1B, 0xFF, 0x00]
        truth = [0x86, 0x86, 0x03, 0xFF]
        test = CCNxCompressorVariableLength.decompress(input)
        self.assertTrue(test == truth)
        self.assertTrue(len(input) == 1)

    def test_pattern_16_16(self):
        input = [0xFF, 0x86, 0x86, 0x83, 0xFF, 0x00]
        truth = [0x86, 0x86, 0x83, 0xFF]
        test = CCNxCompressorVariableLength.decompress(input)
        self.assertTrue(test == truth)
        self.assertTrue(len(input) == 1)

if __name__ == "__main__":
    unittest.main()
