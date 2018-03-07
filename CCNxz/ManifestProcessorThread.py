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
import Queue
from collections import deque
from CCNx.CCNxName import *
from CCNx.CCNxInterest import *
from CCNx.CCNxManifestParser import *

__author__ = 'mmosko'


class ManifestProcessorThread(threading.Thread):
    def __init__(self, name, keyid, user_write_queue, transport_read_queue, transport_write_queue):
        """
        :param name: The prefix to ask for (will append chunk numbers)
        :param keyid: byte array of the keyid to use when we don't know a hash
        :param user_write_queue: queue of CCNxContentObjects up to user
        :param transport_read_queue: input from the transport (a parsed CCNxMessage)
        :param transport_write_queue: output to the transport (a CCNxInterest)
        :return:
        """
        super(ManifestProcessorThread, self).__init__()
        self.__name = name
        self.__keyid = keyid
        self.__user_write_queue = user_write_queue
        self.__transport_read_queue = transport_read_queue
        self.__transport_write_queue = transport_write_queue
        self.__kill = False

    def run(self):
        self.__fetch_first_manifest()
        while not self.__kill:
            try:
                message = self.__transport_read_queue.get(block=True, timeout=0.2)
                if message.manifest is None:
                    # it's data
                    self.__user_write_queue.put(message)
                else:
                    # it's a manifest
                    self.__receive_manifest(message)

            except Queue.Empty:
                pass

        print "ManifestProcessorThread exiting run"

    def stop(self):
        self.__kill = True

    def __fetch_first_manifest(self):
        chunk_0 = CCNxNameFactory.from_name(self.__name, 0)
        first_interest = CCNxInterest(chunk_0, self.__keyid, None)
        self.__transport_write_queue.put(first_interest)

    def __receive_manifest(self, message):
        manifest = CCNxManifestParser(message)
        chunk_number = manifest.manifest_start_chunk
        for hash_value in manifest.manifest_hash_list:
            chunked_name = CCNxNameFactory.from_name(self.__name, chunk_number)
            interest = CCNxInterest(chunked_name, None, hash_value)
            self.__transport_write_queue.put(interest)
            print "ManifestProcessor put ", interest
            chunk_number += 1

        chunk_number = manifest.data_start_chunk
        for hash_value in manifest.data_hash_list:
            chunked_name = CCNxNameFactory.from_name(self.__name, chunk_number)
            interest = CCNxInterest(chunked_name, None, hash_value)
            self.__transport_write_queue.put(interest)
            print "ManifestProcessor put ", interest
            chunk_number += 1
