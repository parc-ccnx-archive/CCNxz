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

import types

from CCNx.CCNxParser import *


class CCNxHuffmanToken(object):
    def __init__(self, token):
        self.__token = token
        self.__count = 0

    @property
    def token(self):
        return self.__token

    @property
    def count(self):
        return self.__count

    def incrementCount(self):
        self.__count += 1

class CCNxHuffman(object):
    def __init__(self):
        self.__tokens = {}

    def addToken(self, token):
        try:
            hufftoken = self.__tokens[token]
        except KeyError:
            hufftoken = CCNxHuffmanToken(token)
            self.__tokens[token] = hufftoken

        hufftoken.incrementCount()

        #print "token {} count {}".format(hufftoken.token, hufftoken.count)

    def addTlv(self, tlv):
        if (type(tlv) == CCNxTlv):
            tlvtype = tlv.type
            tlvlength = tlv.length
            self.addToken((tlvtype, tlvlength))
            self.addTlv(tlv.value)
        elif (type(tlv) == types.ListType):
            for x in tlv:
                self.addTlv(x)

    def addParsedPacket(self, parser):
        if (not isinstance(parser, CCNxParser)):
            raise TypeError("parser must be of type CCNxParser")

        body = parser.body
        for tlv in body:
            self.addTlv(tlv)

    def analyze(self):
        sortedlist = sorted(self.__tokens, key=lambda hufftoken: hufftoken.count)
        #print "Sorted: ", sortedlist


