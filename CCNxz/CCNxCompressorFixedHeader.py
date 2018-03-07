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
v = version, t = packetType (PT), h = headerLen (HL),
l = packetLen (PL), m = hopLimit (HOP) c = return code (RC),
r = reserved, i = context ID (CID)
                                       BYTE HL  PL HOP RC PT
Uncompressed packet
000vvvvr t{8} l{16} m{8} c{8} r{8} h{8}   8  8  16   8  8  8

Compressed packet
10 i{3} crc{3} compressed_fh
110 i{6} crc{7} compressed_fh
111 reserved

001vvvvr t{8} l{16} m{8} c{8} r{8} h{8}   8  8  16   8  8  8
010vvvvt ttllllll m{8}                    3  0   6   8  0  3
011vvvvt tthhhhhl l{8}                    3  5   9   0  0  3
100vvvvt tthhhhhl l{8} m{8}               4  5   9   8  0  3
                                           green: full len

Version field reduced to 4 bits in all packets
PacketType greater than 7 must use 8-byte fixed header
"""

__author__ = 'mmosko'

from CCNx.CCNxFixedHeader import *
from CCNxCompressorContextID import *

#####################
# These bit lengths are used various places, define here
# to avoid having magic numbers all over

_bits_2 = 0x0003
_bits_3 = 0x0007
_bits_5 = 0x001F
_bits_6 = 0x003F
_bits_7 = 0x007F
_bits_8 = 0x00FF
_bits_9 = 0x01FF
_bits_14 = 0x3FFF
_bits_16 = 0xFFFF

#####################
#

_compressed_mask = 0x80
_compressed_bit = 0x80

_pattern_mask = 0xE0
_pattern_000 = 0x00
_pattern_h0_l6_m8 = 0x40
_pattern_h5_l9_m0 = 0x60
_pattern_h5_l9_m8 = 0x80
_pattern_h8_l16_m8 = 0x20


#####################

class CCNxCompressorFixedHeader(object):
    @staticmethod
    def compress(fh, context_id):
        """
        Compress the given fixed header.

        NOTE: This does not allow the 'natively compressed' form.

        :param fh:  The uncompressed fixed header
        :param context_id: The compression context ID to prepend to header
        :return: Byte string of the compressed fixed header
        """

        if type(fh) != CCNxFixedHeader:
            raise TypeError("fh must be CCNxFixedHeader")

        output = CCNxCompressorContextID.encode(context_id)
        output_fh = None
        if fh.packetType.type <= _bits_3 and fh.reserved == 0:
            if fh.headerLength == 8 and fh.packetLength <= _bits_6:
                output_fh = CCNxCompressorFixedHeader.__compress_h0_l6_m8(fh)
            elif fh.headerLength <= _bits_5 and fh.packetLength <= _bits_9 and fh.hopLimit == 0:
                output_fh = CCNxCompressorFixedHeader.__compress_h5_l9_m0(fh)
            elif fh.headerLength <= _bits_5 and fh.packetLength <= _bits_9:
                output_fh = CCNxCompressorFixedHeader.__compress_h5_l9_m8(fh)

        if output_fh is None:
            # Otherwise we cannot compress it, so just set the Compressed flag
            output_fh = CCNxCompressorFixedHeader.__compress_h8_l16_m8(fh)

        output.extend(output_fh)
        return output

    @staticmethod
    def decompress(byte_array):
        """
        Returns a list of decoded bytes

        :param byte_array: Input bytes, will pop decoded bytes off the array
        :return: A list of decoded bytes
        """

        if (byte_array[0] & _compressed_mask) != _compressed_bit:
            output = CCNxCompressorFixedHeader.__decompress_000(byte_array)
        else:
            # it is compressed
            context_id = CCNxCompressorContextID.decode(byte_array)

            # After removing context ID bytes, look for next pattern
            pattern = byte_array[0] & _pattern_mask

            if pattern == _pattern_h0_l6_m8:
                output = CCNxCompressorFixedHeader.__decompress_h0_l6_m8(byte_array)
            elif pattern == _pattern_h5_l9_m0:
                output = CCNxCompressorFixedHeader.__decompress_h5_l9_m0(byte_array)
            elif pattern == _pattern_h5_l9_m8:
                output = CCNxCompressorFixedHeader.__decompress_h5_l9_m8(byte_array)
            elif pattern == _pattern_h8_l16_m8:
                return CCNxCompressorFixedHeader.__decompress_h8_l16_m8(byte_array)
            else:
                raise ValueError("pattern not recognized: ", hex(pattern))

        return output

    ##############
    # private method

    @staticmethod
    def __fixed_header_list(version, packet_type, packet_length, hop_limit, header_length, reserved = 0):
        return [version, packet_type, packet_length >> 8, packet_length & 0xFF,
                hop_limit, reserved >> 8, reserved & 0xFF, header_length]


    @staticmethod
    def __uncompressed(fh):
       return CCNxCompressorFixedHeader.__fixed_header_list(fh.version, fh.packetType.type, fh.packetLength,
                                                            fh.hopLimit, fh.headerLength,
                                                            fh.reserved)

    @staticmethod
    def __compress_h8_l16_m8(fh):
        """
        100vvvvr t{8} l{16} m{8} c{8} r{8} h{8}   8  8  16   8  8  8

        This is the same as the uncompressed format, but with the "compressed" bit set.

        :param fh:
        :return:
        """
        packed = CCNxCompressorFixedHeader.__uncompressed(fh)
        packed[0] |= _pattern_h8_l16_m8
        return packed

    @staticmethod
    def __compress_h0_l6_m8(fh):
        """
        101vvvvt ttllllll m{8}                    3  0   6   8  0  3

        :param fh: Fixed Header to encode
        :return: list of bytes
        """
        byte0 = _pattern_h0_l6_m8 | (fh.version << 1) | (fh.packetType.type >> 2)
        byte1 = ((fh.packetType.type & _bits_2) << 6) | (fh.packetLength & _bits_6)
        byte2 = fh.hopLimit
        return [byte0, byte1, byte2]

    @staticmethod
    def __compress_h5_l9_m0(fh):
        """
        110vvvvt tthhhhhl l{8}                    3  5   9   0  0  3

        :param fh: Fixed Header to encode
        :return: list of bytes
        """
        byte0 = _pattern_h5_l9_m0 | (fh.version << 1) | (fh.packetType.type >> 2)
        byte1 = ((fh.packetType.type & _bits_3) << 6) | (fh.headerLength << 1) | (fh.packetLength >> 8)
        byte2 = fh.packetLength & 0xFF

        return [byte0, byte1, byte2]

    @staticmethod
    def __compress_h5_l9_m8(fh):
        """
        111vvvvt tthhhhhl l{8} m{8}               4  5   9   8  0  3

        :param fh: Fixed Header to encode
        :return: list of bytes
        """
        byte0 = _pattern_h5_l9_m8 | (fh.version << 1) | (fh.packetType.type >> 2)
        byte1 = ((fh.packetType.type & _bits_3) << 6) | (fh.headerLength << 1) | (fh.packetLength >> 8)
        byte2 = fh.packetLength & 0xFF
        byte3 = fh.hopLimit & 0xFF

        return [byte0, byte1, byte2, byte3]

    # *** Decompression

    @staticmethod
    def __decompress_000(byte_array):
        """
        000vvvvr t{8} l{16} m{8} c{8} r{8} h{8}   8  8  16   8  8  8

        :param byte_array: list of bytes to decode
        :return: list of bytes
        """
        output = [byte_array.pop(0), byte_array.pop(0), byte_array.pop(0), byte_array.pop(0),
                  byte_array.pop(0), byte_array.pop(0), byte_array.pop(0), byte_array.pop(0)]

        return output

    @staticmethod
    def __decompress_h8_l16_m8(byte_array):
        """
        100vvvvr t{8} l{16} m{8} c{8} r{8} h{8}   8  8  16   8  8  8

        :param byte_array: list of bytes to decode
        :return: list of bytes
        """
        output = CCNxCompressorFixedHeader.__decompress_000(byte_array)

        # Clear the compressed flag
        output[0] &= ~_pattern_h8_l16_m8

        return output

    @staticmethod
    def __decompress_h0_l6_m8(byte_array):
        """
        101vvvvt ttllllll m{8}                    3  0   6   8  0  3

        :param byte_array: list of bytes to decode
        :return: list of bytes of the decompressed header
        """
        byte0 = byte_array.pop(0) & ~_pattern_h0_l6_m8
        byte1 = byte_array.pop(0)
        byte2 = byte_array.pop(0)

        version = byte0 >> 1
        packet_type = (byte0 & 0x01) << 2 | (byte1 >> 6)
        packet_length = byte1 & 0x3F
        hop_limit = byte2

        return CCNxCompressorFixedHeader.__fixed_header_list(version, packet_type, packet_length, hop_limit, 8)

    @staticmethod
    def __decompress_h5_l9_m0(byte_array):
        """
        110vvvvt tthhhhhl l{8}                    3  5   9   0  0  3

        :param byte_array: list of bytes to decode
        :return: list of bytes
        """
        byte0 = byte_array.pop(0) & ~_pattern_h5_l9_m0
        byte1 = byte_array.pop(0)
        byte2 = byte_array.pop(0)

        version = byte0 >> 1
        packet_type = (byte0 & 0x01) << 2 | (byte1 >> 6)
        header_length = (byte1 & 0x3F) >> 1
        packet_length = (byte1 & 0x01) << 8 | byte2

        return CCNxCompressorFixedHeader.__fixed_header_list(version, packet_type, packet_length, 0, header_length)

    @staticmethod
    def __decompress_h5_l9_m8(byte_array):
        byte0 = byte_array.pop(0) & ~_pattern_h5_l9_m8
        byte1 = byte_array.pop(0)
        byte2 = byte_array.pop(0)
        byte3 = byte_array.pop(0)

        version = (byte0 & 0x1E) >> 1
        packet_type = (byte0 & 0x01) << 2 | (byte1 >> 6)
        header_length = (byte1 & 0x3F) >> 1
        packet_length = (byte1 & 0x01) << 8 | byte2
        hop_limit = byte3

        return CCNxCompressorFixedHeader.__fixed_header_list(version, packet_type, packet_length, hop_limit,
                                                             header_length)
