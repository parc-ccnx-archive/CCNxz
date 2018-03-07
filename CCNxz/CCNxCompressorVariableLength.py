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
Compressor for fields with a variable length value.

This module is written in the old function style.  Should update it to look more like the
CCNxCompressorFixedLength module.

Compressed Formats: ("1xx" fixed header)
0zzzllll                            ( 3-bit Z &  4-bit L)
110zzzzl l{8}                       ( 4-bit Z &  9-bit L)
1110tttt t{8} tttlllll              (15-bit T &  4-bit L)
111110tt t{8} ttttttll l{8}         (16-bit T & 10-bit L)
11111111 t{16} l{16}                (16-bit T & 16-bit L)
"""

__author__ = 'mmosko'

from CCNx.CCNxTlv import *

class VariableLengthEntry(object):
    def __init__(self, tlv_type, pattern, key):
        self.__type = tlv_type
        self.__pattern = pattern
        self.__key = key

    def __eq__(self, other):
        return self.__type == other.__type and self.__pattern == other.__pattern and self.__key == other.__key

    def __str__(self):
        return "VLE [ type {}, pattern {}, key {} ]" % {self.__type, self.__pattern, bin(self.__key)}

    @property
    def type(self):
        return self.__type

    @property
    def pattern(self):
        return self.__pattern

    @property
    def key(self):
        return self.__key

    @property
    def compressor_key(self):
        return self.__type, self.__pattern

    @property
    def decompressor_key(self):
        return self.__key


_pattern_3_4 = 0x00
_pattern_4_9 = 0xC0
_pattern_15_5 = 0xE0
_pattern_16_10 = 0xF8
_pattern_16_16 = 0xFF

_mask_3_4 = 0x80
_mask_4_9 = 0xE0
_mask_15_5 = 0xF0
_mask_16_10 = 0xFC
_mask_16_16 = 0xFF

_length_3_4 = 0x0010
_length_4_9 = 0x0200
_length_15_5 = 0x0020
_length_16_10 = 0x0400
_length_16_16 = 0x10000

_type_bits_15_5 = 0x8000


def _generate_variable_length_entries():
    vles = [
        VariableLengthEntry(0x0000, _pattern_3_4, 0x00),
        VariableLengthEntry(0x0001, _pattern_3_4, 0x10),
        VariableLengthEntry(0x0002, _pattern_3_4, 0x20),
        VariableLengthEntry(0x000A, _pattern_3_4, 0x30),
        VariableLengthEntry(0x0013, _pattern_3_4, 0x40),
        VariableLengthEntry(0x0000, _pattern_4_9, 0xC0),
        VariableLengthEntry(0x0001, _pattern_4_9, 0xC2),
        VariableLengthEntry(0x0002, _pattern_4_9, 0xC4),
        VariableLengthEntry(0x0003, _pattern_4_9, 0xC6),
        VariableLengthEntry(0x0004, _pattern_4_9, 0xC8),
        VariableLengthEntry(0x0005, _pattern_4_9, 0xCA),
        VariableLengthEntry(0x0006, _pattern_4_9, 0xCC),
        VariableLengthEntry(0xF000, _pattern_4_9, 0xCE),
        VariableLengthEntry(0xF001, _pattern_4_9, 0xD0)]
    return vles


def _generate_compression_dictionary(vles):
    output = {}
    for vle in vles:
        output[vle.compressor_key] = vle
    return output


def _generate_decompression_dictionary(vles):
    output = {}
    for vle in vles:
        output[vle.decompressor_key] = vle
    return output


class CCNxCompressorVariableLength(object):
    _vles = _generate_variable_length_entries()
    _compression_dict = _generate_compression_dictionary(_vles)
    _decompression_dict = _generate_decompression_dictionary(_vles)

    # ###### PUBLIC API

    @staticmethod
    def decompress(byte_array):
        """
        Decompress a TL pair

        :param byte_array: The input byte stream
        :return: A list of bytes or None
        """
        byte0 = byte_array[0]
        decoded = None
        if (byte0 & _mask_3_4) == _pattern_3_4:
            decoded = CCNxCompressorVariableLength.__decompress_3_4(byte_array)
        elif (byte0 & _mask_4_9) == _pattern_4_9:
            decoded = CCNxCompressorVariableLength.__decompress_4_9(byte_array)
        elif (byte0 & _mask_15_5) == _pattern_15_5:
            decoded = CCNxCompressorVariableLength.__decompress_15_5(byte_array)
        elif (byte0 & _mask_16_10) == _pattern_16_10:
            decoded = CCNxCompressorVariableLength.__decompress_16_10(byte_array)
        elif (byte0 & _mask_16_16) == _pattern_16_16:
            decoded = CCNxCompressorVariableLength.__decompress_16_16(byte_array)

        return decoded

    @staticmethod
    def compress(tlv):
        """
        Perform a dictionary substitution on the T and encode the L
        with the smallest available bits

        :param tlv:
        :return:
        """
        if not type(tlv) == CCNxTlv:
            raise TypeError("tlv must be CCNxTlv")

        encoded = None
        if tlv.length < _length_3_4:
            vle = CCNxCompressorVariableLength.__find_pattern(tlv, _pattern_3_4)
            if vle is not None:
                encoded = CCNxCompressorVariableLength.__compress_pattern_3_4(tlv, vle)

        if encoded is None and tlv.length < _length_4_9:
            vle = CCNxCompressorVariableLength.__find_pattern(tlv, _pattern_4_9)
            if vle is not None:
                encoded = CCNxCompressorVariableLength.__compress_pattern_4_9(tlv, vle)

        return encoded

    @staticmethod
    def compact(tlv):
        """
        Encode the TLV with the smallest T and L sizes available.  No
        dictionary substitution is done.

        Will encode as (15,5) in 3 bytes, (16,10) in 4 bytes, or (16,16) in 5 bytes.

        :param tlv:
        :return:
        """
        if tlv.length < _length_15_5 and tlv.type < _type_bits_15_5:
            encoded = CCNxCompressorVariableLength.__compact_pattern_15_5(tlv)
        elif tlv.length < _length_16_10:
            encoded = CCNxCompressorVariableLength.__compact_pattern_16_10(tlv)
        else:
            encoded = CCNxCompressorVariableLength.__compact_pattern_16_16(tlv)
        return encoded

    # ##### Private API

    # #### Compression

    @staticmethod
    def __find_pattern(tlv, pattern):
        try:
            lookup_key = (tlv.type, pattern)
            vle = CCNxCompressorVariableLength._compression_dict[lookup_key]
            return vle

        except KeyError:
            return None

    @staticmethod
    def __compress_pattern_3_4(tlv, vle):
        if not tlv.length < _length_3_4:
            raise ValueError("tlv length must be less than {}: {}" % {_length_3_4, tlv.length})

        byte = vle.key | tlv.length
        return [byte]

    @staticmethod
    def __compress_pattern_4_9(tlv, vle):
        if not tlv.length < _length_4_9:
            raise ValueError("tlv length must be less than {}: {}" % {_length_4_9, tlv.length})

        word = (vle.key << 8) | tlv.length
        return [word >> 8, word & 0xFF]

    @staticmethod
    def __compact_pattern_15_5(tlv):
        if not tlv.length < _length_15_5:
            raise ValueError("tlv length must be less than {}: {}" % {_length_15_5, tlv.length})

        byte0 = _pattern_15_5 | tlv.type >> 11
        byte1 = (tlv.type & 0x07FF) >> 3
        byte2 = ((tlv.type & 0x7) << 5) | tlv.length
        return [byte0, byte1, byte2]

    @staticmethod
    def __compact_pattern_16_10(tlv):
        if not tlv.length < _length_16_10:
            raise ValueError("tlv length must be less than {}: {}" % {_length_16_10, tlv.length})

        byte0 = _pattern_16_10 | tlv.type >> 14
        byte1 = (tlv.type & 0x3FFF) >> 6
        byte2 = ((tlv.type & 0x3F) << 2) | (tlv.length >> 8)
        byte3 = tlv.length & 0xFF
        return [byte0, byte1, byte2, byte3]

    @staticmethod
    def __compact_pattern_16_16(tlv):
        if not tlv.length < _length_16_16:
            raise ValueError("tlv length must be less than {}: {}" % {_length_16_16, tlv.length})

        byte0 = _pattern_16_16
        byte1 = tlv.type >> 8
        byte2 = tlv.type & 0xFF
        byte3 = tlv.length >> 8
        byte4 = tlv.length & 0xFF
        return [byte0, byte1, byte2, byte3, byte4]

    # #### Decompression
    @staticmethod
    def __decompress_3_4(byte_array):
        output = None
        byte0 = byte_array[0]
        key = byte0 & 0xF0
        try:
            vle = CCNxCompressorVariableLength._decompression_dict[key]
            length = byte0 & 0x0F

            output = [vle.type >> 8, vle.type & 0xFF, length >> 8, length & 0xFF]

            byte_array.pop(0)

        except KeyError:
            pass

        return output

    @staticmethod
    def __decompress_4_9(byte_array):
        output = None
        byte0 = byte_array[0]
        key = byte0 & 0xFE
        try:
            vle = CCNxCompressorVariableLength._decompression_dict[key]

            byte_array.pop(0)
            byte1 = byte_array.pop(0)

            length_upper = byte0 & 0x01
            length_lower = byte1

            output = [vle.type >> 8, vle.type & 0xFF, length_upper, length_lower]

        except KeyError:
            pass

        return output

    @staticmethod
    def __decompress_15_5(byte_array):
        byte0 = byte_array.pop(0)
        byte1 = byte_array.pop(0)
        byte2 = byte_array.pop(0)

        tlv_type_0 = ((byte0 & 0x0F) << 3) | (byte1 >> 5)
        tlv_type_1 = ((byte1 & 0x1F) << 3) | (byte2 >> 5)
        tlv_length_0 = 0
        tlv_length_1 = byte2 & 0x1F

        return [tlv_type_0, tlv_type_1, tlv_length_0, tlv_length_1]

    @staticmethod
    def __decompress_16_10(byte_array):
        byte0 = byte_array.pop(0)
        byte1 = byte_array.pop(0)
        byte2 = byte_array.pop(0)
        byte3 = byte_array.pop(0)

        tlv_type_0 = ((byte0 & 0x03) << 6) | (byte1 >> 2)
        tlv_type_1 = ((byte1 & 0x03) << 6) | (byte2 >> 2)
        tlv_length_0 = byte2 & 0x03
        tlv_length_1 = byte3

        return [tlv_type_0, tlv_type_1, tlv_length_0, tlv_length_1]

    @staticmethod
    def __decompress_16_16(byte_array):
        byte_array.pop(0)
        output = [byte_array.pop(0), byte_array.pop(0), byte_array.pop(0), byte_array.pop(0)]

        return output
