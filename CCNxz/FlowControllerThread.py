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

import threading
from collections import deque
import Queue

from CCNx.CCNxMessage import *
from CCNx.CCNxName import *

__author__ = 'mmosko'


class FlowControllerThread(threading.Thread):
    _rtx_priority = 0
    _data_priority = 1
    _max_expiry_time = 0xFFFFFFFFFFFFFFFF

    class TxQueueEntry(object):
        """
        Stored in the FlowControllerThread __tx_queue.
        """
        def __init__(self, data, expiry_time, send_time):
            self.__data = data
            self.__expiry_time = expiry_time
            self.__send_time = send_time

        def __eq__(self, other):
            return self.data == other.data

        @property
        def data(self):
            return self.__data

        @property
        def expiry_time(self):
            return self.__expiry_time

        @property
        def send_time(self):
            return self.__send_time

    def __init__(self, user_read_queue, user_write_queue, net_read_queue, net_write_queue, clock):
        """
        Reads a queue of Interests from the user and issues them to the network.  handles
        keeping the outstanding number of Interests a reasonable size and hndles re-transmissions.

        The net_write_queue is a PriorityQueue and the entries are (priority, CCNxMessage).  Lower
        priorities take precedence.

        The net_read_queue should have already parsed the QueueEntry and included the parser
        in the QueueEntry.

        :param user_read_queue: A queue of CCNxMessage (interests) from user to fetch from network
        :param user_write_queue: Return CCNxMessage (objects) to user
        :param net_read_queue: A queue of QueueEntry from the network
        :param net_write_queue: A queue of (priority, CCNxMessage) to send to network
        :param clock: Something like time.clock
        :return:
        """
        super(FlowControllerThread, self).__init__()

        self.__user_read_queue = user_read_queue
        self.__user_write_queue = user_write_queue
        self.__net_read_queue = net_read_queue
        self.__net_write_queue = net_write_queue
        self.__clock = clock
        self.__kill = False

        self.__max_window = 128
        self.__window_size = 4
        self.__tx_queue = deque()
        self.__rtx_queue = deque()
        self.__rtt_estimate = 0.100
        self.__min_expiry_time = self._max_expiry_time

    @property
    def current_window_size(self):
        return self.__window_size

    @property
    def tx_queue_length(self):
        """Possibly not thread safe..."""
        return len(self.__tx_queue)

    @property
    def rtx_queue_length(self):
        """Possibly not thread safe..."""
        return len(self.__rtx_queue)

    @staticmethod
    def __keyid_ok(tx_entry, message):
        """tx_entry is the Interest we sent.  If it has a keyid restriction, then the
        received message has to match the keyid field"""
        ok = False
        if tx_entry.data.keyid_restr is not None:
            if message.keyid is not None:
                if tx_entry.data.keyid_restr == message.keyid:
                    ok = True
        else:
            ok = True
        return ok

    @staticmethod
    def __hash_ok(tx_entry, message):
        """tx_entry is the Interest we sent.  If it has a hash restriction, then the
        received message has to match the hash"""
        ok = False
        if tx_entry.data.hash_restr is not None:
            received_hash = message.hash()
            if tx_entry.data.hash_restr == received_hash:
                ok = True
        else:
            ok = True
        return ok

    @staticmethod
    def __keyid_from_valag(valalg_tlv):
        for tlv in valalg_tlv.value:
            if tlv.type == T_RSA_SHA256:
                # Need to go down another level of recursion
                return FlowControllerThread.__keyid_from_valag(tlv.value)
            elif tlv.type == T_KEYID:
                return tlv.value
        return None

    def run(self):
        while not self.__kill:
            # will remove expired Interests from the tx queue and put
            # them on the rtx queue
            self.__expire_tx_queue()
            self.__enqueue_tx()

            try:
                wait_time = self.__rtt_estimate
                if len(self.__tx_queue) > 0:
                    next_expiry_time = self.__tx_queue[0].expiry_time
                    delta = max(self.__clock() - next_expiry_time, 0)
                    wait_time = min(delta, wait_time)

                queue_entry = self.__net_read_queue.get(block=True, timeout=wait_time)
                self.__receive(queue_entry)
            except Queue.Empty:
                pass

        print "FlowControllerThread exiting run"

    def stop(self):
        self.__kill = True

    def __append_tx_queue(self, message):
        """
        Appends a CCNxMessage to the tx_queue with appropriate send_time and
        expiry_time (based on RTT estimate).

        :param message: A CCNxMessage
        :return:
        """
        send_time = self.__clock()
        expiry_time = send_time + self.__rtt_estimate
        entry = FlowControllerThread.TxQueueEntry(message, expiry_time, send_time)
        self.__tx_queue.append(entry)
        if expiry_time < self.__min_expiry_time:
            self.__min_expiry_time = expiry_time

    def __receive(self, queue_entry):
        """
        Match packet to the TX queue.  Update our estimate of the RTT.
        Remove entry from TX queue.  Send data to the user.
        :param queue_entry: A QueueEntry from the network
        :return:
        """
        if queue_entry.message is None:
            raise ValueError("The QueueEntry received from the network does not have a message")

        name = queue_entry.message.name

        for i in range(len(self.__tx_queue)):
            try:
                tx_entry = self.__tx_queue[i]
            except IndexError as err:
                print "Error trying to read index {} out of {}".format(i, len(self.__tx_queue))
                raise err

            if tx_entry.data.name == name:
                if self.__keyid_ok(tx_entry, queue_entry.message) and self.__hash_ok(tx_entry, queue_entry.message):
                    # Found match!
                    print "Found match in tx_queue"
                    del self.__tx_queue[i]
                    self.__set_min_expiry_time()
                    self.__user_write_queue.put(queue_entry.message)
                    break
            print "ERROR: Could not match packet to TX queue: ", queue_entry.message.wire_format

    def __set_min_expiry_time(self):
        if len(self.__tx_queue) > 0:
            self.__min_expiry_time = self.__tx_queue[0].expiry_time
        else:
            self.__min_expiry_time = self._max_expiry_time

    def __input_available(self):
        return (len(self.__rtx_queue) > 0) or (not self.__user_read_queue.empty())

    def __expire_tx_queue(self):
        """
        Look at the expiry_time at the had of the tx queue and move to rtx queue
        if it has expired.  Finished when head of queue is not expired.

        This is not correct, as there could be entries beyond the head that will
        expire sooner because the RTT estimate has decreased.

        :return:
        """
        while len(self.__tx_queue) > 0:
            next_expiry = self.__tx_queue[0].expiry_time
            remaining_expiry_time = next_expiry - self.__clock()
            if remaining_expiry_time <= 0:
                expired = self.__tx_queue.popleft()
                self.__rtx_queue.append(expired.data)
            else:
                break

    def __enqueue_tx(self):
        while len(self.__tx_queue) < self.__window_size and self.__input_available():
            # If we have retransmissions waiting, service them first
            if len(self.__rtx_queue) > 0:
                interest = self.__rtx_queue.popleft()
                self.__net_write_queue.put((self._rtx_priority, interest))
                self.__append_tx_queue(interest)
            elif not self.__user_read_queue.empty():
                interest = self.__user_read_queue.get()
                self.__net_write_queue.put((self._data_priority, interest))
                self.__append_tx_queue(interest)

