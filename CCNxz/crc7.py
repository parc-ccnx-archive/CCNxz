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
crc-7 from RFC 4995

polynomial = 1 + x + x^2 + x^3 + x^6 + x^7

Simple implementation like a linear feedback shift register.

=== 6-bit coverage
tested 1 bits of error, ran 6 tests, 0 undetected
tested 2 bits of error, ran 15 tests, 0 undetected
tested 3 bits of error, ran 20 tests, 0 undetected
tested 4 bits of error, ran 15 tests, 0 undetected
tested 5 bits of error, ran 6 tests, 0 undetected
tested 6 bits of error, ran 1 tests, 0 undetected

For 10 bits
Number bit errors   Undetected count
    1                    0
    2                    0
    3                    0
    4                    2 / 210
    5                    0
    6                    4 / 210
    7                    0
    8                    1 / 45
    9                    0
    10                   0

polynomial = 1 + x + x^2 + x^4 + x^7
tested 1 bits of error, ran 10 tests, 0 undetected
tested 2 bits of error, ran 45 tests, 0 undetected
tested 3 bits of error, ran 120 tests, 0 undetected
tested 4 bits of error, ran 210 tests, 0 undetected
tested 5 bits of error, ran 252 tests, 3 undetected
tested 6 bits of error, ran 210 tests, 3 undetected
tested 7 bits of error, ran 120 tests, 1 undetected
tested 8 bits of error, ran 45 tests, 0 undetected
tested 9 bits of error, ran 10 tests, 0 undetected
tested 10 bits of error, ran 1 tests, 0 undetected

This is probably a better polynomial as it pushes the errors out to
a much higher error rate
polynomial = 1 + x + x^2 + x^4 + x^6 + x^7
tested 1 bits of error, ran 10 tests, 0 undetected
tested 2 bits of error, ran 45 tests, 0 undetected
tested 3 bits of error, ran 120 tests, 0 undetected
tested 4 bits of error, ran 210 tests, 1 undetected
tested 5 bits of error, ran 252 tests, 0 undetected
tested 6 bits of error, ran 210 tests, 6 undetected
tested 7 bits of error, ran 120 tests, 0 undetected
tested 8 bits of error, ran 45 tests, 0 undetected
tested 9 bits of error, ran 10 tests, 0 undetected
tested 10 bits of error, ran 1 tests, 0 undetected
"""

# __author__ = 'mmosko'

class CRC7(object):
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
        self.__crc = [1] * 7

    def update_bit(self, bit):
        inverted = bit ^ self.__crc[6]
        self.__crc[6] = self.__crc[5] ^ inverted
        self.__crc[5] = self.__crc[4]
        self.__crc[4] = self.__crc[3]
        self.__crc[3] = self.__crc[2] ^ inverted
        self.__crc[2] = self.__crc[1] ^ inverted
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
        output = self.__crc[6] << 6 | self.__crc[5] << 5 | self.__crc[4] << 4 |\
                 self.__crc[3] << 3 | self.__crc[2] << 2 | self.__crc[1] << 1 | \
                 self.__crc[0]
        return output

