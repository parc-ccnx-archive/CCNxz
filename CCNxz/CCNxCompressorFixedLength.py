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


from CCNxTrie import *
from CCNxTrieWalker import *

import struct
import array


class Tuple(object):
    """
    Tuple class represents a fixed length dictionary entry.  It associates a
    token_string with a compressed_key.  It also says how may bytes (the fixed length L)
    should be following the token_string or compressed_key (it should be the same
    as the last 2 bytes of the token_string).
    """

    def __init__(self, token_string, compressed_key, value_length):
        """
        :param token_string: The byte string to try and match
        :param compressed_key: The byte to replace token_string with
        :param value_length: The number of 'value' bytes that will immediately follow token_string
        """
        
        self.__token_string = token_string
        self.__compressed_key = compressed_key
        self.__value_length = value_length
        
    @property
    def token_string(self):
        return self.__token_string
    
    @property
    def compressed_key(self):
        return self.__compressed_key
    
    @property
    def value_length(self):
        return self.__value_length


def _generate_tuples():
    """
    Create all the (token_string, compressor_key) tuples
    These are used later to build the token->key trie and the key->token dictionary

    :return: A list of Tuples
    """
    tuples = [
        Tuple([0x00, 0x02, 0x00, 0x00], 0x80, 0x0000),
        Tuple([0x00, 0x02, 0x00, 0x04], 0x81, 0x0004),
        Tuple([0x00, 0x02, 0x00, 0x20], 0x82, 0x0020),
        Tuple([0x00, 0x03, 0x00, 0x04], 0x83, 0x0004),
        Tuple([0x00, 0x03, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0x04, 0x00, 0x04], 0x84, 0x0004),
        Tuple([0x00, 0x03, 0x00, 0x0C], 0x85, 0x000C),
        Tuple([0x00, 0x03, 0x00, 0x0C, 0x00, 0x04, 0x00, 0x08, 0x00, 0x09, 0x00, 0x04], 0x86, 0x0004),
        Tuple([0x00, 0x03, 0x00, 0x12], 0x87, 0x0012),
        Tuple([0x00, 0x03, 0x00, 0x14, 0x00, 0x04, 0x00, 0x10, 0x00, 0x09, 0x00, 0x04], 0x88, 0x0004),
        Tuple([0x00, 0x03, 0x00, 0x20], 0x89, 0x0020),
        Tuple([0x00, 0x03, 0x00, 0x34, 0x00, 0x06, 0x00, 0x30, 0x00, 0x09, 0x00, 0x20], 0x8A, 0x0020),
        Tuple([0x00, 0x03, 0x00, 0xCE, 0x00, 0x06, 0x00, 0xCA, 0x00, 0x09, 0x00, 0x20], 0x9C, 0x0020),
        Tuple([0x00, 0x04, 0x00, 0x04], 0x8B, 0x0004),
        Tuple([0x00, 0x04, 0x00, 0x0E], 0x8C, 0x000E),
        Tuple([0x00, 0x04, 0x00, 0x10], 0x8D, 0x0010),
        Tuple([0x00, 0x04, 0x00, 0x14], 0x8E, 0x0014),
        Tuple([0x00, 0x05, 0x00, 0x01], 0x8F, 0x0001),
        Tuple([0x00, 0x06, 0x00, 0x08], 0x90, 0x0008),
        Tuple([0x00, 0x08, 0x00, 0x11], 0x91, 0x0011),
        Tuple([0x00, 0x09, 0x00, 0x04], 0x92, 0x0004),
        Tuple([0x00, 0x09, 0x00, 0x10], 0x93, 0x0010),
        Tuple([0x00, 0x09, 0x00, 0x20], 0x94, 0x0020),
        Tuple([0x00, 0x0B, 0x00, 0xA2], 0x95, 0x00A2),
        Tuple([0x00, 0x0B, 0x01, 0x26], 0x96, 0x0126),
        Tuple([0x00, 0x0B, 0x02, 0x26], 0x97, 0x0226),
        Tuple([0x00, 0x0F, 0x00, 0x08], 0x98, 0x0008),
        Tuple([0x00, 0x19, 0x00, 0x01], 0x99, 0x0001),
        Tuple([0x00, 0x19, 0x00, 0x02], 0x9A, 0x0002),
        Tuple([0x00, 0x19, 0x00, 0x04], 0x9B, 0x0004)
    ]

    return tuples


