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

from CCNxz.CCNxzGenServer import *
from CCNxz.CCNxzGenClient import *

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


class TestFlowControllerStaticMethods(unittest.TestCase):
    def test_keyid_ok_true_no_keyid(self):
        name = CCNxNameFactory.from_uri("lci:/apple/berry")
        interest = CCNxInterest(name, None, None)
        tx_entry = FlowControllerThread.TxQueueEntry(interest, 0, 0)

        co = CCNxContentObject(name, None)
        co.sign(_key)

        ok = FlowControllerThread._FlowControllerThread__keyid_ok(tx_entry, co)
        self.assertTrue(ok, "Interest without keyid restriction should have matched content object")

    def test_keyid_ok_true_with_keyid(self):
        name = CCNxNameFactory.from_uri("lci:/apple/berry")
        co = CCNxContentObject(name, None)
        co.sign(_key)

        interest = CCNxInterest(name, co.keyid, None)
        tx_entry = FlowControllerThread.TxQueueEntry(interest, 0, 0)

        ok = FlowControllerThread._FlowControllerThread__keyid_ok(tx_entry, co)
        self.assertTrue(ok, "Interest with matching keyid restriction should have matched content object")

    def test_keyid_ok_false_with_bad_keyid(self):
        name = CCNxNameFactory.from_uri("lci:/apple/berry")
        co = CCNxContentObject(name, None)
        co.sign(_key)

        interest = CCNxInterest(name, [1] * 32, None)
        tx_entry = FlowControllerThread.TxQueueEntry(interest, 0, 0)

        ok = FlowControllerThread._FlowControllerThread__keyid_ok(tx_entry, co)
        self.assertFalse(ok, "Interest with non-matching keyid restriction should not match content object")

    def test_hash_ok_matching_hash(self):
        name = CCNxNameFactory.from_uri("lci:/apple/berry")
        co = CCNxContentObject(name, None)
        co.sign(_key)

        interest = CCNxInterest(name, None, co.hash())
        tx_entry = FlowControllerThread.TxQueueEntry(interest, 0, 0)

        ok = FlowControllerThread._FlowControllerThread__hash_ok(tx_entry, co)
        self.assertTrue(ok, "Interest with matching hash restriction should have matched content object")

    def test_hash_ok_bad_hash(self):
        name = CCNxNameFactory.from_uri("lci:/apple/berry")
        co = CCNxContentObject(name, None)
        co.sign(_key)

        interest = CCNxInterest(name, None, [1] * 32)
        tx_entry = FlowControllerThread.TxQueueEntry(interest, 0, 0)

        ok = FlowControllerThread._FlowControllerThread__hash_ok(tx_entry, co)
        self.assertFalse(ok, "Interest with bad hash restriction should not match content object")


