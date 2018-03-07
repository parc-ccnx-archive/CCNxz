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

from crc3 import *
from crc7 import *

_cid_3_3_mask = 0xC0
_cid_3_3_pattern = 0x80
_cid_3_3_max = 7

_cid_6_7_mask = 0xE0
_cid_6_7_pattern = 0xC0
_cid_6_7_max = 63

_bits_3 = 0x07
_bits_7 = 0x7F


class CCNxCompressorContextID(object):
    @staticmethod
    def encode(context_id):
        """
        Encode the context ID in to a byte list

        :param context_id:
        :return: list of bytes
        """
        if context_id <= _cid_3_3_max:
            byte0 = _cid_3_3_pattern | (context_id << 3)
            crc = CRC3()
            crc.update_byte(byte0)
            crc_output = crc.finalize()
            byte0 |= crc_output
            output = [byte0]
        elif context_id <= _cid_6_7_max:
            byte0 = _cid_6_7_pattern | (context_id >> 1)
            byte1 = (context_id & 0x01) << 7
            crc = CRC7()
            crc.update_byte(byte0)
            crc.update_byte(byte1)
            crc_output = crc.finalize()
            byte1 |= crc_output
            output = [byte0, byte1]
        else:
            raise ValueError("context_id {} too large, max {}".format(context_id, _cid_6_7_max))
        return output

    @staticmethod
    def decode(byte_array):
        """
        pops bytes off the byte_array to decode the context ID.

        :param byte_array: A list or array or similar of bytes
        :return:
        :raises ValueError: If the first byte is not a valid context id
        """
        output = None
        byte0 = byte_array.pop(0)
        if (byte0 & _cid_3_3_mask) == _cid_3_3_pattern:
            # Save the packets CRC then clear those bits to 0
            packet_crc = byte0 & _bits_3
            byte0 &= ~_bits_3

            crc = CRC3()
            crc.update_byte(byte0)
            calculated_crc = crc.finalize()

            if calculated_crc == packet_crc:
                # extract the context_id and return it as integer
                output = (byte0 & ~_cid_3_3_mask) >> 3
            else:
                print "Calculated crc {} does not match packet crc {}".format(hex(calculated_crc), hex(packet_crc))

        elif (byte0 & _cid_6_7_mask) == _cid_6_7_pattern:
            byte1 = byte_array.pop(0)
            # extract the crc from the packet and zero those bits
            packet_crc = byte1 & _bits_7
            byte1 &= ~_bits_7

            crc = CRC7()
            crc.update_byte(byte0)
            crc.update_byte(byte1)

            calculated_crc = crc.finalize()

            if calculated_crc == packet_crc:
                # extract the context_id and return it as integer
                output = ((byte0 & ~_cid_6_7_mask) << 1) | (byte1 >> 7)
            else:
                print "Calculated crc {} does not match packet crc {}".format(hex(calculated_crc), hex(packet_crc))

        else:
            raise ValueError("Byte0 {} is not recognized pattern".format(hex(byte0)))

        return output
