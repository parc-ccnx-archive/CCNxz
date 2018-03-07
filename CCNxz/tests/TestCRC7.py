#!/usr/bin/pyton
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

from CCNxz.crc7 import *
import itertools

class TestCRC7(unittest.TestCase):
    def test_vectors(self):
        vectors = [
            {'input': [0xE1, 0x00, 0xCA, 0xFE], 'output': 0x0C},
            {'input': [0xC0, 0x03, 0xBE, 0xEF, 0x01, 0x02], 'output': 0x71}
        ]

        crc = CRC7()
        for v in vectors:
            crc.initialize()
            crc.update_bytes(v['input'])
            test = crc.finalize()
            #self.assertTrue(test == v['output'])

    def test_three_bit_errors(self):
        """
        For all 3-bit inputs, test bit error detection.

        0b10xxx

        bit positions from left
        If bit 0 is corrupted, will not even run the check, so don't do that one.
        If bit 1 is corrupted, it will look like a 0b110xxxxxxxxxx crc3, so don't do that one.

        This should so resilience to all 1, 2, or 3 bit errors
        """

        # generate all the error patterns up to 3 bit errors
        items = [0, 1]
        all_errors = itertools.product(items, repeat=3)
        errors = itertools.ifilter(lambda x: 0 < x.count(1) <= 3, all_errors)

        for i in range(0, 8):
            crc = CRC7()
            bit2 = i >> 2
            bit1 = (i & 0x02) >> 1
            bit0 = i & 0x01
            bits = [1, 0, bit2, bit1, bit0]

            for b in bits:
                crc.update_bit(b)

            truth = crc.finalize()

            for error in errors:
                corrupted = list(bits)
                for pos in range(0, 3):
                    corrupted[pos + 2] ^= error[pos]

                crc.initialize()
                for b in corrupted:
                    crc.update_bit(b)

                test = crc.finalize()

                self.assertTrue(test != truth, "error {}: truth {} != test {}".format(error, truth, test))

    def __run_one_test(self, errors, bit_length):
        test_size = 0
        error_count = 0
        for i in range(0, 1024):
            crc = CRC7()
            bits = [1, 1, 0]
            for j in range(0, bit_length):
                shift = bit_length - j - 1
                mask = 1 << shift
                bits.append((i & mask) >> shift)

            for b in bits:
                crc.update_bit(b)

            truth = crc.finalize()

            for error in errors:
                test_size += 1
                corrupted = list(bits)
                for pos in range(0, bit_length):
                    corrupted[pos + 2] ^= error[pos]

                crc.initialize()
                for b in corrupted:
                    crc.update_bit(b)

                test = crc.finalize()
                if test == truth:
                    error_count += 1

        return test_size, error_count

    def test_ten_bit_errors(self):
        """
        For all 3-bit inputs, test bit error detection.

        0b110xxxxxxxxxx

        Bit positions from left
        If bit 0 is corrupted, will not even run the check, so don't do that one.
        If bit 1 is corrupted, it will look like a 0b110xxxxxxxxxx crc3, so don't do that one.
        If bit 2 is corrupted, will look like reserved value, so don't do that.

        """
        print "=== 10-bit coverage"
        items = [0, 1]
        for i in range(0, 10):
            all_errors = itertools.product(items, repeat=10)
            errors = itertools.ifilter(lambda x: i < x.count(1) <= i + 1, all_errors)
            test_size, error_count = self.__run_one_test(errors, 10)
            print "tested {} bits of error, ran {} tests, {} undetected".format(i+1, test_size, error_count)

    def test_six_bit_errors(self):
        """
        For all 6-bit inputs, test bit error detection.

        0b110xxxxxx

        Bit positions from left
        If bit 0 is corrupted, will not even run the check, so don't do that one.
        If bit 1 is corrupted, it will look like a 0b110xxxxxxxxxx crc3, so don't do that one.
        If bit 2 is corrupted, will look like reserved value, so don't do that.

        """
        print "=== 6-bit coverage"
        items = [0, 1]
        for i in range(0, 6):
            all_errors = itertools.product(items, repeat=6)
            errors = itertools.ifilter(lambda x: i < x.count(1) <= i + 1, all_errors)
            test_size, error_count = self.__run_one_test(errors, 6)
            print "tested {} bits of error, ran {} tests, {} undetected".format(i+1, test_size, error_count)

if __name__ == "__main__":
    unittest.main()
