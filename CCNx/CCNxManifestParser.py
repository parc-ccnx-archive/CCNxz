from CCNx.CCNxTypes import *
from CCNx.CCNxTlv import *

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


class CCNxManifestParser(object):
    def __init__(self,content_object):
        """
        Pass in a CCNxContentObject and create a CCNxManifest
        :param content_object:
        :return: A CCNxManifest based on the CCNxContentObject
        """
        self.__manifest_start_chunk = None
        self.__manifest_hash_list = []
        self.__data_start_chunk = None
        self.__data_hash_list = []

        if content_object.manifest is None:
            raise ValueError("The content object does not have a manifest section")

        for section in content_object.manifest:
            if section.type == T_MANIFEST_LINKS:
                self.__manifest_start_chunk, self.__manifest_hash_list = CCNxManifestParser.__parse_section(section)

            elif section.type == T_DATA_LINKS:
                self.__data_start_chunk, self.__data_hash_list = CCNxManifestParser.__parse_section(section)

    @staticmethod
    def __parse_section(section):
        hash_length = 32
        start_chunk = None
        hash_links = []

        for subsection in section.value:
            if subsection.type == T_START_CHUNK_NUMBER:
                start_chunk = CCNxTlv.array_to_number(subsection.value)

            elif subsection.type == T_HASH_LIST:
                for offset in range(0, subsection.length, hash_length):
                    hash = subsection.value[offset:offset + hash_length]
                    hash_links.append(hash)

        return start_chunk, hash_links

    @property
    def manifest_start_chunk(self):
        """starting chunk number for hashes in manifest section"""
        return self.__manifest_start_chunk

    @property
    def manifest_hash_list(self):
        return self.__manifest_hash_list

    @property
    def data_start_chunk(self):
        """Starting chunk number for hashes in data section"""
        return self.__data_start_chunk

    @property
    def data_hash_list(self):
        return self.__data_hash_list
