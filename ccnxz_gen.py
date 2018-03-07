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

"""
A simple client/server pair for sending test traffic.  Uses UDP.

    # make a 100 MB file.bin, you could substitute other files here
    mkdir files
    dd if=/dev/random of=files/file.bin bs=1000000 count=100

    # Start a server, relay chain, channel emulator, and client
    ccnxz_gen     -p 10000 --server --prefix lci:/ccnxz --directory files
    ccnxz_gen     -p 10004 --client --name lci:/ccnxz/files/file.bins --peer 127.0.0.1:10000

NOTE:
- This module require 'pycrypto' (e.g. pip install --user pycrypto)

"""

import argparse
import textwrap
import os

from Crypto.PublicKey import RSA

from CCNx.CCNxManifestTree import *
from CCNxz.CCNxzGenServer import CCNxzGenServer
from CCNxz.CCNxzGenClient import CCNxzGenClient


# __author__ = 'mmosko'

chunk_size = 1500


def _run_client(args):
    print "Running client"
    client = CCNxzGenClient(args)
    client.loop()


def _add_manifest_tree(objects_by_name, objects_by_hash, manifest):
    co = manifest.get_content_object()
    objects_by_name[co.name] = co
    objects_by_hash[co.hash] = co

    for child in manifest.data_links():
        objects_by_name[child.name] = child
        objects_by_hash[child.hash.tostring()] = child

    for child in manifest.manifest_links():
        _add_manifest_tree(objects_by_name, objects_by_hash, child)


def _run_server(args):
    print "Running server"

    fh = open(args.key, "r")
    key = RSA.importKey(fh.read())
    fh.close()

    files = []
    for dirname, dirnames, filenames in os.walk(args.dir):
        for f in filenames:
            path = os.path.join(dirname, f)
            files.append(path)

    print "list of files = ", files

    objects_by_name = {}
    objects_by_hash = {}

    for file_name in files:
        uri = args.prefix + "/" + file_name
        print 'uri = ', uri
        fh = open(file_name, 'rb')
        data = fh.read()
        tree = CCNxManifestTree(uri, data, chunk_size, key)
        root_manifest = tree.create_tree()

        _add_manifest_tree(objects_by_name, objects_by_hash, root_manifest)

    server = CCNxzGenServer(args, key, objects_by_name, objects_by_hash)
    server.loop()


def _parse_args():
    """
    command line: ccnxz_gen server -p PORT --prefix PREFIX --dir DIR --key KEY
    command line: ccnxz_gen client -p PORT --name NAME --peer PEER --pubkey PUBKEY
    command line: -h
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='A UDP client/server traffic generator',
        epilog=textwrap.dedent('''\
            The server side will generate a Manifest and chunked content objects
            for files in a specified directory.  The client will retrieve the
            given file name.

            You must generate a keypair, such as with these commands.  The server
            needs the private key "key" and the client needs the public key "pubkey".
            Only RSA supported at this time.
                openssl genrsa -out key 2048
                openssl rsa -in key -pubout -out pubkey'''))

    sub_parsers = parser.add_subparsers(dest='mode', help="sub-command help")

    server_parser = sub_parsers.add_parser("server", help="Content server")
    server_parser.add_argument('-p', required=True, dest='port', type=int, action='store', help='listen port')
    server_parser.add_argument('--prefix', required=True, dest='prefix', help='The content prefix')
    server_parser.add_argument('--dir', required=True, dest='dir', help='The directory to serve')
    server_parser.add_argument('--key', required=True, dest='key', help='The private signing key (DER or PEM)')

    client_parser = sub_parsers.add_parser("client", help="Content client")
    client_parser.add_argument('-p', required=True, dest='port', type=int, action='store', help='listen port')
    client_parser.add_argument('--name', required=True, dest='name', help='The content name')
    client_parser.add_argument('--peer', required=True, dest='peer', help='The client nexthop (host:port)')
    client_parser.add_argument('--pubkey', required=True, dest='pubkey', help='The servers public key (DER or PEM)')

    args = parser.parse_args()
    return args


def _run_main():
    args = _parse_args()
    print args

    if args.mode == 'client':
        _run_client(args)
    elif args.mode == 'server':
        _run_server(args)
    else:
        print "Unsupported mode: ", args.mode
        exit(1)


if __name__ == "__main__":
    _run_main()

