#!/usr/bin/python

# Implemented from RFC2118 and licensed as a code component
#
# Copyright (c) 1997 IETF Trust and the persons identified as authors of the code.  All rights reserved.
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


# Implements the Microsoft Point-to-Point Compression (MPPC) protocol
# RFC 2118
#
# __author__ = 'mmosko'
#
# #######
# History size:
#    8192 bytes
#
# Packet format
#
#    0                   1                   2                   3
#    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#   |         PPP Protocol          |A|B|C|D| Coherency Count       |
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#   |        Compressed Data...
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
# A Bit : history initialize
# B Bit: Set history pointer to front of buffer
# C Bit: Packet is compressed (1)
# D Bit: unused (must be 0)
#
# Coherency counter:
#   monotonically increasing counter with wrap-around to 0
#
# Unlike RFC 2118 we do not include the Protocol field at the start
# of the compressed data, we just begin with the CCNx packet.
#
########
# Because we are not running inside PPP, we will use this packet format:
#
#    0                   1                   2                   3
#    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#   |A|B|C|      zeros (13)         |        Coherency Count        |
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#   |        Compressed Data...
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
# N.B.:
#   If the output becomes larger than the input, the program currently
#   crashes with something like:
#       File "./mppc.py", line 159, in __encode7bitLiteral
#         self.__out[byte_offset+1] |= lowerbyte
#     IndexError: array index out of range
#

import array
import binascii
import struct
import sys

