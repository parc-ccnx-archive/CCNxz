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
import array
from CCNxz.CCNxCompressorFixedHeader import *


class TestCCNxCompressorFixedHeader_Compress(unittest.TestCase):

    def test_large_packet_type(self):
        """Packet types over 3 bits are uncompressed"""
        original = [0x01, 0x08, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x08]
        fh = CCNxFixedHeader(original)
        test = CCNxCompressorFixedHeader.compress(fh, context_id=0)
        truth = [0x86, 0x21, 0x08, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x08]
        self.assertTrue(test is not None)
        self.assertTrue(test == truth)

    def test_reserved_bytes(self):
        """Packets with reserved bytes are uncompressed"""

        original = [0x01, 0x01, 0x00, 0x0F, 0x00, 0x01, 0x00, 0x08]
        fh = CCNxFixedHeader(original)
        test = CCNxCompressorFixedHeader.compress(fh, context_id=0)
        truth = [0x86, 0x21, 0x01, 0x00, 0x0F, 0x00, 0x01, 0x00, 0x08]
        self.assertTrue(test is not None)
        self.assertTrue(test == truth)

    def test_pattern_h0_l6_m8(self):
        """should encode to pattern 101"""

        original = [0x01, 0x01, 0x00, 0x3F, 0xFF, 0x00, 0x00, 0x08]
        fh = CCNxFixedHeader(original)

        test = CCNxCompressorFixedHeader.compress(fh, context_id=0)
        truth = [0x86, 0x42, 0x7F, 0xFF]
        self.assertTrue(test is not None)
        self.assertTrue(test == truth)

    def test_pattern_h5_l9_m0(self):
        """should encode to pattern 110"""

        original = [0x01, 0x01, 0x01, 0xFF, 0x00, 0x00, 0x00, 0x1F]
        fh = CCNxFixedHeader(original)

        test = CCNxCompressorFixedHeader.compress(fh, context_id=0)
        truth = [0x86, 0x62, 0x7F, 0xFF]
        self.assertTrue(test is not None)
        self.assertTrue(test == truth)

    def test_pattern_h5_l9_m8(self):
        """should encode to pattern 111"""

        original = [0x01, 0x01, 0x01, 0xFF, 0xFE, 0x00, 0x00, 0x1F]
        fh = CCNxFixedHeader(original)

        test = CCNxCompressorFixedHeader.compress(fh, context_id=0)
        truth = [0x86, 0x82, 0x7F, 0xFF, 0xFE]
        self.assertTrue(test is not None)
        self.assertTrue(test == truth)

class TestCCNxCompressorFixedHeader_Decompress(unittest.TestCase):

    def test_uncompressed(self):
        """Pattern 000 packet is uncompressed"""
        truth = [0x01, 0x08, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x08]
        a = array.array("B")
        a.fromlist(truth)

        test = CCNxCompressorFixedHeader.decompress(a)
        self.assertTrue(test == truth, "truth = {}, test = {}".format(truth, test))

    def test_pattern_h0_l6_m8(self):
        byte_array = [0x86, 0x42, 0x7F, 0xFF, 0x00]
        truth = [0x01, 0x01, 0x00, 0x3F, 0xFF, 0x00, 0x00, 0x08]

        a = array.array("B")
        a.fromlist(byte_array)

        test = CCNxCompressorFixedHeader.decompress(a)
        self.assertTrue(test == truth, "truth = {}, test = {}".format(truth, test))
        self.assertTrue(len(a) == 1, "expected len 1, a = {}".format(a))

    def test_pattern_h5_l9_m0(self):
        byte_array = [0x86, 0x62, 0x7F, 0xFF, 0x00]
        truth = [0x01, 0x01, 0x01, 0xFF, 0x00, 0x00, 0x00, 0x1F]

        a = array.array("B")
        a.fromlist(byte_array)

        test = CCNxCompressorFixedHeader.decompress(a)
        self.assertTrue(test == truth, "truth = {}, test = {}".format(truth, test))
        self.assertTrue(len(a) == 1, "expected len 1, a = {}".format(a))

    def test_pattern_h5_l9_m8(self):
        byte_array = [0x86, 0x82, 0x7F, 0xFF, 0xFE, 0x00]
        truth = [0x01, 0x01, 0x01, 0xFF, 0xFE, 0x00, 0x00, 0x1F]

        a = array.array("B")
        a.fromlist(byte_array)

        test = CCNxCompressorFixedHeader.decompress(a)
        self.assertTrue(test == truth, "truth = {}, test = {}".format(truth, test))
        self.assertTrue(len(a) == 1, "expected len 1, a = {}".format(a))

if __name__ == "__main__":
    unittest.main()
