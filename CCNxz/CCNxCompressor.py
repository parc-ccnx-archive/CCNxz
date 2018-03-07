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
    Re-encode a parsed object using compressed format

    Arguments:
        :parser: A CCNxParser representing a packet

    Returns:
        Byte string

"""

# __author__ = 'mmosko'

from CCNx.CCNxParser import *
from CCNxCompressorFixedLength import CCNxCompressorFixedLength
from CCNxCompressorVariableLength import CCNxCompressorVariableLength
from CCNxCompressorFixedHeader import CCNxCompressorFixedHeader


class CCNxCompressor(object):
    def __init__(self, parser):
        if not isinstance(parser, CCNxParser):
            raise TypeError("parser must be of type CCNxParser")
        self.__parser = parser
        self.__encoded = ""
        self.__encodedHeaders = ""
        self.__encodedBody = ""
        self.__encodedFixedHeader = ""
        self.__fixed_length_compressor = CCNxCompressorFixedLength()
        self.__context_id = 1

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
        encoded = CCNxCompressorFixedHeader.compress(self.__parser.fixed_header, self.__context_id)
        self.__encodedFixedHeader = encoded

    def __encode_fixed_length_value(self, list):
        # this function will possibly encode 1 or more TLVs from the list.
        # The value will be encoded too, so we do not need to do that here.
        encoded = self.__fixed_length_compressor.compress(list)
        return encoded

    @staticmethod
    def __encode_variable_length_value(list):
        """
        Try to compress the top TLV in the list using a variable-length key.

        :param list: A list of TLVs to compress
        :return:  The compressed TLV or None
        """
        encoded = None
        tlv = list[0]
        encoded = CCNxCompressorVariableLength.compress(tlv)
        if encoded is not None:
            list.pop(0)
            if tlv.value is not None:
                encoded.extend(tlv.value)
        return encoded

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

    def __encode_tlv_list(self, list):
        output = []
        # See if the FixedLength dictionary can consume tokens
        while len(list) > 0:
            result = self.__encode_fixed_length_value(list)
            if result is None:
                result = self.__encode_variable_length_value(list)
                if result is None:
                    result = self.__compact_tlv(list)
            output.extend(result)
        return output

    def __encode_headers(self):
        self.__encodedHeaders = self.__encode_tlv_list(self.__parser.headers)

    def __encode_body(self):
        linear_body = self.__parser.linearize_body()
        self.__encodedBody = self.__encode_tlv_list(linear_body)
