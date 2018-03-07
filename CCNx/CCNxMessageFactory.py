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

import array

from CCNx.CCNxInterest import *
from CCNx.CCNxContentObject import *
from CCNx.CCNxName import *


class CCNxMessageFactory(object):
    @staticmethod
    def from_wire_format(wire_format):
        parser = CCNxParser(wire_format)
        parser.parse()

        keyid_restr = None
        if parser.keyid_restriction_tlv is not None:
            keyid_restr = array.array("B", parser.keyid_restriction_tlv.value)

        hash_restr = None
        if parser.hash_restriction_tlv is not None:
            hash_restr = array.array("B", parser.hash_restriction_tlv.value)

        linear = parser.linearize_body()
        if linear[0].type == T_INTEREST:
            message = CCNxInterest(name=CCNxNameFactory.from_tlv_list(parser.name_tlv.value),
                                   keyid_restr=keyid_restr, hash_restr=hash_restr)
        elif linear[0].type == T_OBJECT:
            name = CCNxNameFactory.from_tlv_list(parser.name_tlv.value)
            # convert linear which is a list to varargs with "*"
            message = CCNxContentObject(name, None, *linear)
            keyid = None
            if parser.keyid_tlv is not None:
                keyid = parser.keyid_tlv.value
            message.keyid = keyid

            manifest = None
            if parser.manifest_tlv is not None:
                manifest = parser.manifest_tlv.value
            message.manifest = manifest

            payload = None
            if parser.payload_tlv is not None:
                payload = parser.payload_tlv.value

            message.payload = payload

        else:
            raise ValueError("Unsupported message type: ", linear[0])
        return message