class MCCP(object):
    # Used as bit patterns in Offset Encoding (RFC Sec 4.2.1)
    __offset_pattern_64 = 0b1111
    __offset_pattern_320 = 0b1110
    __offset_pattern_8191 = 0b110

    __length_pattern_3    = 0b0
    __length_pattern_8    = 0b10
    __length_pattern_16   = 0b110
    __length_pattern_32   = 0b1110
    __length_pattern_64   = 0b11110
    __length_pattern_128  = 0b111110
    __length_pattern_256  = 0b1111110
    __length_pattern_512  = 0b11111110
    __length_pattern_1024 = 0b111111110
    __length_pattern_2048 = 0b1111111110
    __length_pattern_4096 = 0b11111111110
    __length_pattern_8192 = 0b111111111110

    def __init__(self, data):
        self.__in = data
        self.__inByteOffset = 0
        self.__out = array.array('B')
        self.__overflowLength = 20
        self.__outLength = len(data) + self.__overflowLength
        self.__out.fromlist([0] * self.__outLength)
        self.__outBitOffset = 0
        self.__historyLength = 8196
        self.__history = array.array('B')
        self.__history.fromlist([0] * self.__historyLength)
        self.__historyOffset = 0

    def __findLongestHistory(self):
        '''
            Begining at __inByteOffset, find the longest substring in the
            history that matches it.

            This is an inefficient implementation as it does a linear scan.

            Because the minimum length encoding is 3, we do not match
            any substrings less than 3 bytes long.

            :return: (offset, length) or None
        '''

        istring = self.__in[self.__inByteOffset:]
        longestLen = 0
        longestOffset = 0

        hstr = self.__history.tostring()
        for iLen in range(3, 1 + len(istring)):
            idx = hstr.find(istring[0:iLen])
            if idx > -1:
                # substrings match, so possible hit
                if iLen > longestLen:
                    longestLen = iLen
                    longestOffset = idx
            else:
                # sustrings no longer match, give up on this historyOffset
                # breaks out of iLen loop
                break

        if longestLen > 0:
            print "Found longest match (off = {}, len = {})".format(longestOffset, longestLen)
            return (longestOffset, longestLen)
        else:
            return (None, None)

    def __getOutputByte(self):
        return self.__outBitOffset / 8

    def __getOutpuBit(self):
        return self.__outBitOffset % 8

    def __incrementHistoryOffset(self):
        self.__historyOffset = (self.__historyOffset + 1) % self.__historyLength

    def __pushByteToHistory(self, byte):
        self.__history[self.__historyOffset] = byte
        self.__incrementHistoryOffset()

    def __encode7bitLiteral(self, byte):
        if byte >= 0x80:
            raise ValueError("Byte must be less than 0x80, got: ", hex(byte))

        byte_offset = self.__getOutputByte()
        bit_offset = self.__getOutpuBit()

        if bit_offset == 0:
            self.__out[byte_offset] = byte
        else:
            # example:
            #   memory: ab00.0000.0000.0000
            #   bitoffset = 2
            #   data = defg.hijk
            #
            #   upperbyte = defghi
            #   memory: abde.fghi.0000.0000
            #
            #   lowerbyte = jk00.0000
            #   memory: abde.fghi.jk00.0000

            upperbyte = byte >> bit_offset
            self.__out[byte_offset] |= upperbyte

            mask = (1 << bit_offset) - 1
            shift = 8 - bit_offset
            lowerbyte = (byte & mask) << shift
            self.__out[byte_offset+1] |= lowerbyte

            #print "wrote {}".format(hex(upperbyte << 8 | lowerbyte))

        self.__outBitOffset += 8

    def __encodeLiteral(self):
        byte = ord(self.__in[self.__inByteOffset])
        self.__inByteOffset += 1

        if byte < 0x80:
            self.__encode7bitLiteral(byte)
        else:
            # We need to write a "1" bit, then write the
            # byte as a 7-bit literal

            byte_offset = self.__getOutputByte()
            bit_offset = self.__getOutpuBit()

            upperbyte = 1 << (7 - bit_offset)
            self.__out[byte_offset] |= upperbyte
            self.__outBitOffset += 1

            self.__encode7bitLiteral(byte & 0x7F)

        self.__pushByteToHistory(byte)

    def __encodebits(self, bits, bit_length):
        bit_offset = self.__getOutpuBit()

        available_bits = 8 - bit_offset
        if bit_length <= available_bits:
            # we can fit the whole thing, shift the bits
            # up so we pack the top of the byte first
            shift = available_bits - bit_length
            x = bits << shift

            byte_offset = self.__getOutputByte()
            self.__out[byte_offset] |= x
            self.__outBitOffset += bit_length

        else:
            # grab 'available_bits' from the top
            shift = bit_length - available_bits
            x = bits >> shift
            self.__encodebits(x, available_bits)

            bit_length -= available_bits
            mask = (1 << bit_length) - 1
            bits &= mask
            self.__encodebits(bits, bit_length)


    def __encodeTupleOffset(self, offset):
        if offset < 64:
            # Encoded as '1111' plus lower 6 bits
            self.__encodebits(MCCP.__offset_pattern_64, 4)
            self.__encodebits(offset, 6)

        elif offset < 320:
            # Encoded as '1110' plus lower 8 bits of (value - 64)
            self.__encodebits(MCCP.__offset_pattern_320, 4)
            self.__encodebits(offset - 64, 8)

        else:
            # Encoded as '110' followed by lower 13 bits of (value - 320)
            self.__encodebits(MCCP.__offset_pattern_8191, 3)
            self.__encodebits(offset - 320, 13)

    def __encodeTupleLength(self, length):
        if length == 3:
            self.__encodebits(MCCP.__length_pattern_3, 1)
        elif length < 8:
            self.__encodebits(MCCP.__length_pattern_8, 2)
            self.__encodebits(length & 0x0003, 2)
        elif length < 16:
            self.__encodebits(MCCP.__length_pattern_16, 3)
            self.__encodebits(length & 0x0007, 3)
        elif length < 32:
            self.__encodebits(MCCP.__length_pattern_32, 4)
            self.__encodebits(length & 0x000F, 4)
        elif length < 64:
            self.__encodebits(MCCP.__length_pattern_64, 5)
            self.__encodebits(length & 0x001F, 5)
        elif length < 128:
            self.__encodebits(MCCP.__length_pattern_128, 6)
            self.__encodebits(length & 0x003F, 6)
        elif length < 256:
            self.__encodebits(MCCP.__length_pattern_256, 7)
            self.__encodebits(length & 0x007F, 7)
        elif length < 512:
            self.__encodebits(MCCP.__length_pattern_512, 8)
            self.__encodebits(length & 0x00FF, 8)
        elif length < 1024:
            self.__encodebits(MCCP.__length_pattern_1024, 9)
            self.__encodebits(length & 0x01FF, 9)
        elif length < 2048:
            self.__encodebits(MCCP.__length_pattern_2048, 10)
            self.__encodebits(length & 0x03FF, 10)
        elif length < 4096:
            self.__encodebits(MCCP.__length_pattern_4096, 11)
            self.__encodebits(length & 0x07FF, 11)
        else:
            self.__encodebits(MCCP.__length_pattern_8192, 12)
            self.__encodebits(length & 0x0FFF, 12)

    def __encodeCopyTuple(self, offset, length):
        self.__encodeTupleOffset(offset)
        self.__encodeTupleLength(length)

        endOffset = self.__inByteOffset + length
        while self.__inByteOffset < endOffset:
            byte = ord(self.__in[self.__inByteOffset])
            self.__pushByteToHistory(byte)
            self.__inByteOffset += 1


    def __addHeader(self, counter):
        A = 0x1000
        B = 0x0000
        C = 0x0000

        struct.pack_into("!HH", self.__out, 0, A | B | C, counter)
        self.__outBitOffset = 32

    def __trimOutputBuffer(self):
        # Trim down to nearest byte

        # Include +1 because we need the length to include the last byte
        last_byte = self.__getOutputByte() + 1
        last_bit = self.__getOutpuBit()
        if last_bit == 0:
            # If the last bit offset is 0, we have not written to the last byte
            last_byte -= 1

        print "last_byte = {}, len = {}".format(last_byte, len(self.__out))
        while len(self.__out) > last_byte:
            self.__out.pop()

    @property
    def history(self):
        return self.__history

    def compress(self):
        self.__addHeader(0)
        while self.__inByteOffset < len(self.__in):
            (longestOffset, longestLen) = self.__findLongestHistory()
#            (longestOffset, longestLen) = (None, None)
            if longestOffset is None:
                self.__encodeLiteral()
            else:
                self.__encodeCopyTuple(longestOffset, longestLen)

        self.__trimOutputBuffer()
        return self.__out


if len(sys.argv) != 2:
    data = "for whom the bell tolls, the bell tolls for thee.\xA6\x80"
    comp = MCCP(data)
    out = comp.compress()

    print "Input len %d Output len %d, ratio %f" % (len(data), len(out), len(out) / len(data))
    print "output:   ",binascii.hexlify(out)
    print "history:  ",binascii.hexlify(comp.history)

    expected = "10000000666f722077686f6d207468652062656c6c20746f6c6c732cf23720f023c9329749a000"
    if binascii.hexlify(out) != expected:
        print "expected: ", expected

else:
    fh = open(sys.argv[1], "rb")
    data = fh.read(65536)
    comp = MCCP(data)
    out = comp.compress()

    fhout = open("compressed.mccp", "wb")
    fhout.write(out)

    print "Input len %d Output len %d, ratio %f" % (len(data), len(out), len(out) / len(data))

    fhout.close()
    fh.close()