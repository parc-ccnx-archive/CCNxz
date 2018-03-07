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


class CCNxContentObject(CCNxMessage):
    def __process_args(self, args):
        pass

    def __init__(self, name, expiry_time, *args):
        """

        :param name: A CCNxName
        :return: a CCNxInterest
        """
        length = name.length
        expiry_tlv = None

        if expiry_time is not None:
            expiry_array = CCNxTlv.number_to_array(expiry_time)
            expiry_tlv = CCNxTlv(T_EXPIRY, len(expiry_array), expiry_array)
            length += 4 + expiry_tlv.length

        for arg in args:
            if arg is not None:
                if type(arg) != CCNxTlv:
                    raise ValueError("arg {} is not a CCNxTlv".format(arg))
                length += 4
                if arg.value is not None:
                    length += arg.length

        co_tlv = CCNxTlv(T_OBJECT, length, None)
        body_tlvs = [co_tlv] + name.tlv_list()
        if expiry_tlv is not None:
            body_tlvs += [expiry_tlv]
        body_tlvs += [a for a in args if a is not None]

        super(CCNxContentObject,self).__init__([], body_tlvs)
        self.name = name

