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


import unittest
from CCNx.CCNxName import *
from CCNx.CCNxInterest import *
from CCNx.CCNxContentObject import *
from CCNx.CCNxManifestTree import *

from CCNxz.CCNxzGenServer import *
from CCNxz.CCNxzGenClient import *
from Crypto.PublicKey import RSA

_pem = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDk680vyxYFEUfuNq8XBPXgvu2NbEn42wK/6V6LPLuiSdINXjRj
V3rA6QcNWAvNLxtOw68zt+Wk2OQIzFTtyhfx1gmXqM+pouY3nJzEh5J70X0ZkULz
9qVswu/Sz+e5a/4S7wWf727yv1eBPd83TjE4a/gOh28971OpVpOufXd9qwIDAQAB
AoGBAODYQlb5EA22JYJyL5Naie5PWaAYhqdo5dB9dSEpa9pAy5HZv3b7i1RDDWwr
2JuV8ypvxXv02hgJ+CA0Ig7U+qHv++c4jdKUY//3hhp8PQ8Bvnb1qnXKVXWHGESU
F/ZSt6K044qQ/wT1OI/53bE868sQCo/54vjlr1ms1yW+z/cBAkEA+/4PHdTXH3Ho
HXyhNq9LOzfOql+39BeqmewRp+/y7UgvN/xGRS8jvJWA0aRUllmHrTb3/u08F5NV
GXee8nhxawJBAOiPz9MwrKjT9MZkq3KVHb2hFkskcY+rPpk9GrFrSCyuT8ayblHJ
TUu0vM/a+srhXtnrMEVI4NrYK3c13oGw9MECQQDLfLtEQa197QOdXBjrCd7ccRJo
LmdjqwDOzvzq+i7XQaUvtn4gPBLFpIyjvem4h4+yZmMY7wXJm+XqbNhjwLMFAkEA
xqiqoD4xD5rXum2eYyfsGuOzNocwFsjylVY0KiB5q+lPLm2XfXfW9ney3l+x4oK4
UrDsMBM8ONV188RpiSHPQQJAEbadj+3K5aJ5p9GR32VBey4MV7IelzJF+g/FfbNF
un4lm0vl6Bqi2uBcdWX7IZtdotaeMPl8mXUx4+WRxM6rfA==
-----END RSA PRIVATE KEY-----"""
_key = RSA.importKey(_pem)

__author__ = 'mmosko'


class TestManifestProcessor(unittest.TestCase):
    def setUp(self):
        self.user_write_queue = Queue.Queue()
        self.net_write_queue = Queue.Queue()
        self.net_to_parser_queue = Queue.Queue()
        self.parser_to_flow_controller_queue = Queue.Queue()
        self.fc_to_processor_queue = Queue.Queue()
        self.processor_to_fc_queue = Queue.Queue()

        self.uri = "lci:/apple/pie/crust"
        self.prefix = CCNxNameFactory.from_uri(self.uri)
        self.server_port = 9696
        self.client_port = 9697
        self.reader = SocketReaderThread(port=self.client_port, write_queue=self.net_to_parser_queue, timeout=0.2)
        self.parser = ParserThread(self.net_to_parser_queue, self.parser_to_flow_controller_queue)
        self.fc = FlowControllerThread(user_read_queue=self.processor_to_fc_queue,
                                       user_write_queue=self.fc_to_processor_queue,
                                       net_read_queue=self.parser_to_flow_controller_queue,
                                       net_write_queue=self.net_write_queue,
                                       clock=time.clock)

        signer = CCNxSignature(_key)
        self.processor = ManifestProcessorThread(name=self.prefix,
                                                 keyid=signer.keyid_array,
                                                 user_write_queue=self.user_write_queue,
                                                 transport_read_queue=self.fc_to_processor_queue,
                                                 transport_write_queue=self.processor_to_fc_queue)

        self.writer = CCNxzGenClient.SocketWriterThread(read_queue=self.net_write_queue, socket=self.reader.socket,
                                                        peer=("127.0.0.1", self.server_port))
        self.threads = [self.writer, self.reader, self.parser, self.fc, self.processor]

        for t in self.threads:
            t.start()

    def tearDown(self):
        for t in self.threads:
            t.stop()

        for t in self.threads:
            t.join(timeout=0.2)

        self.reader.close()

    @staticmethod
    def _add_manifest_tree(objects_by_name, objects_by_hash, manifest):
        co = manifest.get_content_object()
        objects_by_name[co.name] = co
        objects_by_hash[co.hash] = co

        for child in manifest.data_links():
            objects_by_name[child.name] = child
            objects_by_hash[child.hash().tostring()] = child

        for child in manifest.manifest_links():
            TestManifestProcessor._add_manifest_tree(objects_by_name, objects_by_hash, child)

    def test_with_server(self):
        """
        Instantiate a CCNxzGenServer with 10 items in it and have the flow controller
        pull them all out.
        """
        interests = []
        objects_by_name = {}
        objects_by_hash = {}

        data_length = 10000
        chunk_size = 1500
        data=array.array("B", [1] * data_length)

        manifest_tree = CCNxManifestTree(uri=self.uri, data=data, chunk_size=chunk_size, key=_key)
        tree_root = manifest_tree.create_tree()

        TestManifestProcessor._add_manifest_tree(objects_by_name, objects_by_hash, tree_root)

        server_port = 9696
        gen_server = CCNxzGenServer(port=server_port, key=_key, objects_by_name=objects_by_name,
                                    objects_by_hash=objects_by_hash)
        gen_server.start()

        try:
            read_length = 0
            while read_length < data_length:
                try:
                    message = self.user_write_queue.get(block=True, timeout=1)
                    read_length += len(message.payload)
                    print "readl len={} total={}", len(message.payload), read_length
                    print "read ", message

                    if len(message.wire_format) > chunk_size:
                        raise OverflowError("Packet length {} is longer than chunk size {}\n{}".format(
                            len(message.wire_format), chunk_size, message.wire_format))

                except Queue.Empty:
                    print "Timed out reading from manifest processor"
                    break

        finally:
            gen_server.stop()
            gen_server.join()

