# CCNxz
Compressed CCNx uses TLV-aware compression to reduce the overhead of TL encoding.
It also learns common TLV tuples (like keyid or public keys) and compresses them.

This is experimental code related to a compressed TLV encoding.  Please see this
presentation for more information about the compression scheme.

https://datatracker.ietf.org/meeting/interim-2016-icnrg-02/materials/slides-interim-2016-icnrg-2-7

# TXT to Binary
    xxd -r -g 1 -c 8 infile outfile

## Examples: 

    xxd -r -g 1 -c 8 examples/tiny_interest.txt tiny_interest.bin
    ./ccnxz.py tiny_interest.bin
    xxd -g 1 -c 8 compressed
	
	
# Simple Testing
The ccnxz.py script will run the (de)compressor on a file. The input file should be one packet
in wire format.  The output will be the (de)compressed wireformat.

    ./ccnxz [-d] input output

-d means to decompress input to output

# Live testing

    Client A -- [Metis A --] ccnxz_relay A -- ccnxz_channel -- ccnxz_relay B [-- Metis B] -- Client B

- Clients A and B are CCNx applications of your choice.  We include a simple traffic generator.
- Metis is the standard CCNx forwarder.  It needs to run in UDP mode.  If your
  client applications speak UDP directly, then Metis is not needed.
- ccnxz_relay is a UDP relay to (de)compress CCNx packets
- ccnxz_channel is a channel emulator to add bit error rate and delay.
  It is optional.

ccnxz_relay is configured with a local port and the UDP socket addresses of its
two peers.  Lets assume everything is going to run on localhost, and we'll skip
Metis for now and assume client A and B speak UDP directly.

* Client A (or Metis A): port 10000
* ccnxz_relay A: port 10001
* ccnxz_channel: port 10002
* ccnxz_relay B: port 10003
* Client B (or Metis B): port 10004

## Example
You would then use these commands:

    # make a 100 MB file.bin, you could substitute other files here
    mkdir files
    dd if=/dev/random of=files/file.bin bs=1000000 count=100
    
    # Start a server, relay chain, channel emulator, and client
    ccnxz_gen     -p 10000 --server --prefix lci:/ccnxz --directory files
    ccnxz_relay   -p 10001 --peers 127.0.0.1:10000 127.0.0.1:10002
    ccnxz_channel -p 10002 --peers 127.0.0.1:10001 127.0.0.1:10003 --ber 10E-4 --delay 0.1
    ccnxz_relay   -p 10003 --peers 127.0.0.1:10002 127.0.0.1:10004
    ccnxz_gen     -p 10004 --client --name lci:/ccnxz/files/file.bins --peer 127.0.0.1:10003

Then start up your two applications on port 10000 and 10004.
