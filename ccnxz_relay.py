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
A UDP compressing relay

Listens on a UDP port for traffic from two peers.  When it gets a packet from
one peer it (de)compresses it and sends it to the other peer.

Client A -- [Metis A --] ccnxz_relay A -- ccnxz_channel -- ccnxz_relay B [-- Metis B] -- Client B

Runs as four threads:
    main: blocks waiting for UDP server to exist
    server: runs SocketServer loop
    worker1: from remote1 to remote2
    worker2: from remote2 to remote1
"""
import SocketServer
import threading
import Queue
import argparse
import textwrap
from socket import error as socket_error

from CCNxz.QueueEntry import *
from CCNxz.CCNxCompressor import *
from CCNx.CCNxParser import *
from CCNxz.CCNxNullDecompressor import *

__author__ = 'mmosko'


def _usage():
    print "usage: ccnxz_relay -h"
    print "       ccnxz_relay port remote1 remote2"
    print ""
    print "-h:      This help display"
    print "port1:   The UDP port to bind to (on all interfaces)"
    print "remote1: The first remote system (hostname:port)"
    print "remote2: The second remote system (hostname:port)"
    print ""
    print "Packets received from one remote will be sent to the other"
    print "remote, as a UDP relay.  Uncompressed packets will be compressed"
    print "and compressed packets will be uncompressed.  A typical"
    print "configuration would be to insert ccnxz_relay between two Metis"
    print "instances to compress the link between them."
    print ""
    print "Example:"
    print "   ccnxz_relay 9696 big.parc.com:9696 murdock.parc.com:9696"
    print ""


class Address(object):
    def __init__(self, host, port):
        self.__host = host
        self.__port = port

    def __str__(self):
        return "({}, {})".format(self.host, self.port)

    def __repr__(self):
        return self.__str__()

    def equals(self, address):
        return (self.__host, self.__port) == address

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    @property
    def tuple(self):
        return self.__host, self.__port


class MyUdpHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print "client: ", self.client_address
        data = self.request[0]
        socket = self.request[1]
        client = self.client_address
        entry = QueueEntry(client, data, socket)
        self.server.receive(entry)


class MyUdpServer(SocketServer.UDPServer):
    def __init__(self, address, addr1, addr2, worker_queue_1, worker_queue_2):
        print "MyUdpServer on address ", address
        self.__addr1 = addr1
        self.__addr2 = addr2
        self.__queue1 = worker_queue_1
        self.__queue2 = worker_queue_2

        SocketServer.UDPServer.allow_reuse_address = True
        SocketServer.UDPServer.__init__(self, address, MyUdpHandler, bind_and_activate=True)

    def receive(self, entry):
        print "receive ", entry
        if self.__addr1.equals(entry.client):
            print "Enqueue #2: ", entry
            self.__queue2.put(entry)
        elif self.__addr2.equals(entry.client):
            print "Enqueue #1: ", entry
            self.__queue1.put(entry)
        else:
            raise ValueError("Packet client {} does not match either remote".format(entry.client))


class MyServer(threading.Thread):
    def __init__(self, port, addr1, addr2, queue1, queue2, timeout=None):
        super(MyServer, self).__init__()

        print "Starting server on port ", port
        self.__udp_server = MyUdpServer(("0.0.0.0", port), addr1, addr2, queue1, queue2)
        self.__udp_server.timeout = timeout
        self.__kill = False
        self.setName("MyServer SocketServer")

    def run(self):
        while not self.__kill:
            self.__udp_server.handle_request()
        self.__udp_server.socket.close()
        print "MyServer exiting run"

    def stop(self):
        self.__kill = True

    @property
    def socket(self):
        return self.__udp_server.socket


class CompressionWorker(threading.Thread):
    """Read the work queue and (de)compress things in there, then send them to our client"""
    def __init__(self, client_address, work_queue, server_socket):
        super(CompressionWorker, self).__init__()
        self.__client_address = client_address
        self.__work_queue = work_queue
        self.__kill = False
        self.__socket = server_socket

    @property
    def work_queue(self):
        return self.__work_queue

    def run(self):
        while not self.__kill:
            try:
                entry = self.__work_queue.get(block=True, timeout=1)
                data = array.array("B")
                data.fromstring(entry.data)

                is_uncompressed = CCNxNullDecompressor.is_uncompressed_fixed_header(data)

                if is_uncompressed:
                    print "Receive uncompressed, len = ", len(data)

                    parser = CCNxParser(data)
                    parser.parse()
                    compressor = CCNxCompressor(parser)
                    compressor.encode()
                    output = compressor.encoded
                    byte_array = array.array("B")
                    byte_array.fromlist(output)
                    self.__socket.sendto(byte_array, self.__client_address.tuple)
                else:
                    print "Receive compressed, len =   ", len(data)

                    parser = CCNxParser(data)
                    parser.parse()

            except Queue.Empty:
                pass

        print "Worker {} exiting run".format(self.__client_address)

    def stop(self):
        self.__kill = True


def _parse_remote(argv):
    _host, _port = argv.split(":")
    return Address(_host, int(_port))


class NewlineParser(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        print "text = ", text
        # this is the RawTextHelpFormatter._split_lines
        if text.find('\n') > -1:
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)


def _parse_args():
    """
    command line: -p port --peer peer1 --peer peer2
    command line: -h

    :param argv:
    :return: [port, peer1, peer2] or ["-h"] or None (error)
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='A UDP relay to (de)compress CCNx packets',
        epilog=textwrap.dedent('''\
            Packets received from one peer will be sent to the other
            peer, as a UDP relay.  Uncompressed packets will be compressed
            and compressed packets will be uncompressed.  A typical
            configuration would be to insert ccnxz_relay between two Metis
            instances to compress the link between them.

            Example:
                ccnxz_relay -p 9696 -peers foo:9695 bar:9695'''))

    parser.add_argument('-p', required=True, dest='port', type=int, action='store', help='ccnxz_relay listen port')
    parser.add_argument('--peers', required=True, dest='peer', nargs=2, help='The two peers (host:port)')

    args = parser.parse_args()
    return args


def _join(thread):
    while thread.is_alive():
        thread.join(timeout=0.25)


def _run_main():
    args = _parse_args()

    port = args.port
    peer_1 = _parse_remote(args.peer[0])
    peer_2 = _parse_remote(args.peer[1])

    queue_1 = Queue.Queue()
    queue_2 = Queue.Queue()

    print "ccnxz_relay port {} peer {} peer {}".format(port, peer_1, peer_2)

    try:
        server = MyServer(port, peer_1, peer_2, queue_1, queue_2, timeout=0.5)
        server.start()

        worker_1 = CompressionWorker(peer_1, queue_1, server.socket)
        worker_2 = CompressionWorker(peer_2, queue_2, server.socket)

        worker_1.start()
        worker_2.start()

        # block until it exits
        try:
            _join(server)

        except (KeyboardInterrupt, SystemExit):
            print "Got keyboard interrupt or SystemExit"

        worker_1.stop()
        worker_2.stop()
        server.stop()

        _join(worker_1)
        _join(worker_2)
        _join(server)

    except socket_error as err:
        print "Socket error: {}".format(err.strerror)


if __name__ == "__main__":
    _run_main()
