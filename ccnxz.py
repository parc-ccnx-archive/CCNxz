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

# __author__ = 'mmosko'

import sys
import os
import array

import CCNxz

def usage():
    print "usgae: ccnxz.py infile outfile"
    print "usgae: ccnxz.py -d infile outfile"
    print ""
    print "-d: decompress infile to outfile"
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

print "argv 1 = '{}'".format(sys.argv[1])
print "argv 2 = '{}'".format(sys.argv[2])

if sys.argv[1] == '-d':
    if len(sys.argv) != 4:
        usage()

    decompress = True
    infile = sys.argv[2]
    outfile = sys.argv[3]
else:
    if len(sys.argv) != 3:
        usage()
    decompress = False
    infile = sys.argv[1]
    outfile = sys.argv[2]


fh = open(infile,"rb")

file_length = os.path.getsize(infile)
a = array.array("B")
a.fromfile(fh, file_length)

packet = CCNxz.CCNxParser(a)
packet.parse()

if decompress:
    encoded = []
    encoded.extend([ord(b) for b in packet.fixed_header.pack()])
    for tlv in packet.linearize_body():
        encoded.extend([tlv.type >> 8, tlv.type & 0xFF, tlv.length >> 8, tlv.length & 0xFF])
        if tlv.length > 0 and tlv.value is not None:
            encoded.extend(tlv.value)

    output = array.array("B")
    output.fromlist(encoded)
    print "Decompressed to {} bytes".format(len(output))

else:
    comp = CCNxz.CCNxCompressor(packet)
    comp.encode()
    output = array.array("B")
    output.fromlist(comp.encoded)
    print "Compressed to {} bytes".format(len(comp.encoded))

fhout = open(outfile, "wb")
fhout.write(output)

fh.close()
fhout.close()


