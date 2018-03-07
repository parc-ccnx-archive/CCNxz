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

from CCNxz.CCNxNullCompressor import *

from CCNx.CCNxSignature import *

__author__ = 'mmosko'


class CCNxMessage(object):
    """
    A CCNxMessage is defined as a list of header CCNxTlvs and a a set of body CCNxTlvs.
    One can also optionally set the name via the name setter.

    Example:
        name_apple = CCNxNameFactory.from_uri("lci:/apple")
        co_apple = CCNxMessage([], [CCNxTlv(T_OBJECT, 4 + name_apple.length, None)] + name_apple.tlv_list())
        co_apple.name = name_apple
        co_apple.generate_wireformat()
    """
    def __init__(self, header_tlv_list, body_tlv_list):
        """
        A linearized list is a list or array of CCNxTlv where container
        TLVs have a positive length and a value of None.  They are not nested.

        :param header_tlv_list: a linearlized list of CCNxTlv
        :param body_tlv_list:  a linearlized list of CCNxTlv
        :return:
        """
        for thing in header_tlv_list:
            if type(thing) != CCNxTlv:
                raise ValueError("element {} in header_tlv_list is not a CCNxTlv".format(thing))
        for thing in body_tlv_list:
            if type(thing) != CCNxTlv:
                raise ValueError("element {} in body_tlv_list is not a CCNxTlv".format(thing))

        # make our own copies of the lists.  We'll be appending to them
        self.__header_tlvs = header_tlv_list
        self.__body_tlvs = body_tlv_list
        self.__wire_format = None
        self.__header_length = None
        self.__name = None
        self.__keyid = None
        self.__manifest = None
        self.__payload = None

    def __str__(self):
        return "MSG(name={}, headers={}, body={} manifest={})".format(self.__name, self.__header_tlvs,
                                                                      self.__body_tlvs, self.__manifest)

    def __eq__(self, other):
        """Equality is based on the wire format"""
        return self.wire_format == other.wire_format

    def generate_wireformat(self):
        # pass a copy of the list, this function is destructive
        headers = CCNxNullCompressor.encode_tlv_list(list(self.__header_tlvs))
        body = CCNxNullCompressor.encode_tlv_list(list(self.__body_tlvs))

        if self.__body_tlvs[0].type == T_INTEREST:
            packet_type = PT_INTEREST
        elif self.__body_tlvs[0].type == T_OBJECT:
            packet_type = PT_OBJECT
        else:
            raise ValueError("Unsupported message type: ", self.__body_tlvs[0])

        self.__header_length = 8 + len(headers)
        packet_len = self.__header_length + len(body)
        byte_list = [1, packet_type, packet_len >> 8, packet_len & 0xFF,
                    0, 0, 0, self.__header_length]
        byte_list.extend(headers)
        byte_list.extend(body)
        self.__wire_format = array.array("B", byte_list)

    def sign(self, key):
        if self.__wire_format is None:
            self.generate_wireformat()

        signer = CCNxSignature(key)
        pubkey_array = signer.public_key_array
        keyid_array = signer.keyid_array

        # Create the TLVs
        keyid_tlv = CCNxTlv(T_KEYID, len(keyid_array), keyid_array)
        pubkey_tlv = CCNxTlv(T_PUBKEY, len(pubkey_array), pubkey_array)
        length = 4 + keyid_tlv.length + 4 + pubkey_tlv.length
        rsa_sha256_tlv = CCNxTlv(T_RSA_SHA256, length, None)
        valalg_tlv = CCNxTlv(T_VALALG, length + 4, None)

        valalg_list = [valalg_tlv, rsa_sha256_tlv, keyid_tlv, pubkey_tlv]
        self.__body_tlvs.extend(valalg_list)

        bytes = CCNxNullCompressor.encode_tlv_list(valalg_list)
        self.__wire_format.extend(bytes)

        # Sign the body
        sig_start = self.__header_length
        sig_array = signer.sign(self.__wire_format[sig_start:])
        sig_tlv = CCNxTlv(T_VALPAY, len(sig_array), sig_array)
        valpay_tlvs = [sig_tlv]
        self.__body_tlvs.append(sig_tlv)

        bytes = CCNxNullCompressor.encode_tlv_list(valpay_tlvs)
        self.__wire_format.extend(bytes)

        # update the PacketLength
        length = len(self.__wire_format)
        self.__wire_format[2] = length >> 8
        self.__wire_format[3] = length & 0xFF

        self.__keyid = keyid_array

    def hash(self):
        """
        The Message Hash for use as a hash restriction
        Should should sign the object first.

        :return: An array of bytes of the SHA256 hash
        """
        if self.__wire_format is None:
            self.generate_wireformat()

        hasher = SHA256Hash(self.wire_format[self.__header_length:])
        hash = hasher.digest()
        return array.array("B", hash)

    @property
    def wire_format(self):
        if self.__wire_format is None:
            self.generate_wireformat()
        return self.__wire_format

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        """
        The name property is only an annotation on the object.  It is not
        part of the wire_format.  You need to include the name in the body_tlv list
        passed to the message when it is created.

        Example:
            name_apple = CCNxNameFactory.from_uri("lci:/apple")
            co_apple = CCNxMessage([], [CCNxTlv(T_OBJECT, 4 + name_apple.length, None)] + name_apple.tlv_list())
            co_apple.name = name_apple
            co_apple.generate_wireformat()

        :param name: A CCNxName
        :return:
        """
        self.__name = name

    @property
    def keyid(self):
        """
        The keyid array for the key used by sign()
        :return: An array of bytes
        """
        return self.__keyid

    @keyid.setter
    def keyid(self, keyid):
        self.__keyid = keyid

    @property
    def manifest(self):
        """
        Returns the manifest, if one exists.  It must be explicitly set by
        calling the manifest setter.  This is done by the CCNxParser when it
        parses a ContentObject.

        :return:
        """
        return self.__manifest

    @manifest.setter
    def manifest(self, manifest):
        self.__manifest = manifest

    @property
    def payload(self):
        return self.__payload

    @payload.setter
    def payload(self, payload):
        self.__payload = payload
