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

import array
from urlparse import urlparse
from CCNxz.CCNxNullCompressor import *


class CCNxNameFactory(object):
    class CCNxName:
        """
        self.__tlv is a linear list of non-nested TLVs.  The first TLV is the
        T_NAME TLV.
        """
        def __init__(self, segments):
            self.__wire_format = None
            if segments is None:
                segments = []

            length = 0
            for tlv in segments:
                length += tlv.length + 4

            self.__tlv_list = [CCNxTlv(T_NAME, length, None)]
            self.__tlv_list.extend(segments)
            self.__hash = None

        def __str__(self):
            return self.__tlv_list.__str__()

        def __hash__(self):
            if self.__hash is None:
                self.__hash = hash(tuple(self.encode()))

            return self.__hash

        def __eq__(self, other):
            return self.encode() == other.encode()

        def add_segment(self, tlv_type, value):
            if value is None:
                seg = CCNxTlv(tlv_type, 0, None)
            else:
                seg = CCNxTlv(tlv_type, len(value), value)

            self.__tlv_list.append(seg)
            self.__tlv_list[0].length += 4 + seg.length
            self.__wire_format = None

        def segment_count(self):
            return len(self.__tlv_list) - 1

        def remove_last(self):
            last_index = len(self.__tlv_list) - 1
            if last_index == 0:
                raise IndexError("Cannot remove T_NAME tlv")

            last = self.__tlv_list.pop()
            self.__tlv_list[0].length -= last.length

        def get_segment(self, index):
            if not index < self.segment_count():
                raise IndexError("Index {} not less than segment count {}".format(
                    index, self.segment_count()))

            # +1 because the first TLV is not a segment, it's the T_NAME
            return self.__tlv_list[index + 1]

        def encode(self):
            if self.__wire_format is None:
                self.__wire_format = CCNxNullCompressor.encode_tlv_list(list(self.__tlv_list))
            return self.__wire_format

        def segments(self):
            return self.__tlv_list[1:]

        def tlv_list(self):
            """The name as a TLV list, including the T_NAME element"""
            return self.__tlv_list

        @property
        def length(self):
            """Returns the total bytes used by the encoded name"""
            return 4 + self.__tlv_list[0].length

        @property
        def chunk_number(self):
            last_index = len(self.__tlv_list) - 1
            last_tlv = self.__tlv_list[last_index]

            chunk_number = None
            if last_tlv.type == T_CHUNK:
                chunk_number = CCNxTlv.array_to_number(last_tlv.value)
            return chunk_number

        @chunk_number.setter
        def chunk_number(self, chunk_number):
            last_index = len(self.__tlv_list) - 1
            last_tlv = self.__tlv_list[last_index]

            if last_tlv.type == T_CHUNK:
                self.remove_last()

            chunk_number_array = CCNxTlv.number_to_array(chunk_number)
            chunk_tlv = CCNxTlv(T_CHUNK, len(chunk_number_array), chunk_number_array)
            self.add_segment(chunk_tlv)

    @staticmethod
    def __label_to_type(label):
        upper = label.upper()
        if upper == "CHUNK":
            return T_CHUNK

        if upper == "SERIAL":
            return T_SERIAL

        raise ValueError("Unsupported name segment label: {}".format(label))

    @staticmethod
    def from_uri(uri):
        """
        Parses the NAME URI in to name segments and returns the nested CCNxTlv for T_NAME

        :return: CCNxTlv for T_NAME
        """
        url = urlparse(uri)
        if url.scheme != 'lci':
            raise ValueError("Name schema must be LCI, got {}".format(url.scheme))
        # eliminate the leading '/' with [1:]
        segments = url.path[1:].split('/')
        tlv_list = []
        length = 0
        for seg in segments:
            # print "segment = ", seg

            # Does it have a label?
            pieces = seg.split('=')
            if len(pieces) == 2:
                tlv_type = CCNxNameFactory.__label_to_type(pieces[0])
                value = pieces[1]
            else:
                tlv_type = T_NAMESEG
                value = pieces[0]

            a = array.array("B", value)

            tlv = CCNxTlv(tlv_type, len(a), a)
            tlv_list.append(tlv)
            length += 4
            length += len(a)

        return CCNxNameFactory.CCNxName(tlv_list)

    @staticmethod
    def from_tlv_list(tlv_list):
        return CCNxNameFactory.CCNxName(tlv_list)

    @staticmethod
    def from_name(name, chunk_number = None):
        """
        Creates a new name from an old name.  If the chunk_number is not None, it will
        append a CHUNK name component.

        :param name: a CCNxName
        :param chunk_number: An integer
        :return: a CCNxName
        """
        segments = name.segments()
        new_name = CCNxNameFactory.CCNxName(segments)
        if chunk_number is not None:
            a = CCNxTlv.number_to_array(chunk_number)
            new_name.add_segment(T_CHUNK, a)
        return new_name

