__author__ = 'mmosko'

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


# Packet Types
PT_INTEREST = 1
PT_OBJECT = 2

# Optional Headers
T_INTLIFE = 0x0001
T_INTFRAG = 0x0003
T_OBJFRAG = 0x0004

# CCNxMessage body
T_INTEREST = 0x0001
T_OBJECT = 0x0002
T_VALALG = 0x0003
T_VALPAY = 0x0004

# CCNxName
T_NAME = 0x0000
T_NAMESEG = 0x0001
T_CHUNK = 0x000A
T_IPID = 0x0008
T_SERIAL = 0x0013

# Body elements
T_KEYIDREST = 0x0002
T_OBJHASHREST = 0x0003
T_PLDTYPE = 0x0005
T_PAYLOAD = 0x0001
T_EXPIRY = 0x0006
T_ENDCHUNK = 0x0019

# ValidationAlg
T_KEYID = 0x0009
T_PUBKEY = 0x000B
T_CERT = 0x000C
T_KEYNAME = 0x000E
T_SIGTIME = 0x000F

T_CRC32C = 2
T_HMAC_SHA256 = 4
T_RSA_SHA256 = 6
T_ECSECP256K1 = 7

# Virtual field (outside normal range of 0x00000 - 0x0FFFF
T_FOOTER = 0x10000

T_MANIFEST = 7
T_MANIFEST_LINKS = 1
T_DATA_LINKS = 2
T_START_CHUNK_NUMBER = 1
T_HASH_LIST = 2
