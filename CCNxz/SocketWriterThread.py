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

import Queue
import socket
import threading

__author__ = 'mmosko'


class SocketWriterThread(threading.Thread):
    """
    Reads a (QueueEntry, CCNxMessage) pair from a read_queue and writes the
    CCNxMessage.wire_format to the QueueEntry.socket.
    """
    def __init__(self, read_queue):
        super(SocketWriterThread, self).__init__()

        self.__read_queue = read_queue
        self.__kill = False
        self.setName("SocketWriterThread")

    def run(self):
        while not self.__kill:
            try:
                entry, co = self.__read_queue.get(block=True, timeout=0.2)
                # print "SocketWriter: ", co.wire_format
                try:
                    entry.socket.sendto(co.wire_format, entry.client)
                except socket.error as err:
                    print "ERROR: SocketWriterThread writing to socket: {}".format(err)

            except Queue.Empty:
                pass
        print "SocketWriterThread exiting run"

    def stop(self):
        """
        Indicates that the thread should exit the run() method after a short poll timeout or
        after the current transaction.  The user should call join() to wait for the thread
        to terminate.
        """
        self.__kill = True