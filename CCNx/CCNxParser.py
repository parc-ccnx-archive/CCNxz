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


# __author__ = 'mmosko'

import array
import binascii

from CCNx.CCNxTypes import *
from CCNxz.CCNxDecompressor import *
from CCNxz.CCNxNullDecompressor import *


class CCNxParser(object):
    def __init__(self, byte_array):
        self.__fixedHeader = None
        self.__headers = []
        self.__body = []
        self.__wire_format = byte_array
        self.__name_tlv = None
        self.__keyid_restr_tlv = None
        self.__hash_restr_tlv = None
        self.__keyid_tlv = None
        self.__expiry_tlv = None
        self.__manifest_tlv = None
        self.__payload_tlv = None

        if type(byte_array) == types.StringType:
            self.__input = array.array("B")
            self.__input.fromstring(byte_array)
        else:
            self.__input = byte_array

        print "Read buffer len = ", len(self.__input)

        if CCNxNullDecompressor.is_uncompressed_fixed_header(self.__input):
            self.__decompressor = CCNxNullDecompressor()
        else:
            self.__decompressor = CCNxDecompressor()

        self.__decompressed = array.array("B")

    def parse(self):
        self.__parse_header()
        self.__parse_headers()
        self.__parseBody()

    @property
    def wire_format(self):
        """
        The input to the parser
        :return: The original input byte_array
        """
        return self.__wire_format

    @property
    def fixed_header(self):
        return self.__fixedHeader

    @property
    def body(self):
        return self.__body

    @property
    def headers(self):
        return self.__headers

    @property
    def name_tlv(self):
        return self.__name_tlv

    @property
    def keyid_restriction_tlv(self):
        return self.__keyid_restr_tlv

    @property
    def hash_restriction_tlv(self):
        return self.__hash_restr_tlv

    @property
    def keyid_tlv(self):
        return self.__keyid_tlv

    @property
    def manifest_tlv(self):
        return self.__manifest_tlv

    @property
    def payload_tlv(self):
        return self.__payload_tlv

    def __linearize(self, entry, linear):
        if type(entry) == types.ListType or type(entry) == array.array:
            for element in entry:
                self.__linearize(element, linear)
        elif type(entry) == CCNxTlv:
            if type(entry.value) == CCNxTlv:
                tlv = CCNxTlv(entry.type, entry.length, None)
                linear.append(tlv)
                self.__linearize(entry.value, linear)
            elif (type(entry.value) == types.ListType) or (type(entry.value) == array.array):

                # If it is a list of TLVs or a list of lists, then recurse in to it
                if len(entry.value) > 0 and (type(entry.value[0]) == CCNxTlv or type(entry.value[0]) == types.ListType):
                    tlv = CCNxTlv(entry.type, entry.length, None)
                    linear.append(tlv)
                    self.__linearize(entry.value, linear)
                else:
                    # Otherwise it is a list of bytes
                    tlv = CCNxTlv(entry.type, entry.length, entry.value)
                    linear.append(tlv)
                    # no recursion
            else:
                raise ValueError("Parser in bad state type: ", type(entry.value))

    def linearize_body(self):
        """
        Convert the nested list of TLVs in the body to a simple list of TLVs in the right order.
        Container TLVs that do not have a terminal Value will have None as their Value.

        :return: list of TLVs
        """

        linear = []
        self.__linearize(self.__body, linear)
        return linear

    def __read_type_length(self):
        """
        This expands the TL tokens from the compressed stream to an uncompressed buffer and then
        reads them like normal TL tokens

        :return: (type, length) pair
        """

        if len(self.__decompressed) < 4:
            bytes = self.__decompressor.decompress_type_length(self.__input)
            self.__decompressed.extend(bytes)

        byte_array = self.__decompressed[0:4]
        del(self.__decompressed[0:4])

        type = (byte_array[0] << 8) | byte_array[1]
        length = (byte_array[2] << 8) | byte_array[3]

        return (type, length)

    def __read_value(self, length):
        value = self.__input[0:length]
        del self.__input[0:length]

        return value

    def __parse_terminal_token(self, type, length):
        value = self.__read_value(length)
        tlv = CCNxTlv(type, length, value)
        return tlv

    def __parse_header(self):
        fh_bytes = self.__decompressor.decompress_fixed_header(self.__input)

        fh = CCNxFixedHeader(fh_bytes)
        self.__fixedHeader = fh
        # print "fixed header: ", fh

    def __parse_headers(self):
        bytes_to_read = self.fixed_header.headerLength - 8

        while bytes_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            bytes_to_read -= 4

            value = self.__read_value(length)
            bytes_to_read -= length

            tlv = CCNxTlv(tlv_type, length, value)
            self.__headers.append(tlv)
            #print "header = ", tlv

    def __parseBody(self):
        length_to_read = self.fixed_header.packetLength - self.fixed_header.headerLength

        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}: [{}]".format(
                    length + 4, length_to_read, binascii.hexlify(self.__wire_format)))

            length_to_read -= 4

            if tlv_type == T_INTEREST:
                value = self.__parse_message(length)
                tlv = CCNxTlv(tlv_type, length, value)
                self.__body.append(tlv)
            elif tlv_type == T_OBJECT:
                value = self.__parse_message(length)
                tlv = CCNxTlv(tlv_type, length, value)
                self.__body.append(tlv)
            elif tlv_type == T_VALALG:
                value = self.__parse_validation_alg(length)
                tlv = CCNxTlv(tlv_type, length, value)
                self.__body.append(tlv)
            elif tlv_type == T_VALPAY:
                tlv = self.__parse_terminal_token(tlv_type, length)
                self.__body.append(tlv)
            else:
                raise ValueError("Unknown type = {}", tlv_type)

            length_to_read -= length

    def __parse_message(self, length_to_read):
        tlvs = []
        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}".format(length + 4, length_to_read))

            length_to_read -= 4

            if tlv_type == T_NAME:
                name = self.__parse_name(length)
                self.__name_tlv = CCNxTlv(tlv_type, length, name)
                tlvs.append(self.__name_tlv)
            elif tlv_type == T_MANIFEST:
                manifest = self.__parse_manifest(length)
                self.__manifest_tlv = CCNxTlv(tlv_type, length, manifest)
                tlvs.append(self.__manifest_tlv)
            else:
                tlv = self.__parse_terminal_token(tlv_type, length)
                tlvs.append(tlv)
                if tlv.type == T_KEYIDREST:
                    self.__keyid_restr_tlv = tlv
                elif tlv.type == T_OBJHASHREST:
                    self.__hash_restr_tlv = tlv
                elif tlv.type == T_PAYLOAD:
                    self.__payload_tlv = tlv

            length_to_read -= length

        return tlvs

    def __parse_name(self, length_to_read):
        tlvs = []
        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}".format(length + 4, length_to_read))

            length_to_read -= 4

            tlv = self.__parse_terminal_token(tlv_type, length)
            tlvs.append(tlv)

            length_to_read -= length

        return tlvs

    def __parse_validation_alg(self, length_to_read):
        tlv = None
        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}".format(length + 4, length_to_read))

            length_to_read -= 4

            value = self.__parse_validation_alg_body(length)
            tlv = CCNxTlv(tlv_type, length, value)

            length_to_read -= length

        return tlv

    def __parse_validation_alg_body(self, length_to_read):
        tlvs = []
        # All the tokens inside a Validation Alg are terminal tokens
        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}".format(length + 4, length_to_read))

            length_to_read -= 4

            tlv = self.__parse_terminal_token(tlv_type, length)
            tlvs.append(tlv)

            if tlv.type == T_KEYID:
                self.__keyid_tlv = tlv

            length_to_read -= length

        return tlvs

    def __parse_manifest(self, length_to_read):
        """
        MANIFEST := MANIFEST_LINKS_SECTION DATA_LINKS_SECTION
        MANIFEST_LINKS_SECTION := SECTION
        DATA_LINKS_SECTION := SECTION
        :param length_to_read:
        :return:
        """
        tlvs = []
        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}".format(length + 4, length_to_read))
            length_to_read -= 4
            section = self.__parse_manifest_section(length)
            section_tlv = CCNxTlv(tlv_type, length, section)
            tlvs.append(section_tlv)
            length_to_read -= length
        return tlvs

    def __parse_manifest_section(self, length_to_read):
        """
        A manifest section is defined by:
        SECTION := START_CHUNK LIST_OF_HASHES

        :param length_to_read:
        :return:
        """
        tlvs = []
        while length_to_read > 0:
            (tlv_type, length) = self.__read_type_length()
            if length + 4 > length_to_read:
                raise ValueError("length + 4 = {}, length_to_read = {}".format(length + 4, length_to_read))
            length_to_read -= 4
            tlv = self.__parse_terminal_token(tlv_type, length)
            tlvs.append(tlv)
            length_to_read -= length
        return tlvs

