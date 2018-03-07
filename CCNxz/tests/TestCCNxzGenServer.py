
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
import socket

from Crypto.PublicKey import RSA

from CCNxz.CCNxzGenServer import *
from CCNxz.Packets import *
from CCNx.CCNxName import *
from CCNx.CCNxContentObject import *

__author__ = 'mmosko'

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


class TestCCNxzGenServerSocketReaderThread(unittest.TestCase):
    def test_socket_reader(self):
        pass


class TestCCNxzGenServerParserThread(unittest.TestCase):
    def setUp(self):
        print "Runing test ", self
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()
        self.thread = ParserThread(self.input_queue, self.output_queue)
        self.thread.start()

    def tearDown(self):
        self.thread.stop()
        while self.thread.is_alive():
            self.thread.join(timeout=0.1)

    def test_parser_thread(self):
        entry = QueueEntry(client=None, data=list(Packets.interest), socket=None, message=None)
        self.input_queue.put(entry)
        test = self.output_queue.get(block=True, timeout=1)
        self.assertTrue(test.message is not None, "Got output from parser, but the message property is None")
        self.assertTrue(isinstance(test.message, CCNxMessage), "Not CCNxMessage derived")


class TestCCNxzGenServerLookupThread(unittest.TestCase):
    def setUp(self):
        self.key = _key
        print "Runing test ", self
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()

        # Apple is unsigned, only has name
        name_apple = CCNxNameFactory.from_uri("lci:/apple")
        self.co_apple = CCNxContentObject(name_apple, None)
        self.co_apple.generate_wireformat()

        # Blueberry is signed, so has a KeyId in it
        name_blueberry = CCNxNameFactory.from_uri("lci:/blue/berry")
        self.co_blueberry = CCNxContentObject(name_blueberry, None)
        self.co_blueberry.sign(self.key)

        self.objects_by_name = {}
        self.objects_by_hash = {}

        self.objects_by_name[self.co_apple.name] = self.co_apple
        self.objects_by_name[self.co_blueberry.name] = self.co_blueberry
        self.objects_by_hash[self.co_blueberry.hash().tostring()] = self.co_blueberry

        signer = CCNxSignature(self.key)
        self.__keyid_array = signer.keyid_array

        self.thread = LookupThread(self.input_queue, self.output_queue, self.__keyid_array, self.objects_by_name,
                                   self.objects_by_hash)
        self.thread.start()

    def tearDown(self):
        self.thread.stop()
        while self.thread.is_alive():
            self.thread.join(timeout=0.1)

    def test_not_interest(self):
        co = CCNxContentObject(CCNxNameFactory.from_uri("lci:/foo/bar"), None)
        entry = QueueEntry(client=None, data=None, socket=None, message=co)
        self.input_queue.put(entry)
        try:
            self.output_queue.get(block=True, timeout=0.25)
            empty = False
        except Queue.Empty:
            empty = True
        self.assertTrue(empty, "Should have failed for non-interest")

    def test_interest_bad_keyid(self):
        """Interest with keyid resriction that does not match our key"""
        name = CCNxNameFactory.from_uri("lci:/blue/berry")
        keyid = [1] * 32
        interest = CCNxInterest(name=name, keyid_restr=keyid)
        entry = QueueEntry(client=None, data=None, socket=None, message=interest)
        self.input_queue.put(entry)
        try:
            self.output_queue.get(block=True, timeout=0.25)
            empty = False
        except Queue.Empty:
            empty = True
        self.assertTrue(empty, "Timed out trying to match interest")

    def test_interest_good_keyid(self):
        """Interest with keyid resriction that does not match our key"""
        name = CCNxNameFactory.from_uri("lci:/blue/berry")
        keyid = self.__keyid_array
        interest = CCNxInterest(name=name, keyid_restr=keyid)
        entry = QueueEntry(client=None, data=None, socket=None, message=interest)
        self.input_queue.put(entry)
        try:
            test = self.output_queue.get(block=True, timeout=0.25)
            empty = False
        except Queue.Empty:
            test = None
            empty = True
        self.assertTrue(not empty, "Timed out trying to match interest")
        self.assertTrue(type(test) == tuple, "Should have gotten a tuple")

    def test_interest_name_match(self):
        name = CCNxNameFactory.from_uri("lci:/apple")
        interest = CCNxInterest(name)
        entry = QueueEntry(client=None, data=None, socket=None, message=interest)
        self.input_queue.put(entry)
        try:
            test = self.output_queue.get(block=True, timeout=.25)
            empty = False
        except Queue.Empty:
            test = None
            empty = True
        self.assertTrue(not empty, "Timed out trying to match interest")
        self.assertTrue(type(test) == tuple, "Should have gotten a tuple")

    def test_interest_hash_match(self):
        name = CCNxNameFactory.from_uri("lci:/blue/berry")
        hash_restriction = self.co_blueberry.hash()
        interest = CCNxInterest(name=name, keyid_restr=None, hash_restr=hash_restriction)
        entry = QueueEntry(client=None, data=None, socket=None, message=interest)
        self.input_queue.put(entry)
        try:
            test = self.output_queue.get(block=True, timeout=.25)
            empty = False
        except Queue.Empty:
            test = None
            empty = True
        self.assertTrue(not empty, "Timed out trying to match interest")
        self.assertTrue(type(test) == tuple, "Should have gotten a tuple")


class TestCCNxGenServerSocketWriterThread(unittest.TestCase):
    def setUp(self):
        print "Runing test ", self

    def test_write(self):
        pass


class TestCCnxzGenServer(unittest.TestCase):
    def setUp(self):
        self.key = _key
        print "Runing test ", self
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()

        # Apple is unsigned, only has name
        name_apple = CCNxNameFactory.from_uri("lci:/apple")
        self.co_apple = CCNxContentObject(name_apple, None)
        self.co_apple.generate_wireformat()

        # Blueberry is signed, so has a KeyId in it
        name_blueberry = CCNxNameFactory.from_uri("lci:/blue/berry")
        self.co_blueberry = CCNxContentObject(name_blueberry, None)
        self.co_blueberry.sign(self.key)

        self.objects_by_name = {}
        self.objects_by_hash = {}

        self.objects_by_name[self.co_apple.name] = self.co_apple
        self.objects_by_name[self.co_blueberry.name] = self.co_blueberry
        self.objects_by_hash[self.co_blueberry.hash().tostring()] = self.co_blueberry

    def test_server(self):
        """
        Send an interest to the SocketReaderThread, let it go through the prodessing pipeline, and
        read the response from SocketWriterThread via our udp client port.
        :return:
        """
        port = 9696
        gen_server = CCNxzGenServer(port=port, key=_key, objects_by_name=self.objects_by_name,
                                    objects_by_hash=self.objects_by_hash)
        gen_server.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            client.settimeout(0.25)
            interest = CCNxInterest(self.co_apple.name)
            client.sendto(interest.wire_format, ("127.0.0.1", port))
            data = client.recv(4096)
            data_array = array.array("B", data)
            self.assertEqual(self.co_apple.wire_format, data_array, "Did not receive expected data")
        finally:
            client.close()
            gen_server.stop()
            try:
                gen_server.join()
            except KeyboardInterrupt:
                print "Got keyboard interrupt"


if __name__ == '__main__':
    unittest.main()
