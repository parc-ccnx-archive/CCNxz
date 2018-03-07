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

from CCNx.CCNxName import *


class TestCCNxManifestTree(unittest.TestCase):
    def test_encode_name(self):
        uri = "lci:/apple/bananna"
        name = CCNxNameFactory.from_uri(uri)
        truth = "[TLV(0, 20, None), TLV(1, 5, array('B', [97, 112, 112, 108, 101])), " + \
                "TLV(1, 7, array('B', [98, 97, 110, 97, 110, 110, 97]))]"
        self.assertTrue(truth == name.__str__(), "Wrong value\ntruth = {}\ntest =  {}".format(truth, name))

    def test_name_plus_chunk(self):
        uri = "lci:/apple"
        chunk = 260
        prefix = CCNxNameFactory.from_uri(uri)
        name = CCNxNameFactory.from_name(prefix, chunk)
        truth = "[TLV(0, 15, None), TLV(1, 5, array('B', [97, 112, 112, 108, 101])), TLV(10, 2, array('B', [1, 4]))]"
        self.assertTrue(truth == name.__str__(), "Wrong value\ntruth = {}\ntest =  {}".format(truth, name))

if __name__ == "__main__":
    unittest.main()