class TestFlowControllerTxQueue(unittest.TestCase):
    def clock(self):
        t = self.time
        return t

    def setUp(self):
        self.user_read_queue = Queue.Queue()
        self.user_write_queue = Queue.Queue()
        self.net_read_queue = Queue.Queue()
        self.net_write_queue = Queue.Queue()
        self.time = 100

        self.fc = FlowControllerThread(user_read_queue=self.user_read_queue,
                                       user_write_queue=self.user_write_queue,
                                       net_read_queue=self.net_read_queue,
                                       net_write_queue=self.net_write_queue,
                                       clock=self.clock)

    def test_expire_tx_queue(self):
        """
        Put 3 elements on tx queue: expired, not-expired, expired
        :return:
        """
        interest_a = CCNxInterest(CCNxNameFactory.from_uri("lci:/apple"))
        interest_b = CCNxInterest(CCNxNameFactory.from_uri("lci:/berry"))
        interest_c = CCNxInterest(CCNxNameFactory.from_uri("lci:/cherry"))

        tx_entry_a = FlowControllerThread.TxQueueEntry(interest_a, self.time - 20, self.time - 30)
        tx_entry_b = FlowControllerThread.TxQueueEntry(interest_b, self.time + 10, self.time)
        tx_entry_c = FlowControllerThread.TxQueueEntry(interest_c, self.time - 10, self.time - 15)

        self.fc._FlowControllerThread__tx_queue.append(tx_entry_a)
        self.fc._FlowControllerThread__tx_queue.append(tx_entry_b)
        self.fc._FlowControllerThread__tx_queue.append(tx_entry_c)

        self.fc._FlowControllerThread__expire_tx_queue()

        # Should have moved interest_a to the rtx queue
        tx_queue_len = len(self.fc._FlowControllerThread__tx_queue)
        self.assertEqual(tx_queue_len, 2,
                         "Wrong tx queue length expected {} got {}".format(2, tx_queue_len))

        rtx_queue_len = len(self.fc._FlowControllerThread__rtx_queue)
        self.assertEqual(rtx_queue_len, 1,
                         "Wrong rtx queue length expected {} got {}".format(1, rtx_queue_len))

    def test_append_tx_queue(self):
        """
        Puts an element on the tx_queue with an expiry and send time.
        :return:
        """
        interest_a = CCNxInterest(CCNxNameFactory.from_uri("lci:/apple"))
        self.fc._FlowControllerThread__append_tx_queue(interest_a)
        tx_queue_len = len(self.fc._FlowControllerThread__tx_queue)
        self.assertEqual(tx_queue_len, 1,
                         "Wrong tx queue length expected {} got {}".format(1, tx_queue_len))
        tx_entry = self.fc._FlowControllerThread__tx_queue.popleft()
        self.assertTrue(tx_entry.data == interest_a, "Wrong message")
        self.assertTrue(tx_entry.expiry_time > self.time, "Bad expiry time, should be in the future")
        self.assertTrue(tx_entry.send_time == self.time, "Bad send time, should be the current time")

    def test_enqueue_tx_new_only(self):
        """Only the user_read_queue has items, no rtx"""

        # make the input queue slightly bigger than the tx queue size
        extra = 2
        for i in range(0, self.fc.current_window_size + extra):
            interest = CCNxInterest(CCNxNameFactory.from_uri("lci:/apple/" + str(i)))
            self.user_read_queue.put(interest)

        self.fc._FlowControllerThread__enqueue_tx()

        self.assertEqual(self.user_read_queue.qsize(), extra,
                         "Did not leave {} entries in user_read_queue".format(extra))
        self.assertEqual(self.fc.tx_queue_length, self.fc.current_window_size,
                         "Wrong tx_queue length expected {} got {}".format(self.fc.current_window_size,
                                                                           self.fc.tx_queue_length))
        self.assertEqual(self.net_write_queue.qsize(), self.fc.current_window_size,
                         "Wrong net_write_queue length expected {} got {}".format(self.fc.current_window_size,
                                                                                  self.net_write_queue.qsize()))

    def test_enqueue_tx_rtx_only(self):
        """Only the rtx queue has items, no user_read_queue"""
        extra = 2
        for i in range(0, self.fc.current_window_size + extra):
            interest = CCNxInterest(CCNxNameFactory.from_uri("lci:/apple/" + str(i)))
            self.fc._FlowControllerThread__rtx_queue.append(interest)

        self.fc._FlowControllerThread__enqueue_tx()

        self.assertEqual(len(self.fc._FlowControllerThread__rtx_queue), extra,
                         "Did not leave {} entries in rtx queue".format(extra))
        self.assertEqual(self.fc.tx_queue_length, self.fc.current_window_size,
                         "Wrong tx_queue length expected {} got {}".format(self.fc.current_window_size,
                                                                           self.fc.tx_queue_length))
        self.assertEqual(self.net_write_queue.qsize(), self.fc.current_window_size,
                         "Wrong net_write_queue length expected {} got {}".format(self.fc.current_window_size,
                                                                                  self.net_write_queue.qsize()))

    def test_enqueue_tx_new_and_rtx(self):
        """Only the rtx queue has items, no user_read_queue"""
        extra = 2
        for i in range(0, self.fc.current_window_size + extra):
            # make the TX queue larger than window
            interest = CCNxInterest(CCNxNameFactory.from_uri("lci:/tx/" + str(i)))
            self.user_read_queue.put(interest)

        for i in range(0, self.fc.current_window_size/2):
            # make the RTX queue 1/2 the size of window
            interest = CCNxInterest(CCNxNameFactory.from_uri("lci:/rtx/" + str(i)))
            self.fc._FlowControllerThread__rtx_queue.append(interest)

        self.fc._FlowControllerThread__enqueue_tx()

        # should have consumed everything from the RTX queue
        self.assertEqual(len(self.fc._FlowControllerThread__rtx_queue), 0,
                         "Did not leave {} entries in rtx queue".format(0))

        # and filled the TX queue
        self.assertEqual(self.fc.tx_queue_length, self.fc.current_window_size,
                         "Wrong tx_queue length expected {} got {}".format(self.fc.current_window_size,
                                                                           self.fc.tx_queue_length))

        # and them all in the network write queue too
        self.assertEqual(self.net_write_queue.qsize(), self.fc.current_window_size,
                         "Wrong net_write_queue length expected {} got {}".format(self.fc.current_window_size,
                                                                                  self.net_write_queue.qsize()))


