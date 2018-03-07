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

from CCNxz.CCNxCompressorFixedLength import *
from CCNx.CCNxTlv import *


class TestCCNxCompressorFixedLength_Compress(unittest.TestCase):

    def test_pairs(self):
        """
        Ensure that we can lookup all the token_strings and get the right compressed keys.
        """
        cmpr = CCNxCompressorFixedLength()
        # We access some "private" data following the name manging rules
        for p in CCNxCompressorFixedLength._CCNxCompressorFixedLength__tuples:
            key = CCNxCompressorFixedLength._CCNxCompressorFixedLength__trie.search(p.token_string)
            self.assertTrue(p.compressed_key == key)


    def test_simple_match(self):
        cmpr = CCNxCompressorFixedLength()

        # This entry has no extension.  It's a simple match
        # pairs.append(Pair([0x00, 0x05, 0x00, 0x01], 0x8F))

        tlv = CCNxTlv(0x0005, 0x0001, "foo")
        tlv_list = [tlv]

        encoded = cmpr.compress(tlv_list)
        self.assertTrue(encoded is not None)
        self.assertTrue(encoded == [ 0x8F, 'f', 'o', 'o' ])

        # make sure we consumed the token off the list
        self.assertTrue(len(tlv_list) == 0)

    def test_simple_nomatch(self):
        cmpr = CCNxCompressorFixedLength()

        # This will match out to 3 of 4 bytes

        tlv = CCNxTlv(0x0005, 0x00FF, "foo")
        tlv_list = [tlv]

        encoded = cmpr.compress(tlv_list)
        self.assertTrue(encoded is None)

        # make sure we did not consume the token off the list
        self.assertTrue(len(tlv_list) == 1)


    def test_sub_match(self):
        #     pairs.append(Pair([0x00, 0x03, 0x00, 0x04], 0x83))
        #     pairs.append(Pair([0x00, 0x03, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0x04, 0x00, 0x04], 0x84))
        #
        # The string 0x00030004 will match both 0x83 and the prefix of 0x84.
        # Test with the string 0x00030004000200FF.  It should return 83 and only remove one item
        # from the TLV list

        cmpr = CCNxCompressorFixedLength()

        tlv1 = CCNxTlv(0x0003, 0x0004, None)
        tlv2 = CCNxTlv(0x0002, 0x00FF, None)
        tlv_list = [tlv1, tlv2]

        encoded = cmpr.compress(tlv_list)
        self.assertTrue(encoded is not None)
        self.assertTrue(encoded == [0x83])

        # make sure we consumed the token off the list
        self.assertTrue(len(tlv_list) == 1)

    def test_longest_match(self):
        #     pairs.append(Pair([0x00, 0x03, 0x00, 0x04], 0x83))
        #     pairs.append(Pair([0x00, 0x03, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0x04, 0x00, 0x04], 0x84))
        #
        # The string 0x00030004 will match both 0x83 and the prefix of 0x84.
        # Test with the full string match.  It should return 84 and more 3 items from list
        # from the TLV list

        cmpr = CCNxCompressorFixedLength()

        tlv1 = CCNxTlv(0x0003, 0x0004, None)
        tlv2 = CCNxTlv(0x0002, 0x0000, None)
        tlv3 = CCNxTlv(0x0004, 0x0004, "foo")
        tlv4 = CCNxTlv(0x00FF, 0x00FF, None)

        tlv_list = [tlv1, tlv2, tlv3, tlv4]

        encoded = cmpr.compress(tlv_list)
        self.assertTrue(encoded is not None)
        self.assertTrue(encoded == [ 0x84, 'f', 'o', 'o' ])

        # make sure we consumed the token off the list
        self.assertTrue(len(tlv_list) == 1)

class TestCCNxCompressorFixedLength_Decompress(unittest.TestCase):

    def test_crc32c(self):
        input = [0x80, 0x00]
        truth = [0x00, 0x02, 0x00, 0x00]

        a = array.array("B")
        a.fromlist(input)

        compressor = CCNxCompressorFixedLength()
        test = compressor.decompress(a)

        self.assertTrue(test == truth)

        # it should have only consumed 1 byte
        self.assertTrue(len(a) == 1)

    def test_expiry(self):
        value = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]

        # setup the input with the compressed key, value, and extra junk at end
        input = [0x90]
        input.extend(value)
        input.append(0xFF)

        truth = [0x00, 0x06, 0x00, 0x08]

        a = array.array("B")
        a.fromlist(input)

        compressor = CCNxCompressorFixedLength()
        test = compressor.decompress(a)

        self.assertTrue(test == truth)

        # it should have only consumed 9 byte
        self.assertTrue(len(a) == 9)

if __name__ == "__main__":
    unittest.main()
