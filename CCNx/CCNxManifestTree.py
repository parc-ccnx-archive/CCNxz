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

"""
Make a manifest tree of the data.  Each ContentObject (manifest or data) will
have a chunked name under 'name'.  For example, if name='/foo/bar' then each
Manifest and data object will have a name like '/foo/bar/chunk=N'.

No object will exceed 'chunk_size'.

The root manifest will have the public key, key id, and signature.  Everything
else will be hash links.

The signature and public key come from the user-provided 'key', which should be
from the python Crypto package.
"""

import time
import math
from collections import deque

from CCNx.CCNxManifest import *
from CCNx.CCNxName import *


# __author__ = 'mmosko'


class ManifestStructure(object):
    def __init__(self, manifest_fanout, data_fanout):
        self.__manifest_fanout = manifest_fanout
        self.__data_fanout = data_fanout

    @property
    def manifest_fanout(self):
        return self.__manifest_fanout

    @property
    def data_fanout(self):
        return self.__data_fanout


class CCNxManifestTree(object):
    """
    Creates a manifest tree representing underlying data (a byte string).

    Example:
        parc_key = RSA.import(pem_string)
        fh = open("video.mp4, "rb")
        data = fh.read()
        manifest_tree = CCNxManifestTree("lci:/parc/video", data, 1500, parc_key)
        root_manifest = manifest_tree.create_tree()
    """

    def __init__(self, uri, data, chunk_size, key):
        """
        The manifests will have names like lci:/uri/CHUNK=[0,k-1] and the data
        will have names like lci:/uri/CHUNK[k, n-1], where there are k manifest nodes
        and (n - k) data nodes.

        :param uri: an LCI URI
        :param data: The original data to chunk and put in a manifest
        :param chunk_size: The size not to exceed for the whole packet
        :param key: The signing key for the root manifest
        :return: A CCNxManifestTree object
        """
        self.__name = CCNxNameFactory.from_uri(uri)
        self.__data = data
        self.__chunk_size = chunk_size
        self.__key = key
        self.__signer = CCNxSignature(self.__key)
        self.__fanount = 4

        # estimate for how many bytes to encode a chunk number
        self.__chunk_len = 3

        # The structure (fanouts) of the root node and internal node
        self.__root_structure = None
        self.__internal_structure = None

    @staticmethod
    def __div_roundup(a, b):
        """
        Calculate the integer ceiling of a / b.

        :param a: number
        :param b: number
        :return: (a/b) + (a%b !=0 : 1 : 0)
        """
        n = a / b
        if a % b > 0:
            n += 1
        return n

    def __internal_manifest_size(self, available_bytes):
        """
        An internal manifest:
            - _chunk_overhead plus
            - 0 bytes for T_MANIFEST (there's already 4 for T_PAYLOAD we won't use)
            - 4 bytes list_of_manifests
            - 4 bytes for T_START_CHUNK plus 3 bytes for number
            - 32 * k bytes of list
            - 4 bytes list_of_data
            - 4 bytes for T_START_CHUNK plus 3 bytes for number
            - 32 * j bytes of list

            Returns the maximum space available for manifest fanout and data fanount
            (i.e. the number of embeddable links)

            :param available_bytes: Number of bytes to encode the manifest
            :return: manifest_fanout, data_fanout
        """
        overhead = self.__chunk_overhead()
        available_bytes -= overhead

        # Manifest List
        available_bytes -= 4
        # StartChunkNumber
        available_bytes -= 7

        hash_size = 32
        min_link_size = hash_size + 4
        if available_bytes < min_link_size:
            raise ValueError("available_bytes {} too small for overhead".format(available_bytes))

        manifest_fanout = 0
        if available_bytes > min_link_size:
            available_bytes -= 4
            max_fanount = int(available_bytes / hash_size)
            manifest_fanout = min(max_fanount, self.__fanount)
            available_bytes -= hash_size * manifest_fanout

        # Data List
        available_bytes -= 4
        # StartChunkNumber
        available_bytes -= 7

        data_fanout = 0
        if available_bytes > min_link_size:
            available_bytes -= 4
            data_fanout = int(available_bytes / hash_size)

        return manifest_fanout, data_fanout

    def __root_manifest_size(self):
        """
        The root manifest has:
            - _chunk_overhead plus
            - _internal_manifest
            - 8 bytes ValidationAlg (RSA)
            - 36 bytes keyid
            - N bytes public key
            - 4 bytes Validation Payload
            - M bytes signature

        :return: manifest_fanout, data_fanout
        """
        # the chunk_overhead will be included in _internal_overhead
        overhead = 8 + 36 + 4
        der = self.__signer.public_key_array
        der_overhead = len(der)
        print "der overhead = ", der_overhead
        sig = self.__signer.sign("a fake hash value")
        sig_overhead = len(sig)
        print "sig overhead = ", sig_overhead
        overhead += der_overhead + sig_overhead
        available_bytes = self.__chunk_size - overhead
        manifest_fanout, data_fanout = self.__internal_manifest_size(available_bytes)
        return manifest_fanout, data_fanout

    def __calculate_manifest_structure(self):
        """
        Sets the internal variables __root_structure and __internal_structure with
        the fanouts for those types of nodes.

        :return: None
        """
        manifest_fanout, data_fanout = self.__root_manifest_size()
        self.__root_structure = ManifestStructure(manifest_fanout, data_fanout)

        manifest_fanout, data_fanout = self.__internal_manifest_size(self.__chunk_size)
        self.__internal_structure = ManifestStructure(manifest_fanout, data_fanout)

    def __chunk_overhead(self):
        """
        Each data object will be:
            - 8 byte fixed header
            - 4 byte T_OBJECT
            - len(encoded name) plus 4 + len(chunk_number)
            - 4 byte T_EXPIRY + 8 byte time
            - 4 byte T_PAYLOAD + payload_bytes

            This may over estimate the number of chunks by a few as we assume
            a fixed chunk encoding size of 3 bytes.  It will be 2 bytes shorter for
            256 chunks and 1 byte shorter for 65536 chunks.

            returns the overhead less the payload_bytes
        """
        # All the fixed overhead
        fh_len = 8
        t_object_len = 4
        expiry_len = 12
        payload_len = 4
        name_len = self.__name.length
        overhead = fh_len + t_object_len + name_len + expiry_len + payload_len
        return overhead

    def __data_size_per_chunk(self):
        overhead = self.__chunk_overhead()

        # first order approximation, which may be off by a byte or two for
        # the chunk length.  We'll assume at most 3 bytes per chunk number.
        data_size_per_chunk = self.__chunk_size - overhead - self.__chunk_len
        return data_size_per_chunk

    def __calculate_data_chunks(self):
        data_size_per_chunk = self.__data_size_per_chunk()
        chunk_count = self.__div_roundup(len(self.__data), data_size_per_chunk)
        if chunk_count >= (1 << (self.__chunk_len * 8)):
            raise ValueError("Need more than 16M chunks, not supported yet")

        return chunk_count

    def __calculate_manifest_count(self):
        """
        Calculates how many manifests it takes to encode all the data chunks.

        :return: number
        """
        chunk_count = self.__calculate_data_chunks()

        self.__calculate_manifest_structure()

        manifest_count = 0
        while chunk_count > 0:
            if manifest_count == 0:
                data_fanout = self.__root_structure.data_fanout
            else:
                data_fanout = self.__internal_structure.data_fanout

            manifest_count += 1
            chunk_count -= data_fanout
        return manifest_count

    def _generate_data_chunk(self, offset, payload_size, chunk_number, expiry_time):
        """
        Creates a CCNxMessage and returns it
        :param offset: byte offset in payload to start at
        :param payload_size: length in payload to include
        :param chunk_number:
        :param expiry_array:
        :return: CCNxMessage
        """
        name = CCNxNameFactory.from_name(self.__name, chunk_number)
        payload_tlv = CCNxTlv(T_PAYLOAD, payload_size, self.__data[offset:offset + payload_size])
        co = CCNxContentObject(name, expiry_time, payload_tlv)
        return co

    def _generate_data(self, chunk_number):
        """

        :param chunk_number:
        :return: A list of CCNxMessage that are all the data chunks
        """
        data_size_per_chunk = self.__data_size_per_chunk()
        offset = 0
        chunks = []

        tomorrow_seconds = 24 * 3600
        expiry_time = int((time.mktime(time.gmtime()) + tomorrow_seconds) * 1000)
        while offset < len(self.__data):
            chunk = self._generate_data_chunk(offset, data_size_per_chunk, chunk_number, expiry_time)
            chunk_number += 1
            offset += data_size_per_chunk
            chunks.append(chunk)
        return chunks

    def __generate_manifests(self, data_objects):
        """
        Create the manifests that go with the data objects.
        :param data_objects: An in-order list of data objects
        :return: An ordered list of manifests, the root is item 0.
        """
        manifest = None
        data_index = 0
        manifest_chunk_number = 0
        remaining_data_links = 0
        manifest_objects = []

        while data_index < len(data_objects):
            if manifest is None:
                if manifest_chunk_number == 0:
                    manifest_fanout = self.__root_structure.manifest_fanout
                    remaining_data_links = self.__root_structure.data_fanout
                else:
                    manifest_fanout = self.__internal_structure.manifest_fanout
                    remaining_data_links = self.__internal_structure.data_fanout

                manifest_name = CCNxNameFactory.from_name(self.__name, manifest_chunk_number)
                manifest_chunk_number += 1
                manifest = CCNxManifest(manifest_name, manifest_fanout, remaining_data_links)
                manifest_objects.append(manifest)

            if remaining_data_links > 0:
                manifest.add_data_link(data_objects[data_index])
                data_index += 1
                remaining_data_links -= 1

            if remaining_data_links == 0:
                manifest = None

        return manifest_objects

    def __link_manifests(self, manifest_objects):
        """
        Link the manifests together in a tree.  They are listed in 'manifest objects' in
        their traversal order.

        The defined traversal order for the tree is DFS pre-order traversal.  So, we need
        to organize the list in to that tree.

        We have self.__root_structure.manifest_fanout branches, where each branch has
        self.__internal_structure.manifest_fanout.  So, find the largest tree height from that
        and start filling in the tree.  The end of the DFS traversal may not be a complete tree.

        The height of a perfect k-ary tree with n nodes is:
            h = ceil( log_k(k-1) + log_k(n) - 1 )

        :return:
        """
        # number of manifests excluding root
        n = len(manifest_objects) - 1

        manifest_nodes_per_branch = self.__div_roundup(n, self.__root_structure.manifest_fanout)
        if manifest_nodes_per_branch > 0:
            k = self.__internal_structure.manifest_fanout
            branch_height = int(math.ceil(math.log(k-1, k) + math.log(manifest_nodes_per_branch, k) - 1))
        else:
            branch_height = 0

        # now make a DFS pre-order walk to branch_height and fill in nodes
        self.__recursive_pre_order(manifest_objects, 0, branch_height)

    @staticmethod
    def __recursive_pre_order(manifest_objects, manifest_start_index, remaining_height):
        manifest = manifest_objects[manifest_start_index]
        manifest_start_index += 1
        if remaining_height > 0:
            while manifest.remaining_manifest_fanout() > 0 and manifest_start_index < len(manifest_objects):
                child = manifest_objects[manifest_start_index]
                manifest.add_manifest_link(child)
                manifest_start_index = CCNxManifestTree.__recursive_pre_order(manifest_objects, manifest_start_index,
                                                                              remaining_height - 1)
        return manifest_start_index

    @staticmethod
    def __bfs_rename(manifest_objects):
        """Rename the manifest objects in BFS order so the chunk numbers are sequential in each manifest"""
        chunk_number = 0
        queue = deque()
        queue.append(manifest_objects[0])
        while len(queue) > 0:
            node = queue.popleft()
            node.name.chunk_number = chunk_number
            chunk_number += 1
            for child in node.manifest_links():
                queue.append(child)

    def create_tree(self):
        """
        Creates a list of data objects.  Creates a list of manifest objects that point
        to the data objects in order.  Links the manifest objects together is proper order.
        Returns the root manifest, which is signed.

        :return: The root CCNxManifest object
        """
        manifest_count = self.__calculate_manifest_count()

        # we start naming data object with chunk = manifest_count and the manifests
        # are in range(0, manifest_count).
        data_objects = self._generate_data(manifest_count)

        # Now generate the manifest objects
        manifest_objects = self.__generate_manifests(data_objects)

        if manifest_count != len(manifest_objects):
            raise RuntimeError("manifest_count = {} but len(manifest_objects) = {}".format(
                manifest_count, len(manifest_objects)))

        # Now link the manifests together
        self.__link_manifests(manifest_objects)

        # We want the manifests named in BFS order so all the chunk numbers are contiguous
        self.__bfs_rename(manifest_objects)

        # And sign the root
        manifest_objects[0].sign(self.__key)

        return manifest_objects[0]