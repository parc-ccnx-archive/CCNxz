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


import Queue

from CCNxz.SocketReaderThread import *
from CCNx.CCNxMessageFactory import *
from CCNx.CCNxInterest import *
from CCNxz.SocketWriterThread import SocketWriterThread


class ParserThread(threading.Thread):
    """
    Reads a QueueEntry from a read_queue, runs CCNxParser on it, adds a CCNxMessage
    (either CCNxInterest or CCNxContentObject) to the Queue entry
    """
    def __init__(self, read_queue, write_queue):
        super(ParserThread, self).__init__()
        self.__read_queue = read_queue
        self.__write_queue = write_queue
        self.__kill = False
        self.setName("ParserThread")

    def run(self):
        while not self.__kill:
            try:
                entry = self.__read_queue.get(block=True, timeout=0.2)
                # Figure out what kind of message it is and create appropriate object
                message = CCNxMessageFactory.from_wire_format(entry.data)
                entry.message = message
                self.__write_queue.put(entry)

            except Queue.Empty:
                pass
        print "ParserThread exiting run"

    def stop(self):
        self.__kill = True


class LookupThread(threading.Thread):
    """
    Reads a read_queue, does table lookups to match a parsed QueueEntry to a CCNxMessage
    and if a match, puts (entry, co) on a write_queue.
    """
    def __init__(self, read_queue, write_queue, keyid_array, objects_by_name, objects_by_hash):
        """
        Perform the dictionary lookups to match the request to a content object.
        If there is no match, the request dies here.

        If there is a match, we put (entry, co) on the write_queue.

        :param read_queue: The input Queue (QueueEntry)
        :param write_queue: The output Queue (QueueEntry, ContentObject) pair
        :param keyid_array: Our KeyId as a byte array
        :param objects_by_name: dictionary by CCNxName to CCNxMessage
        :param objects_by_hash: dictionary by byte array to CCNxMessage
        """
        super(LookupThread, self).__init__()

        self.__read_queue = read_queue
        self.__write_queue = write_queue
        self.__keyid_array = keyid_array
        self.__objects_by_name = objects_by_name
        self.__objects_by_hash = objects_by_hash
        self.__kill = False
        self.setName("LookupThread")

    def run(self):
        while not self.__kill:
            try:
                entry = self.__read_queue.get(block=True, timeout=0.2)
                name = None
                keyid_restr = None
                hash_restr = None

                try:
                    if type(entry.message) == CCNxInterest:
                        name = entry.message.name
                        keyid_restr = entry.message.keyid_restr
                        hash_restr = entry.message.hash_restr

                        if self.__keyid_ok(keyid_restr):
                            co = self.__lookup(name, hash_restr)
                            if co is not None:
                                #print "LookupThread returning: ", co.wire_format
                                self.__write_queue.put((entry, co))
                    else:
                        raise AttributeError("Not an Interest: ", entry.message)

                except AttributeError as err:
                    print "caught error parsing Interest", err
                    print "name        = ", name
                    print "keyid_restr = ", keyid_restr
                    print "hash_restr  = ", hash_restr

            except Queue.Empty:
                pass
        print "LookupThread exiting run"

    def stop(self):
        self.__kill = True

    def __keyid_ok(self, keyid_restr):
        return keyid_restr is None or keyid_restr == self.__keyid_array

    def __lookup(self, name, hash_restriction):
        co = None
        try:
            if hash_restriction is not None:
                # If it has a ContentObjectHashRestr, lookup by hash
                key = hash_restriction.tostring()
                #print "hash_restriction key = ", [ord(b) for b in key]
                co = self.__objects_by_hash[key]
            elif name is not None:
                # else lookup by Name
                #print "Trying to match name hash = ", name.__hash__()
                co = self.__objects_by_name[name]
        except KeyError:
            pass

        if co is None:
            print "__lookup no match"
        return co


class CCNxzGenServer(object):
    def __init__(self, port, key, objects_by_name, objects_by_hash):
        """
        Runs the CCNxzGenServer for serving files as Manifest transported content objects.

        objects_by_name is a dictionary from a CCNxName to a CCNxContentObject.
        objects_by_hash is a dictionary from a 'string' of the hash to a CCNxContentObject.

        :param port: The UDP port to bind to
        :param key: Crypto.PublicKey.RSA key
        :param objects_by_name: CCNxName to CCNxMessage
        :param objects_by_hash: byte array to CCNxMessage
        :return:
        """
        self.__port = port
        signer = CCNxSignature(key)
        self.__keyid_array = signer.keyid_array
        self.__objects_by_name = objects_by_name
        self.__objects_by_hash = objects_by_hash
        self.__treads = []

    def start(self):
        """
        Starts the server threads.  The server is made up of a FIFO processing pipe line:
        SocketReaderThread, ParserThread, LookupThread, SocketWriterThread.

        Call stop() to terminate all threads and join() to wait for them all to exit
        their rum() methods.
        :return:
        """
        # Queues named after the reader
        parse_queue = Queue.Queue()
        lookup_queue = Queue.Queue()
        writer_queue = Queue.Queue()

        self.socket_reader = SocketReaderThread(self.__port, parse_queue, timeout=0.2)
        parser = ParserThread(parse_queue, lookup_queue)
        lookup = LookupThread(lookup_queue, writer_queue, self.__keyid_array, self.__objects_by_name,
                              self.__objects_by_hash)
        socket_writer = SocketWriterThread(writer_queue)

        self.__treads = [self.socket_reader, parser, lookup, socket_writer]

        for t in self.__treads:
            t.start()

    def stop(self):
        """Signal the server to stop all threads"""
        for t in self.__treads:
            t.stop()

    def join(self):
        """Join all the threads"""
        for t in self.__treads:
            self.__join(t)

        self.socket_reader.close()

    @staticmethod
    def __join(thread):
        """Join the server thread with a timeout to avoid blocking interrupts"""
        while thread.is_alive():
            thread.join(timeout=0.25)
