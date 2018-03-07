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

import time

from Crypto.PublicKey import RSA

from CCNxz.SocketReaderThread import *
from CCNxz.CCNxzGenServer import ParserThread
from CCNx.CCNxName import *
from CCNxz.FlowControllerThread import *
from CCNxz.ManifestProcessorThread import *


class CCNxzGenClient(object):
    def __init__(self, args):
        self.__port = args['port']
        self.__name = CCNxNameFactory.from_uri(args['name'])
        self.__peer = args['peer']
        self.__pubkey = RSA.importKey(open(args['pubkey']).read())

    def loop(self):
        # ======= Queues between components

        # From network to Parser
        net_to_parser_queue = Queue.Queue()

        # From Parser to Flow Controller
        parser_to_flow_controller_queue = Queue.Queue()

        # From Manifest Processor to User
        manifest_to_user_queue = Queue.Queue()

        # From Manifest Processor to Flow Controller
        manifest_to_flow_controller_queue = Queue.Queue()
        flow_controller_to_manifest_queue = Queue.Queue()

        socket_writer_queue = Queue.Queue()

        # ======= Threads

        socket_reader_thread = SocketReaderThread(self.__port, net_to_parser_queue, timeout=0.5)
        parser_thread = ParserThread(net_to_parser_queue, parser_to_flow_controller_queue)

        manifest_processor_thread = ManifestProcessorThread(name=self.__name,
                                                            user_write_queue=manifest_to_user_queue,
                                                            to_transport_queue=manifest_to_flow_controller_queue,
                                                            from_transport_queue=flow_controller_to_manifest_queue)

        flow_controller_thread = FlowControllerThread(user_read_queue=manifest_to_flow_controller_queue,
                                                      user_write_queue=flow_controller_to_manifest_queue,
                                                      net_read_queue=parser_to_flow_controller_queue,
                                                      net_write_queue=socket_writer_queue,
                                                      clock=time.clock)

        socket_writer_thread = CCNxzGenClient.SocketWriterThread(read_queue=socket_writer_queue,
                                                                 socket=socket_reader_thread.socket,
                                                                 peer=self.__peer)

        threads = [socket_reader_thread, parser_thread, flow_controller_thread, manifest_processor_thread,
                   socket_writer_thread]

        # ====== Now run it all

        for t in threads:
            t.start()

        # block until it exits
        try:
            self.__join(socket_reader_thread)

        except (KeyboardInterrupt, SystemExit):
            print "Got keyboard interrupt or SystemExit"

        for t in threads:
            t.stop()

        for t in threads:
            self.__join(t)

        socket_reader_thread.close()

        print "Exiting CCNxzGenServer loop"

    @staticmethod
    def __join(thread):
        while thread.is_alive():
            thread.join(timeout=0.25)

    class SocketWriterThread(threading.Thread):
        """
        The read_queue is a PriorityQueue and the entries are (priority, CCNxMessage).  Reads
        the CCNxMessage from the read_queue and sends them to self.__peer using self.__socket.
        """
        def __init__(self, read_queue, socket, peer):
            super(CCNxzGenClient.SocketWriterThread, self).__init__()

            self.__read_queue = read_queue
            self.__socket = socket
            self.__peer = peer
            self.__kill = False

        def run(self):
            while not self.__kill:
                try:
                    priority, message = self.__read_queue.get(block=True, timeout=0.2)
                    self.__socket.sendto(message.wire_format, self.__peer)

                except Queue.Empty:
                    pass

        def stop(self):
            self.__kill = True
