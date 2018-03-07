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

import struct
import types
import array

from CCNx.CCNxPacketType import *


class CCNxFixedHeader(object):
    def __init__(self, byte_array):
        if len(byte_array) < 8:
            raise ValueError("Byte array less than 8 bytes")

        if type(byte_array) == types.StringType:
            self.__unpack_string(byte_array)
        elif type(byte_array) == array.array:
            self.__unpack_list(byte_array)
        elif type(byte_array) == types.ListType:
            self.__unpack_list(byte_array)

        if self.version != 1:
            raise ValueError("Invalid version: ", self.version)

        if self.headerLength < 8:
            raise ValueError("Invalid headerLength: ", self.headerLength)

    def __str__(self):
        x = 'FH: ver = {}, type = {}, len = {}, hl = {}, resv = {}, hdrLen = {}'.format(self.version, self.packetType, self.packetLength, self.hopLimit, self.reserved, self.headerLength)
        return x

    @property
    def version(self):
        return self.__ver

    @property
    def packetType(self):
        return self.__packetType

    @property
    def packetLength(self):
        return self.__packetLength

    @property
    def hopLimit(self):
        return self.__hopLimit

    @property
    def headerLength(self):
        return self.__headerLength

    @property
    def reserved(self):
        return self.__reserved

    def pack(self):
        buffer = struct.pack("!BBHBHB", self.version, self.packetType.type, self.packetLength, self.hopLimit, self.reserved, self.headerLength)
        return buffer

    def byte_array(self):
        output = [self.version & 0x0F, self.packetType.type & 0xFF, self.packetLength >> 8, self.packetLength & 0x0FF,
                  self.hopLimit & 0xFF, self.reserved >> 8, self.reserved & 0xFF, self.headerLength & 0xFF]
        return output

    def __unpack_string(self, bytearray):
        (ver, packetType, packetLength, hopLimit, resv, headerLength) = struct.unpack_from("!BBHBHB", bytearray, 0)
        self.__ver = ver
        self.__packetType = CCNxPacketType(packetType)
        self.__packetLength = packetLength
        self.__hopLimit = hopLimit
        self.__reserved = resv
        self.__headerLength = headerLength

    def __unpack_list(self, bytearray):
        self.__ver = bytearray[0]
        self.__packetType = CCNxPacketType(bytearray[1])
        self.__packetLength = (bytearray[2] << 8) | bytearray[3]
        self.__hopLimit = bytearray[4]
        self.__reserved = (bytearray[5] << 8) | bytearray[6]
        self.__headerLength = bytearray[7]
