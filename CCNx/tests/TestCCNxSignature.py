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

import unittest

from Crypto.PublicKey import RSA

from CCNx.CCNxSignature import *


class TestCCNxSignature(unittest.TestCase):
    def setUp(self):
        """
        Truth values take from openssl
        openssl genrsa 1024
        echo "One small step for man" > data
        openssl dgst -sign keys -sha256 data | xxd -i
        """
        pem = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDk680vyxYFEUfuNq8XBPXgvu2NbEn42wK/6V6LPLuiSdINXjRj
V3rA6QcNWAvNLxtOw68zt+Wk2OQIzFTtyhfx1gmXqM+pouY3nJzEh5J70X0ZkULz
9qVswu/Sz+e5a/4S7wWf727yv1eBPd83TjE4a/gOh28971OpVpOufXd9qwIDAQAB
AoGBAODYQlb5EA22JYJyL5Naie5PWaAYhqdo5dB9dSEpa9pAy5HZv3b7i1RDDWwr
2JuV8ypvxXv02hgJ+CA0Ig7U+qHv++c4jdKUY//3hhp8PQ8Bvnb1qnXKVXWHGESU
F/ZSt6K044qQ/wT1OI/53bE868sQCo/54vjlr1ms1yW+z/cBAkEA+/4PHdTXH3Ho
HXyhNq9LOzfOql+39BeqmewRp+/y7UgvN/xGRS8jvJWA0aRUllmHrTb3/u08F5NV
GXee8nhxawJBAOiPz9MwrKjT9MZkq3KVHb2hFkskcY+rPpk9GrFrSCyuT8ayblHJ
TUu0vM/a+srhXtnrMEVI4NrYK3c13oGw9MECQQDLfLtEQa197QOdXBjrCd7ccRJo
LmdjqwDOzvzq+i7XQaUvtn4gPBLFpIyjvem4h4+yZmMY7wXJm+XqbNhjwLMFAkEA
xqiqoD4xD5rXum2eYyfsGuOzNocwFsjylVY0KiB5q+lPLm2XfXfW9ney3l+x4oK4
UrDsMBM8ONV188RpiSHPQQJAEbadj+3K5aJ5p9GR32VBey4MV7IelzJF+g/FfbNF
un4lm0vl6Bqi2uBcdWX7IZtdotaeMPl8mXUx4+WRxM6rfA==
-----END RSA PRIVATE KEY-----"""
        self.data = "One small step for man"
        self.sig_bytes = [
            0x5a, 0x13, 0xfa, 0x60, 0x0c, 0x1d, 0x2d, 0xd5, 0x00, 0xde, 0xf4, 0x68,
            0x56, 0x8c, 0x6a, 0x51, 0xcd, 0x16, 0xcd, 0x45, 0x18, 0x19, 0x38, 0xe1,
            0xb1, 0x52, 0xe9, 0x3e, 0xdd, 0x04, 0xab, 0x59, 0xcf, 0x5d, 0x6a, 0x78,
            0xb5, 0x72, 0x8d, 0xc7, 0xcd, 0x6b, 0x37, 0x58, 0x9d, 0xd8, 0x6e, 0xa0,
            0x92, 0x97, 0x5f, 0x06, 0xad, 0x29, 0x73, 0x11, 0x1c, 0x5f, 0xb0, 0x14,
            0x85, 0xaa, 0xd1, 0x93, 0xae, 0x3f, 0x4a, 0xaa, 0xde, 0xc8, 0x88, 0xe8,
            0x1e, 0x3b, 0x7f, 0xe2, 0xb6, 0x5c, 0x67, 0x11, 0x4a, 0xdb, 0xda, 0x04,
            0x8a, 0x70, 0xef, 0x45, 0xb6, 0xa5, 0x3e, 0x75, 0x91, 0xe8, 0x9b, 0x87,
            0x69, 0x1a, 0x29, 0xf2, 0xda, 0x5f, 0xd9, 0x88, 0x94, 0xfa, 0x62, 0xda,
            0x6f, 0x70, 0x58, 0xc2, 0x1b, 0xfb, 0x20, 0x5c, 0xd1, 0x5b, 0x0d, 0xc2,
            0xd2, 0xf0, 0xaf, 0x7b, 0x64, 0x95, 0xb0, 0x5e]

        self.key = RSA.importKey(pem)
        self.sig_array = array.array("B", self.sig_bytes)

    def test_sign(self):
        signer = CCNxSignature(self.key)
        sig = signer.sign(self.data)
        self.assertTrue(sig == self.sig_array)

if __name__ == '__main__':
    unittest.main()
