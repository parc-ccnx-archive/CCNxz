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

from CCNx.CCNxMessage import *
from CCNx.CCNxTlv import *
from CCNx.CCNxTypes import *


class CCNxInterest(CCNxMessage):
    def __init__(self, name, keyid_restr=None, hash_restr=None):
        """

        :param name: A CCNxName
        :param keyid_restr: list or array of bytes
        :param hash_restr:  list or array of bytes
        :return: a CCNxInterest
        """
        length = name.length
        if keyid_restr is not None:
            keyid_tlv = CCNxTlv(T_KEYIDREST, len(keyid_restr), keyid_restr)
            length += 4 + keyid_tlv.length
        else:
            keyid_tlv = None

        if hash_restr is not None:
            hash_tlv = CCNxTlv(T_OBJHASHREST, len(hash_restr), hash_restr)
            length += 4 + hash_tlv.length
        else:
            hash_tlv = None

        interest_tlv = CCNxTlv(T_INTEREST, length, None)
        body_tlvs = [interest_tlv] + name.tlv_list()
        if keyid_tlv is not None:
            body_tlvs += [keyid_tlv]
        if hash_tlv is not None:
            body_tlvs += [hash_tlv]

        super(CCNxInterest,self).__init__([], body_tlvs)
        self.name = name
        self.__keyid_restr = keyid_restr
        self.__hash_restr = hash_restr

    @property
    def hash_restr(self):
        return self.__hash_restr

    @property
    def keyid_restr(self):
        return self.__keyid_restr

