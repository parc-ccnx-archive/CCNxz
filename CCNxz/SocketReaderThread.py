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

import threading
import SocketServer
from CCNxz.QueueEntry import *


class SocketReaderThread(threading.Thread):
    """
    Runs a SocketServer on a designated port.  For each UDP read, creates a QueueEntry and
    puts it in an output queue for handling by a different thread.

    Because each item put in the SocketReaderThread write_queue has a reference to the UDP server socket,
    the socket is not closed until the user explicitly calls the close() method.  This lets the user
    join all other threads that might be using the UDP server socket before closing the socket.

    Typical usage:
        parse_queue = Queue.Queue()
        lookup_queue = Queue.Queue()
        writer_queue = Queue.Queue()

        socket_reader = SocketReaderThread(self.__port, parse_queue, timeout=0.2)
        parser = ParserThread(parse_queue, lookup_queue)
        lookup = LookupThread(lookup_queue, writer_queue, keyid_array, objects_by_name, objects_by_hash)
        socket_writer = SocketWriterThread(writer_queue)

        threads = [socket_reader, parser, lookup, socket_writer]
        for t in threads:
            t.start()

        # block until ready to exit
        for t in threads:
            t.stop()

        for t in threads:
            t.join()

        # finally do explicit close on UDP socket
        socket_reader.close()

    """
    class MyUdpHandler(SocketServer.BaseRequestHandler):
        def handle(self):
            print "client: ", self.client_address
            data = self.request[0]
            socket = self.request[1]
            client = self.client_address
            entry = QueueEntry(client, data, socket)
            self.server.receive(entry)

    class MyUdpServer(SocketServer.UDPServer):
        def __init__(self, address, write_queue):
            """
            :param address: The (host, port) pair to pass to UDPServer
            :param receive_queue: The queue to put QueueEntry object on for processing
            :return: MyUdpServer
            """
            print "SocketReaderThread.MyUdpServer on address ", address
            self.__write_queue = write_queue

            SocketServer.UDPServer.allow_reuse_address = True
            SocketServer.UDPServer.__init__(self, address, SocketReaderThread.MyUdpHandler, bind_and_activate=True)

        def receive(self, entry):
            self.__write_queue.put(entry)

    def __init__(self, port, write_queue, timeout=None):
        super(SocketReaderThread, self).__init__()

        print "Starting server on port ", port
        self.__udp_server = SocketReaderThread.MyUdpServer(("0.0.0.0", port), write_queue)
        self.__udp_server.timeout = timeout
        self.__kill = False
        self.setName("SocketReaderThread")

    def run(self):
        while not self.__kill:
            self.__udp_server.handle_request()
        print "SocketReaderThread exiting run"

    def stop(self):
        """
            Indicates the UDP server should exit its handle_request() loop.  The loop will
            exit after a short poll interval.  The caller should use join() to wait for the
            loop to exist, then call close().
            """
        self.__kill = True

    def close(self):
        """Closes the UDP socket"""
        self.__udp_server.socket.close()

    @property
    def socket(self):
        """
        Reference to the UDP server's socket.  The caller must ensure that it is not used after
        close() is called on this object.
        :return:
        """
        return self.__udp_server.socket
