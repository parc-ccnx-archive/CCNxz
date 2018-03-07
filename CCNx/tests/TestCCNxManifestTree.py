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
import os

import Crypto.PublicKey.RSA as RSA

from CCNx.CCNxManifestTree import *


class TestCCNxManifestTree(unittest.TestCase):
    def setUp(self):
        self.name = "lci:/apple/bananna"
        self.chunk_size = 1500
        self.data = [1] * 384
        self.key = RSA.generate(2048, os.urandom)
        self.mt = CCNxManifestTree(self.name, self.data, self.chunk_size, self.key)

    def test_root_manifest_size(self):
        print dir (self.mt)
        manifest_fanout, data_fanout = self.mt._CCNxManifestTree__root_manifest_size()
        print "root fanout = ({}, {})".format(manifest_fanout, data_fanout)
        self.assertTrue(manifest_fanout > 0, "non-positive manifest_fanout: {}".format(manifest_fanout))
        self.assertTrue(data_fanout > 0, "non-positive data_fanout: {}".format(data_fanout))

    def test_internal_manifest_size(self):
        manifest_fanout, data_fanout = self.mt._CCNxManifestTree__internal_manifest_size(self.chunk_size)
        print "internal fanout = ({}, {})".format(manifest_fanout, data_fanout)
        self.assertTrue(manifest_fanout > 0, "non-positive manifest_fanout: {}".format(manifest_fanout))
        self.assertTrue(data_fanout > 0, "non-positive data_fanout: {}".format(data_fanout))

    def test_calculate_manifest_count(self):
        manifest_count = self.mt._CCNxManifestTree__calculate_manifest_count()
        self.assertTrue(manifest_count == 1, "Expected 1 got {}".format(manifest_count))


class TestCCNxManifestTree_LargeTree(unittest.TestCase):
    """
    This should encode in to 4 manifests.

    The general overhead is 52 bytes per ContentObject.  We have 448 bytes per data object, so
    that's 23 data objects.  The root manifest has data fanout 1 and internal have 12, so that
    takes 3 total.
    """
    def setUp(self):
        self.name = "lci:/apple/bananna"
        self.chunk_size = 700
        self.data = [2] * 10000
        self.key = RSA.generate(2048, os.urandom)
        self.mt = CCNxManifestTree(self.name, self.data, self.chunk_size, self.key)

    def test_calculate_manifest_count_many(self):
        manifest_count = self.mt._CCNxManifestTree__calculate_manifest_count()
        self.assertTrue(manifest_count == 3, "Expected 3 got {}".format(manifest_count))

    @staticmethod
    def _preorder_walk(manifest_node, visit_list):
        name = manifest_node.name
        letter = chr(name.get_segment(0).value[0])
        visit_list.append(letter)
        for child in manifest_node.manifest_links():
            TestCCNxManifestTree_LargeTree._preorder_walk(child, visit_list)

    def test_recursive_tree(self):
        """
        Test in a tree where the root has fanout 2 and internal nodes have fanout 3.
        Less the root, there are 17 manifests.  That means there are 9 per branch.
        A 3-ary tree holds 9 nodes in height 2 tree.  So the left branch will have
        13 entries and the right branch will have 4 entries

                                       A
                                       |
                        |---------------------|
                        B                     O
                        |                     |
            |-----------|-----------|     |---|---|
            C           G           K     P   Q   R
            |           |           |
        |---|---|   |---|---|   |---|---|
        D   E   F   H   I   J   L   M   N

        :return:
        """
        manifest_list = []
        truth = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R']
        for letter in truth:
            name = CCNxNameFactory.from_uri('lci:/' + letter)
            if letter == "A":
                fanout = 2
            else:
                fanout = 3
            manifest = CCNxManifest(name, fanout, 10)
            manifest_list.append(manifest)

        CCNxManifestTree._CCNxManifestTree__recursive_pre_order(manifest_list, 0, 3)

        visit_list = []
        self._preorder_walk(manifest_list[0], visit_list)
        self.assertTrue(visit_list == truth, "Expected {} got {}".format(truth, visit_list))

    def test_create_tree(self):
        tree = self.mt.create_tree()
        print tree


if __name__ == "__main__":
    unittest.main()
