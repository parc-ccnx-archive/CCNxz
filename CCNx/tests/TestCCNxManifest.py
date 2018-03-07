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

from CCNx.CCNxManifest import *
from CCNx.CCNxName import *


class TestCCNxManifest(unittest.TestCase):
    def test_init(self):
        name = CCNxNameFactory.from_uri("lci:/foo")
        manifest = CCNxManifest(name, 4, 20)
        self.assertTrue(manifest is not None)
        self.assertTrue(manifest.name == name)

    def test_add_data_link(self):
        data_name = CCNxNameFactory.from_uri("lci:/foo/chunk=\x01")
        co = CCNxContentObject(data_name, None)
        co_hash = co.hash()

        data_fanout = 20
        manifest_name = CCNxNameFactory.from_uri("lci:/foo")
        manifest = CCNxManifest(manifest_name, 4, data_fanout)
        manifest.add_data_link(co)
        length = manifest.data_links_length()
        self.assertTrue(length == 1, "Wrong length, expected {} got {}".format(1, length))

        wire_format = manifest.get_content_object().wire_format

        truth = [0x01, 0x02, 0x00, 0x48, 0x00, 0x00, 0x00, 0x08,
                 0x00, 0x02, 0x00, 0x3c,
                 0x00, 0x00, 0x00, 0x07,
                 0x00, 0x01, 0x00, 0x03, 0x66, 0x6f, 0x6f,
                 0x00, 0x07, 0x00, 0x2d,
                 0x00, 0x02, 0x00, 0x29,
                 0x00, 0x01, 0x00, 0x01, 0x01,
                 0x00, 0x02, 0x00, 0x20] + co_hash.tolist()

        truth_array = array.array("B", truth)

        self.assertTrue(wire_format == truth_array, "wrong wire format, expected\n{}\ngot\n{}".format(
            ["0x{:02x}".format(b) for b in truth],
            ["0x{:02x}".format(b) for b in wire_format]))

    def test_add_manifest_link(self):
        name = CCNxNameFactory.from_uri("lci:/foo")
        manifest_1 = CCNxManifest(name, 4, 20)
        fanout = 3
        manifest_2 = CCNxManifest(name, fanout, 10)
        manifest_2.add_manifest_link(manifest_1)
        length = manifest_2.manifest_links_length()
        self.assertTrue(length == 1, "Wrong length, expected {} got {}".format(1, length))
        remaining = manifest_2.remaining_manifest_fanout()
        self.assertTrue(remaining == fanout - 1, "Wrong fanout, expected {} got {}".format(fanout - 1, remaining))

    def test_get_content_object(self):
        prefix = CCNxNameFactory.from_uri("lci:/foo")
        manifest_0_name = CCNxNameFactory.from_name(prefix, 0)
        manifest_1_name = CCNxNameFactory.from_name(prefix, 1)
        co_2_name = CCNxNameFactory.from_name(prefix, 2)
        co_3_name = CCNxNameFactory.from_name(prefix, 3)

        manifest_0 = CCNxManifest(manifest_0_name, 4, 20)
        manifest_1 = CCNxManifest(manifest_1_name, 4, 20)

        co_2 = CCNxContentObject(co_2_name, None)
        co_3 = CCNxContentObject(co_3_name, None)

        manifest_0.add_manifest_link(manifest_1)
        manifest_0.add_data_link(co_2)
        manifest_0.add_data_link(co_3)

        co_0 = manifest_0.get_content_object()
        wire_format = co_0.wire_format

        truth = [0x01, 0x02, 0x00, 0x9a, 0x00, 0x00, 0x00, 0x08,
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

        truth_array = array.array("B", truth)

        self.assertTrue(wire_format == truth_array, "wrong wire format, expected\n{}\ngot\n{}".format(
            ["0x{:02x}".format(b) for b in truth],
            ["0x{:02x}".format(b) for b in wire_format]))

if __name__ == "__main__":
    unittest.main()