class TestFlowControllerWithServer(unittest.TestCase):
    def setUp(self):
        self.user_read_queue = Queue.Queue()
        self.user_write_queue = Queue.Queue()
        self.net_write_queue = Queue.Queue()
        self.net_to_parser_queue = Queue.Queue()
        self.parser_to_flow_controller_queue = Queue.Queue()

        self.server_port = 9696
        self.client_port = 9697
        self.reader = SocketReaderThread(port=self.client_port, write_queue=self.net_to_parser_queue, timeout=0.2)
        self.parser = ParserThread(self.net_to_parser_queue, self.parser_to_flow_controller_queue)
        self.fc = FlowControllerThread(user_read_queue=self.user_read_queue,
                                       user_write_queue=self.user_write_queue,
                                       net_read_queue=self.parser_to_flow_controller_queue,
                                       net_write_queue=self.net_write_queue,
                                       clock=time.clock)
        self.writer = CCNxzGenClient.SocketWriterThread(read_queue=self.net_write_queue, socket=self.reader.socket,
                                                        peer=("127.0.0.1", self.server_port))

        # Join the writer first
        self.threads = [self.writer, self.reader, self.parser, self.fc]

        for t in self.threads:
            t.start()

    def tearDown(self):
        for t in self.threads:
            t.stop()

        for t in self.threads:
            t.join(timeout=0.2)

        self.reader.close()

    def test_with_server(self):
        """
        Instantiate a CCNxzGenServer with 10 items in it and have the flow controller
        pull them all out.
        """
        interests = []
        objects_by_name = {}
        objects_by_hash = {}

        interest_count = 10
        for i in range(0, interest_count):
            # make the TX queue larger than window
            name = CCNxNameFactory.from_uri("lci:/apple/" + str(i))
            interest = CCNxInterest(name)
            interests.append(interest)
            object = CCNxContentObject(name, None, CCNxTlv(T_PAYLOAD, 5, [i] * 5))
            object.sign(_key)
            objects_by_name[object.name] = object
            objects_by_hash[object.hash().tostring()] = object

        server_port = 9696
        gen_server = CCNxzGenServer(port=server_port, key=_key, objects_by_name=objects_by_name,
                                    objects_by_hash=objects_by_hash)
        gen_server.start()

        try:
            for interest in interests:
                self.user_read_queue.put(interest)

            read_count = 0
            while read_count < interest_count:
                try:
                    message = self.user_write_queue.get(block=True, timeout=1)
                    read_count += 1
                    print "read ", message

                except Queue.Empty:
                    print "Timed out reading from flow controller"
                    break

        finally:
            gen_server.stop()
            gen_server.join()


if __name__ == '__main__':
    unittest.main()