def _generate_trie(tuples):
    trie = CCNxTrie()

    for p in tuples:
        trie.insert(p.token_string, p.compressed_key)

    return trie


def _generate_keys(tuples):
    keys = {}

    for tuple in tuples:
        keys[tuple.compressed_key] = tuple

    return keys

class CCNxCompressorFixedLength(object):
    """
    Implements the fixed length static dictionary.

    (t = type bit, l = length bit, z = compressor key)

    Uncompressed Format: ('000' fixed header)
    t{16} l{16}                         (16-bit T & 16-bit L)

    Compressed Formats: ('1xx' fixed header)
    0zzzllll                            ( 3-bit Z &  4-bit L)
    10zzzzzz                            ( 6-bit Z &  fixed L)
    110zzzzl l{8}                       ( 4-bit Z &  9-bit L)
    1110tttt t{8} tttlllll              (15-bit T &  4-bit L)
    111110tt t{8} ttttttll l{8}         (16-bit T & 10-bit L)
    11111111 t{16} l{16}                (16-bit T & 16-bit L)

    11110zzz z{8}                       (learned, next slide)
    1111110z z{16}                      (learned, next slide)
    11111110 z{24}                      (learned, next slide)

    Formats with a 't' encode dictionary misses.
    Formats with a 'z' encode dictionary hits.
    """

    __tuples = _generate_tuples()
    __trie = _generate_trie(__tuples)
    __keys = _generate_keys(__tuples)

    def __init__(self):
        self.__walker = CCNxTrieWalker(self.__trie)
        self.__last_match = None

    @staticmethod
    def isFixedLengthToken(type):
        masked = type & 0b11000000
        if masked == 0b10000000:
            return True
        return False

    def compress(self, tlv_list):
        """
        Make the longest match from tlv_list and return the compressed token.

        :param tlv:
        :return:
        """
        self.__walker.reset()

        to_encode = []

        finished = False
        list_offset = 0
        while not finished:
            tlv = tlv_list[list_offset]
            packed = [tlv.type >> 8, tlv.type & 0xFF, tlv.length >> 8, tlv.length & 0xFF]
            for byte in packed:
                result = self.__walker.next(byte)
                if result == CCNxTrieWalker.NoMatch:
                    finished = True
                    break

            if not finished:
                list_offset += 1

                # We had a hit on the (TL) pair in the trie
                compressed_key = self.__walker.value()
                if compressed_key is not None:
                    # this is a potential longest match
                    for j in range(0, list_offset):
                        # pop off everything up to this point
                        tlv_list.pop(0)

                    # we've not poped off the consumed entries, so go back to
                    # the front of the list
                    list_offset = 0
                    to_encode.append([tlv, compressed_key])

                    # If this TLV has a Value, we stop here
                    if tlv.length > 0 and tlv.value is not None:
                        finished = True

                else:
                    # there's no compression key, so keep going so long as
                    # the current TLV does not have a value.  Otherwise, wre're finished
                    if tlv.length > 0 and tlv.value is not None:
                        finished = True

        if len(to_encode) > 0:
            # write out whatever we got.  We only write out the terminal token

            [tlv, compress_key] = to_encode.pop()
            encoded = [compress_key]
            if tlv.value is not None:
                encoded.extend(tlv.value)
            return encoded

        return None

    @staticmethod
    def decompress(byte_array):
        """
        Decompress one or more TL pairs.  Will consume bytes from byte_array that are decoded.

        :param byte_array: The input byte stream
        :return: A list of bytes or None
        """

        output = None
        byte0 = byte_array[0]
        if CCNxCompressorFixedLength.isFixedLengthToken(byte0):
            try:
                tuple = CCNxCompressorFixedLength.__keys[byte0]
                output = tuple.token_string
                byte_array.pop(0)

            except KeyError:
                pass

        return output
