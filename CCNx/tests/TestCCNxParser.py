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

from CCNx.CCNxParser import *
from CCNx.CCNxTypes import *

class TestCCNxParser(unittest.TestCase):
    def setUp(self):
        # a test vector for parsing
        self.interest = [
            # fixed header
            0x01, 0x00, 0x00, 0x41, 0x20, 0x00, 0x00, 0x18,
            # interest frag
            0x00, 0x03, 0x00, 0x0c,
            0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x05, 0xdc, 0x00, 0x00,
            # interest
            0x00, 0x01, 0x00, 0x15,
            # name
            0x00, 0x00, 0x00, 0x11,
            # name seg
            0x00, 0x01, 0x00, 0x05,
            0x68, 0x65, 0x6c, 0x6c, 0x6f,
            # name seg
            0x00, 0x02, 0x00, 0x04,
            0x6f, 0x75, 0x63, 0x68,
            # validation alg
            0x00, 0x03, 0x00, 0x04,
            # crc32c
            0x00, 0x02, 0x00, 0x00,
            # validation payload
            0x00, 0x04, 0x00, 0x04,
            0x6a, 0xd7, 0xb1, 0xf2]

        self.compressed = [
            # fixed header
            0x62, 0x30, 0x41, 0x20,
            # interest frag
            0x85,
            0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x05, 0xdc, 0x00, 0x00,
            # interest
            0xc2, 0x15,
            # name
            0xc0, 0x11,
            # nameseg
            0x15,
            0x68, 0x65, 0x6c, 0x6c, 0x6f,
            # nameseg
            0x81,
            0x6f, 0x75, 0x63, 0x68,
            # validation alg + CRC32C + validation payload
            0x84,
            # validation payload
            0x6a, 0xd7, 0xb1, 0xf2]

        # a manifest with 1 manifest link and 2 content object links
        self.manifest = [
                0x01, 0x02, 0x00, 0x9a, 0x00, 0x00, 0x00, 0x08,
                0x00, 0x02, 0x00, 0x8e,
                0x00, 0x00, 0x00, 0x0c,
                0x00, 0x01, 0x00, 0x03, 0x66, 0x6f, 0x6f,
                0x00, 0x0a, 0x00, 0x01, 0x00,
                0x00, 0x07, 0x00, 0x7a,
                0x00, 0x01, 0x00, 0x29,
                0x00, 0x01, 0x00, 0x01, 0x01,
                0x00, 0x02, 0x00, 0x20,
                0xaf, 0xce, 0xa4, 0xed, 0x86, 0xa9, 0xa0, 0x97, 0xc8, 0x12, 0x2d, 0x0b, 0x69, 0xf2, 0x96, 0x1b,
                0x20, 0x03, 0x20, 0xcc, 0x1b, 0xe7, 0x6f, 0x0f, 0xa4, 0x66, 0xd9, 0x43, 0xda, 0x13, 0x7d, 0xcc,
                0x00, 0x02, 0x00, 0x49,
                0x00, 0x01, 0x00, 0x01, 0x02,
                0x00, 0x02, 0x00, 0x40,
                0xc4, 0xbf, 0xec, 0x04, 0x5c, 0x35, 0x1f, 0x47, 0x2c, 0xf8, 0x65, 0xd5, 0x9f, 0x16, 0x67, 0x59,
                0x5a, 0x8d, 0x13, 0x86, 0x2c, 0x42, 0x87, 0xbf, 0x13, 0xae, 0x69, 0x99, 0x58, 0x73, 0x5b, 0x35,
                0xb5, 0x3b, 0x71, 0xd6, 0xde, 0x2b, 0x3b, 0x83, 0x63, 0x41, 0xd1, 0xa5, 0x51, 0xdf, 0x9d, 0x5d,
                0xe5, 0xe8, 0x35, 0x63, 0x55, 0xb4, 0x4a, 0xee, 0x97, 0x0a, 0x28, 0xa4, 0x8c, 0xcf, 0x21, 0xfa]

    def test_parse(self):
        parser = CCNxParser(self.interest)
        parser.parse()
        body = parser.body
        self.assertTrue(body is not None)
        self.assertTrue(len(body) == 3)


    def test_linearize_body(self):
        parser = CCNxParser(self.interest)
        parser.parse()
        linear = parser.linearize_body()
        self.assertTrue(linear is not None)

        # Interest (1)
        #  Name (2)
        #     NameSeg (value) (3), NameSeg (value) (4)
        # ValAlg (5)
        #   CRC32C (6)
        # ValPayload (value) (7)
        self.assertTrue(len(linear) == 7)

        valalg = linear[4]
        self.assertTrue(valalg.type == T_VALALG)
        self.assertTrue(valalg.length == 4)
        self.assertTrue(valalg.value == None)

    def test_manifest(self):
        parser = CCNxParser(self.manifest)
        parser.parse()
        self.assertIsNotNone(parser.manifest_tlv)
        manifest_links = parser.manifest_tlv.value[0]
        data_links = parser.manifest_tlv.value[1]
        self.assertIsNotNone(manifest_links)
        self.assertIsNotNone(data_links)

        self.assertEqual(manifest_links.type, T_MANIFEST_LINKS, "wrong type type {} expected {}".format(
            manifest_links.type,  T_MANIFEST_LINKS))

        manifest_links_start_chunk = manifest_links.value[0]
        manifest_links_hashes = manifest_links.value[1]
        self.assertEqual(manifest_links_start_chunk.type, T_START_CHUNK_NUMBER, "wrong type type {} expected {}".format(
            manifest_links_start_chunk.type,  T_START_CHUNK_NUMBER))

        self.assertEqual(manifest_links_hashes.type, T_HASH_LIST, "wrong type type {} expected {}".format(
            manifest_links_hashes.type,  T_HASH_LIST))

        self.assertEqual(data_links.type, T_DATA_LINKS, "wrong type type {} expected {}".format(
            data_links.type,  T_DATA_LINKS))

        # Don't exhaustively verify the data links section.  It's the same code as gave the correct result for
        # the manifest links section.

if __name__ == "__main__":
    unittest.main()
