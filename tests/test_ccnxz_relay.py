#!/usr/bin/pyton

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

from ccnxz_relay import *
from CCNxz.Packets import *

# ##############
# Helpers for running the test


class TestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        client = self.client_address
        entry = QueueEntry(client, data, None)
        self.server.receive(entry)


class TestUdpServer(SocketServer.UDPServer):
    def __init__(self, address, recv_queue):
        self.__recv_queue = recv_queue
        SocketServer.UDPServer.allow_reuse_address = True
        SocketServer.UDPServer.__init__(self, address, TestHandler, bind_and_activate=True)

    def receive(self, entry):
        print "TestUdpServer receive ", entry
        self.__recv_queue.put(entry)


class TestClient(threading.Thread):
    def __init__(self, local_address):
        super(TestClient,self).__init__()
        self.__address = local_address
        self.__recv_queue = Queue.Queue()
        print "Starting client ", local_address.tuple
        SocketServer.UDPServer.allow_reuse_address = True
        self.__server = TestUdpServer(local_address.tuple, self.__recv_queue)

    def run(self):
        self.__server.serve_forever()
        self.__server.socket.close()
        print "TestClient {} exiting run".format(self.__address)

    def sendto(self, data, address):
        self.__server.socket.sendto(data, address.tuple)

    def receive(self, timeout=None):
        return self.__recv_queue.get(block=True, timeout=timeout)

    def stop(self):
        self.__server.shutdown()

# ##################
# The tests


class TestCCnxRelay(unittest.TestCase):
    def setUp(self):
        print "***\nsetUp"
        self.port = 9699
        self.remote1 = Address('127.0.0.1', 9697)
        self.remote2 = Address('127.0.0.1', 9698)
        self.relay_address = Address("localhost", self.port)

        self.client1 = TestClient(self.remote1)
        self.client2 = TestClient(self.remote2)
        self.client1.start()
        self.client2.start()

    def tearDown(self):
        print "***\ntearDown"
        self.client1.stop()
        self.client2.stop()
        self.client1.join()
        self.client2.join()

    def test_server_routing_1_to_2(self):
        """Send a packet from client 1 to relay to queue 2"""
        print "****\nrunning ", self._testMethodName

        q1 = Queue.Queue()
        q2 = Queue.Queue()

        my_server = MyServer(self.port, self.remote1, self.remote2, q1, q2, timeout=1)
        my_server.start()

        # Send a test packet from client 1 to the relay
        self.client1.sendto(Packets.interest_array, self.relay_address)

        # It should show up in q2
        try:
            test = q2.get(block=True,timeout=1)
        except Queue.Empty:
            test = None

        my_server.stop()
        self.assertTrue(test is not None, "Did not get packet in queue #2")

    def test_server_routing_2_to_1(self):
        """ Send a packet form client2 to relay to queue1"""
        print "****\nrunning ", self._testMethodName

        q1 = Queue.Queue()
        q2 = Queue.Queue()

        my_server = MyServer(self.port, self.remote1, self.remote2, q1, q2, timeout=1)
        my_server.start()

        # Send a test packet from client 1 to the relay
        self.client2.sendto(Packets.interest_array, self.relay_address)

        # It should show up in q1
        try:
            test = q1.get(block=True,timeout=1)
        except Queue.Empty:
            test = None

        my_server.stop()
        self.assertTrue(test is not None, "Did not get packet in queue #1")

    def floss_packet(self, packet_array):
        q1 = Queue.Queue()
        q2 = Queue.Queue()

        my_server = MyServer(self.port, self.remote1, self.remote2, q1, q2, timeout=1)
        my_server.start()

        worker2 = CompressionWorker(self.remote2, q2, my_server.socket)
        worker2.start()

        # Send a test packet from client 1 to the relay
        self.client1.sendto(packet_array, self.relay_address)

        # It should show up as readable in client2
        try:
            test = self.client2.receive(timeout=1)
            print "Received packet len = ", len(test.data)
        except Queue.Empty:
            test = None

        my_server.stop()
        worker2.stop()
        worker2.join()

        return test

    def test_worker_compress(self):
        """Send a packet from client 1 to relay to worker 2"""
        print "****\nrunning ", self._testMethodName
        test = self.floss_packet(list(Packets.interest_array))

        self.assertTrue(test is not None, "Did not get packet in queue #2")
        self.assertTrue(len(test.data) == len(Packets.compressed_interest),
                        "Wrong length expected {} got {}".format(len(Packets.compressed_interest), len(test.data)))

    def test_worker_decompress(self):
        """Send a packet from client 1 to relay to worker 2"""
        print "****\nrunning ", self._testMethodName
        test = self.floss_packet(list(Packets.compressed_interest_array))

        self.assertTrue(test is not None, "Did not get packet in queue #2")
        self.assertTrue(len(test.data) == len(Packets.interest),
                        "Wrong length expected {} got {}".format(len(Packets.interest), len(test.data)))

if __name__ == "__main__":
    unittest.main()
