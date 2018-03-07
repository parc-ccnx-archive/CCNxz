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

from CCNx.CCNxName import *
from CCNx.CCNxContentObject import *


class TestCCNxContentObject(unittest.TestCase):
    def test_object_name_none_none(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        co = CCNxContentObject(name, None)

        self.assertEqual(name, co.name, "Names do not match")

        truth = [0x01, 0x02, 0x00, 0x20, 0x00, 0x00, 0x00, 0x08,
                 # Content Object
                 0x00, 0x02, 0x00, 0x14,
                 # name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65]

        truth_array = array.array("B", truth)
        wire_format = co.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)

    def test_object_name_expiry_none(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        expiry_time = 6321
        co = CCNxContentObject(name, expiry_time)

        self.assertEqual(name, co.name, "Names do not match")

        truth = [0x01, 0x02, 0x00, 0x26, 0x00, 0x00, 0x00, 0x08,
                 # Content Object
                 0x00, 0x02, 0x00, 0x1a,
                 # name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65,
                 # Expiry Time
                 0x00, 0x06, 0x00, 0x02,
                 0x18, 0xB1]

        truth_array = array.array("B", truth)
        wire_format = co.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)

    def test_object_name_expiry_extras(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        expiry_time = 6321
        payload_tlv = CCNxTlv(T_PAYLOAD, 3, [1, 2, 3])

        co = CCNxContentObject(name, expiry_time, None, payload_tlv)

        self.assertEqual(name, co.name, "Names do not match")

        truth = [0x01, 0x02, 0x00, 0x2d, 0x00, 0x00, 0x00, 0x08,
                 # Content Object
                 0x00, 0x02, 0x00, 0x21,
                 # name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65,
                 # Expiry Time
                 0x00, 0x06, 0x00, 0x02,
                 0x18, 0xB1,
                 # Payload TLV
                 0x00, 0x01, 0x00, 0x03,
                 0x01, 0x02, 0x03]

        truth_array = array.array("B", truth)
        wire_format = co.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)

    def test_container_tlvs_and_none_tlvs(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        expiry_time = 6321
        valalg_tlv = CCNxTlv(T_VALALG, 8, None)
        keyid_tlv = CCNxTlv(T_KEYID, 4, [1, 2, 3, 4])
        payload_tlv = CCNxTlv(T_PAYLOAD, 3, [1, 2, 3])

        co = CCNxContentObject(name, expiry_time, None, payload_tlv, valalg_tlv, keyid_tlv)

        self.assertEqual(name, co.name, "Names do not match")

        truth = [0x01, 0x02, 0x00, 0x39, 0x00, 0x00, 0x00, 0x08,
                 # Content Object
                 0x00, 0x02, 0x00, 0x2d,
                 # Name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65,
                 # Expiry Time
                 0x00, 0x06, 0x00, 0x02, 0x18, 0xb1,
                 # Payload TLV
                 0x00, 0x01, 0x00, 0x03, 0x01, 0x02, 0x03,
                 # ValAlg
                 0x00, 0x03, 0x00, 0x08,
                 # KeyId
                 0x00, 0x09, 0x00, 0x04,
                 0x01, 0x02, 0x03, 0x04]

        truth_array = array.array("B", truth)
        wire_format = co.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)



if __name__ == '__main__':
    unittest.main()
