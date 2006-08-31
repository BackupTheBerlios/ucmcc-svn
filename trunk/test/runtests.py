#!/usr/bin/env python

# Run regression test suite

# Miki Tebeka <mtebeka@qualcomm.com>

from os import popen,getcwd
from glob import glob
from sys import executable

import re
count_re = re.compile("Ran\s+(\d+)\s+tests in .*")

def test_count(line):
    matches = count_re.findall(line)
    if not matches:
        return 0
    return int(matches[0])

def main(argv=None):
    if argv is None:
        import sys
        argv = sys.argv

    from optparse import OptionParser
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-q", "--quiet", help="be quiet",
            dest="quiet", action="store_true", default=0)
    parser.add_option("-v", "--verbose", help="be verbose",
            dest="quiet", action="store_false", default=0)

    opts, args = parser.parse_args()
    if args:
        parser.error("wrong number of arguments") # Will exit

    if opts.quiet:
        verbose = ""
    else:
        verbose = "-v"

    count = 0
    failed = []
    all_tests = glob("test_*.py")
    print getcwd()
    for test in all_tests:
        print "=== %s ===" % test
        pipe = popen("%s %s %s 2>&1" % (executable, test, verbose))
        for line in pipe:
            print line.rstrip()
            count += test_count(line)
        if pipe.close():
            failed.append(test)

    print
    print "Ran Total of %d tests (%d test functions)" % \
            (len(all_tests), count)
    if failed:
        print "%d test(s) failed:" % len(failed)
        for test in failed:
            print "\t%s" % test
        return 0
    
    print "We're cool"
    return 1

if __name__ == "__main__":
    if not main():
        raise SystemExit(1)
