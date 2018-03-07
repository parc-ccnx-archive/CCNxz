#!/usr/bin/python

# Implemented from RFC4995 and licensed as a code component
#
# Copyright (c) 2007 IETF Trust and the persons identified as authors of the code.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# .  Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#
# .  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# .  Neither the name of Internet Society, IETF or IETF Trust, nor the names of specific contributors, may be used
#    to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
crc-3 from RFC 4995

polynomial = 1 + x + x^3

For 10 bits
Number bit errors   Undetected count
    1                    0
    2                    0
    3                    0
    4                    29 / 210
    5                    27 / 252
    6                    25 / 210
    7                    17 / 120
    8                    6 / 45
    9                    1 / 10
    10                   0

"""

# __author__ = 'mmosko'


class CRC3(object):
    def __init__(self):
        self.__crc = []
        self.initialize()

    @staticmethod
    def _bit_position(bit):
        return bit % 8

    @staticmethod
    def _byte_position(bit):
        return bit / 8

    def initialize(self):
        """
        Set the crc to the initial state.  RFC 4995 initializes the CRC to all 1's.

        :return:
        """
        self.__crc = [1, 1, 1]

    def update_bit(self, bit):
        inverted = bit ^ self.__crc[2]
        self.__crc[2] = self.__crc[1]
        self.__crc[1] = self.__crc[0] ^ inverted
        self.__crc[0] = inverted

    def update_byte(self, byte):
        for pos in range(0, 8):
            shift = 7 - pos
            mask = 1 << shift
            input_bit = (byte & mask) >> shift
            self.update_bit(input_bit)

    def update_bytes(self, list):
        """
        Given a list of bytes, calculate the CRC3 over them.

        :param list: Input octet sequence
        :return: CRC3 as 1 byte -- only bottom 3 bits matter
        """

        for pos in range(0, len(list)):
            self.update_byte(list[pos])

    def finalize(self):
        output = self.__crc[2] << 2 | self.__crc[1] << 1 | self.__crc[0]
        return output

