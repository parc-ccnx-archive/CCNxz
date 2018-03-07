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
Null Compressor will write out the Parser in uncompressed form
"""

__author__ = 'mmosko'

from CCNx.CCNxParser import *

class CCNxNullCompressor(object):
    def __init__(self, parser):
        if not isinstance(parser, CCNxParser):
            raise TypeError("parser must be of type CCNxParser")
        self.__parser = parser
        self.__encoded = []
        self.__encodedHeaders = []
        self.__encodedBody = []
        self.__encodedFixedHeader = []

    def encode(self):
        self.__encode_fixed_header()
        self.__encode_headers()
        self.__encode_body()
        self.__generate_encoded()

    @property
    def encoded(self):
        return self.__encoded

    def __generate_encoded(self):
        self.__encoded = self.__encodedFixedHeader
        self.__encoded.extend(self.__encodedHeaders)
        self.__encoded.extend(self.__encodedBody)

    def __encode_fixed_header(self):
        self.__encodedFixedHeader = self.__parser.fixed_header.byte_array()

    @staticmethod
    def __compact_tlv(tlv):
        """
        The given TLV cannot be compressed, so encode it using 2+2

        :param tlv: The TLV to encode
        :return: The wire format string
        """
        tlv = list.pop(0)
        print "Could not compress type {} length {}".format(tlv.type, tlv.length)
        encoded = CCNxCompressorVariableLength.compact(tlv)
        if tlv.length > 0:
            encoded.extend(tlv.value)
        return encoded

    def __encode_headers(self):
        self.__encodedHeaders = self.encode_tlv_list(self.__parser.headers)

    def __encode_body(self):
        linear_body = self.__parser.linearize_body()
        self.__encodedBody = self.encode_tlv_list(linear_body)

    @staticmethod
    def encode_tlv_list(list):
        """
        Takes a linearized list of TLVs and encodes it.

        A linearized list of TLVs is one where no TLVs are nested.
        Container TLVs have a positive length and a value of None.

        :param list: a linearized list of TLVs
        :return: byte array
        """
        output = []
        # See if the FixedLength dictionary can consume tokens
        while len(list) > 0:
            tlv = list.pop(0)
            result = [tlv.type >> 8, tlv.type & 0xFF, tlv.length >> 8, tlv.length & 0xFF]
            if tlv.length > 0 and tlv.value is not None:
                result.extend(tlv.value)

            output.extend(result)
        return output

