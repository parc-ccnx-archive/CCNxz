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
from CCNx.CCNxInterest import *


class TestCCNxInterest(unittest.TestCase):
    def test_interest_name_none_none(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        interest = CCNxInterest(name=name, keyid_restr=None, hash_restr=None)

        self.assertEqual(name, interest.name, "Names do not match")
        self.assertIsNone(interest.keyid_restr)
        self.assertIsNone(interest.hash_restr)

        truth = [0x01, 0x01, 0x00, 0x20, 0x00, 0x00, 0x00, 0x08,
                 # Interest
                 0x00, 0x01, 0x00, 0x14,
                 # name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65]

        truth_array = array.array("B", truth)
        wire_format = interest.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)

    def test_interest_name_keyid_none(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        keyid = array.array("B", [1, 2, 3, 4, 5])
        interest = CCNxInterest(name=name, keyid_restr=keyid, hash_restr=None)

        self.assertEqual(name, interest.name, "Names do not match")
        self.assertEqual(keyid, interest.keyid_restr, "KeyId Restrictions do not match")
        self.assertIsNone(interest.hash_restr)

        truth = [0x01, 0x01, 0x00, 0x29, 0x00, 0x00, 0x00, 0x08,
                 # Interest
                 0x00, 0x01, 0x00, 0x1d,
                 # name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65,
                 # KeyId Restriction
                 0x00, 0x02, 0x00, 0x05,
                 0x01, 0x02, 0x03, 0x04, 0x05]

        truth_array = array.array("B", truth)
        wire_format = interest.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)

    def test_interest_name_keyid_hash(self):
        name = CCNxNameFactory.from_uri("lci:/apple/pie")
        keyid = array.array("B", [1, 2, 3, 4, 5])
        hash_restr = array.array("B", [6, 7, 8, 9, 10, 11])
        interest = CCNxInterest(name=name, keyid_restr=keyid, hash_restr=hash_restr)

        self.assertEqual(name, interest.name, "Names do not match")
        self.assertEqual(keyid, interest.keyid_restr, "KeyId Restrictions do not match")
        self.assertEqual(hash_restr, interest.hash_restr, "Hash Restrictions do not match")

        truth = [0x01, 0x01, 0x00, 0x33, 0x00, 0x00, 0x00, 0x08,
                 # Interest
                 0x00, 0x01, 0x00, 0x27,
                 # name
                 0x00, 0x00, 0x00, 0x10,
                 0x00, 0x01, 0x00, 0x05, 0x61, 0x70, 0x70, 0x6c, 0x65,
                 0x00, 0x01, 0x00, 0x03, 0x70, 0x69, 0x65,
                 # KeyId Restriction
                 0x00, 0x02, 0x00, 0x05,
                 0x01, 0x02, 0x03, 0x04, 0x05,
                 # Hash Restriction
                 0x00, 0x03, 0x00, 0x06,
                 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b]

        truth_array = array.array("B", truth)
        wire_format = interest.wire_format
        # print ["0x{:02x}".format(b) for b in wire_format]
        self.assertEqual(truth_array, wire_format)


if __name__ == '__main__':
    unittest.main()
