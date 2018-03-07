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

import Crypto.PublicKey.RSA as RSA

from CCNx.CCNxMessage import *


class TestCCNxMessage(unittest.TestCase):
    def setUp(self):
        pem_2048 = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAx3qY0TsmL0I7mTR93MMGTT7VI5mdqUGmKObKuQwvUp9kCVcN
2zqap0Vj8tBLjVdQPrFPvkrrlr8g4+N7Fppp4G47LOXIthl2A8OmCeF/Hy/nFmVP
xUUOV1k5gqnmGWuJS4pUDjYTVUB9uL6QBkpzxtvKnPUPRRcYUP2otSt6SrVGycMT
8VVA4w/ezwzQzuzP3YcyoTYSR+WdsWpP+spwSIgirwNi96F/NvS/6azl/B1a8lhg
xQUV1aQqaT+LEzYucw4IXw0frROLh97zeJsuXpcqIRgl8Q8+fqO+6o+NOWkI/eyD
XVnueW6Lk37sLTH9IZPDjr7SUdPFSATeOf2sUwIDAQABAoIBACMqIIBZ3fxcv6bd
Uwa0toqtdeNFtD5fHUx+iuQeGsWE5Zyj5QRti0/LcrgeMgNjjfjPRxBzop47aS/j
LRKp+9oddH8QrtYzHNPDDKUXRFKaHjGbgHl1F/cb+oBnNPHsPBK9+t1aeQQBT2he
54LEYy5+FnSe2qdCT/4PCUuOs4sxo6JQ2jZUff4GMuajfUKgVtlDn9YpQmi0lfFS
Hq3HM6vA/bMPLfIu9Q004h/kcGI0ze/XD+Lo8iIZY+ngfJZYw0hPzBPZECTQ312Q
MCicVnYolfJPpaKSBvNwHfYxJ6YV/+ln8W645AqGq+sXiy3Z1l6SHi2SAcmeFVco
UqsOYjkCgYEA9swO7OTN6N2v15sXyyFZVAEh7y+O4kYYMXykRB1JcImuLebDuUqD
n2mG+RHgadisL7ltZd9IUPhku4jAbpugaW4JYYN5aoYvJN1hvEH3Tfn2AI7Z6yN2
CL6HZtFKemjQdXZVVyeO8dQyuGXrPLRivMimEgj7SEpMMYe9L4xYfHUCgYEAzurV
+ixmRp1smAOTb/LlxVkd3aEXw3O+KcEPK5OhGNoz6SAntYXrhjuxMs4rXNBXtIxH
dF9N0bcfhjRFFt1aNxGrRuVj46TGkkPFZJOsePebgnPIqBXSQda7uSAA5QHihSO/
FYyU4WcyELIqIydrjeTZpTWLiT1x1yFoxOrTDKcCgYEA9AxPyhRsRhVKeJOmkLlW
o0pHa0YFLl6QOAeATNcFM2MCueNTspwr0mzBCvWRjDm186+SrcWBtoga3JPbbsU4
eGlWn3Yqj5tHbVX5+vbkfdhrWpvohKxZYUY/kP3vf2K8mRs+QuQcZ6klytEGMM5U
QUjNaFI3YoIOHICVJTrMma0CgYEAvj5sPnhUENjs31dqV6OcXrZxHzTeBHaGgR1g
NVCm7ZKx58YIvH1E70YyxeOJOuzTtszDZdu6UPdtpJaqbztVlwxHzgdasBLv/8sP
0kl0akQ+VtLdyq1FhANK1gr2x5fUDVWwer+moxeekHs/AtNbsDqZYay5fpVf9cxh
56uAIEECgYAMZiK4vPjJLBjD8pn6RS0J63mnPabkoJFH4msaIItL05WXb5d3ZrYH
OPWykjf6UQFHL7K+ZYruiIEXM5xRCe5vnZ6aupGT5ELun9etZRIQEnx9n4oNKRg5
tYhSUPb2R8yKyyWsKz0U1ZO9nSD+D9DWC+yrPGyXMdnvGC9Mmpaa/Q==
-----END RSA PRIVATE KEY-----"""
        self.key = RSA.importKey(pem_2048)
        self.signer = CCNxSignature(self.key)

    def test_sign(self):
        body_tlvs = [CCNxTlv(T_OBJECT, 12, None),
                     CCNxTlv(T_NAME, 8, None),
                     CCNxTlv(T_NAMESEG, 4, [0x62, 0x75, 0x7a, 0x7a])]
        co_test = CCNxMessage([], body_tlvs)
        co_test.sign(self.key)

        truth = [CCNxTlv(T_OBJECT, 12, None),
                 CCNxTlv(T_NAME, 8, None),
                 CCNxTlv(T_NAMESEG, 4, [0x62, 0x75, 0x7a, 0x7a]),
                 CCNxTlv(T_VALALG, 338, None),
                 CCNxTlv(T_RSA_SHA256, 334, None),
                 CCNxTlv(T_KEYID, 32, self.signer.keyid_array),
                 CCNxTlv(T_PUBKEY, len(self.signer.public_key_array), self.signer.public_key_array),
                 CCNxTlv(T_VALPAY, 256, [
                     131, 33, 29, 167, 110, 146, 120, 255, 59, 206, 222, 130, 65, 42, 181, 164, 4, 138, 233, 251, 169,
                     154, 178, 183, 40, 208, 31, 5, 236, 251, 44, 136, 254, 139, 1, 41, 104, 3, 90, 122, 90, 153, 36,
                     119, 197, 154, 185, 236, 228, 254, 0, 152, 37, 101, 217, 66, 197, 104, 234, 89, 225, 203, 247, 202,
                     153, 115, 108, 55, 222, 242, 229, 251, 19, 141, 106, 112, 189, 119, 38, 175, 69, 61, 121, 219, 6,
                     30, 12, 254, 194, 231, 115, 146, 169, 203, 61, 124, 128, 62, 75, 197, 165, 8, 247, 149, 193, 218,
                     67, 106, 118, 52, 93, 151, 205, 19, 102, 60, 213, 192, 40, 250, 56, 226, 0, 116, 231, 84, 118, 100,
                     82, 117, 35, 204, 165, 110, 7, 51, 187, 208, 193, 222, 206, 197, 219, 61, 238, 27, 40, 27, 206,
                     214, 251, 255, 167, 179, 115, 213, 205, 56, 37, 51, 123, 114, 97, 129, 232, 109, 161, 101, 61, 225,
                     91, 149, 147, 1, 21, 249, 138, 4, 128, 196, 89, 97, 17, 232, 56, 196, 117, 209, 13, 230, 136, 1,
                     250, 128, 138, 176, 10, 133, 33, 160, 205, 65, 37, 4, 51, 179, 185, 149, 201, 82, 67, 186, 1, 65,
                     248, 68, 15, 83, 73, 160, 70, 226, 7, 241, 224, 255, 109, 84, 252, 223, 34, 169, 166, 222, 101,
                     119, 47, 154, 209, 19, 132, 192, 97, 147, 134, 248, 177, 143, 116, 16, 83, 148, 25, 231, 202, 28])
                 ]
        co_truth = CCNxMessage([], truth)
        co_truth.generate_wireformat()
        self.assertTrue(co_test.wire_format == co_truth.wire_format)

    def test_content_object_hash(self):
        """
        Truth generated by writing out the wireformat (without fixed header and optional headers)
        and then running openssl on it:

        openssl dgst -sha256 -binary ./CCNxz/tests/x | xxd -i

        :return:
        """
        truth = [
            0x43, 0xb9, 0x75, 0x2b, 0x49, 0x31, 0xfc, 0x13, 0xa7, 0x14, 0xb1, 0x78,
            0xa5, 0xe0, 0xd1, 0xc4, 0xfa, 0xed, 0x10, 0x5e, 0x3a, 0x6a, 0x3f, 0x69,
            0xc5, 0x07, 0x2f, 0xd4, 0x05, 0x98, 0x57, 0x3c]
        truth_array = array.array("B", truth)

        # Header TLVs should be ignored in the hash
        header_tlv = [CCNxTlv(T_INTLIFE, 4, [0x4, 0x3, 0x2, 0x1])]
        body_tlvs = [CCNxTlv(T_OBJECT, 12, None),
                     CCNxTlv(T_NAME, 8, None),
                     CCNxTlv(T_NAMESEG, 4, [0x62, 0x75, 0x7a, 0x7a])]
        co = CCNxMessage(header_tlv, body_tlvs)
        co.generate_wireformat()

        test = co.hash()
        self.assertTrue(test == truth_array)

    def test_set_name(self):
        name_tlv = [CCNxTlv(T_NAME, 8, None), CCNxTlv(T_NAMESEG, 4, [0x62, 0x75, 0x7a, 0x7a])]
        body_tlvs = [CCNxTlv(T_OBJECT, 12, None)]
        body_tlvs.extend(name_tlv)

        co = CCNxMessage([], body_tlvs)
        co.name = name_tlv

        test = co.name
        self.assertTrue(test == name_tlv)


if __name__ == '__main__':
    unittest.main()
