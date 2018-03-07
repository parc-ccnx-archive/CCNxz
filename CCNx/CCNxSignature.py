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


import array
from Crypto.Hash.SHA256 import *
from Crypto.Signature import PKCS1_v1_5
#from Crypto.Signature import PKCS1_PSS

__author__ = 'mmosko'


class CCNxSignature(object):
    def __init__(self, key):
        self.__key = key
        self.__pubkey = CCNxSignature.__generate_pubkey(key)
        self.__keyid = CCNxSignature.__generate_keyid(self.__pubkey)

    @staticmethod
    def __generate_pubkey(key):
        pubkey_der = key.publickey().exportKey("DER")
        return array.array("B", pubkey_der)

    @staticmethod
    def __generate_keyid(pubkey):
        keyid_hash = SHA256Hash(pubkey)
        keyid = keyid_hash.digest()
        return array.array("B", keyid)

    @property
    def public_key_array(self):
        """
        Returns DER encoded public key.
        :return: array of bytes
        """
        return self.__pubkey

    @property
    def keyid_array(self):
        """
        The SHA256 hash of the DER encoded public key
        :return: array of bytes
        """
        return self.__keyid

    def sign(self, data):
        """

        :param data: an array or list of bytes
        :return: a signature array
        """
        hasher = SHA256Hash(data)
        signer = PKCS1_v1_5.new(self.__key)
        sig = signer.sign(hasher)
        sig_array = array.array("B", sig)
        return sig_array
