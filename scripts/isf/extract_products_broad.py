#!/usr/bin/env python2.7
"""Extract columns from a tab-separated summary file.

2012/10/01
Edward Liaw
"""
from __future__ import print_function
import sys
import argparse

SAVE_COLS = ('LOCUS', 'NAME')


def read_input(infile):
    """Read input.

    Args:
        infile: A filestream to read from.
    """
    pass


def mark_columns(header):
    marked = []
    spline = header.rstrip('\n').split('\t')
    for i, col in enumerate(spline):
        for save in SAVE_COLS:
            if col == save:
                marked.append(i)
    return marked


def write_output(outfile):
    """Write output.

    Args:
        outfile: A filestream to write to.
    """
    pass


def parse_arguments():
    """Handle command-line arguments.

    Returns:
        args: Arguments passed in from the command-line."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     fromfile_prefix_chars='@')
    parser.add_argument('infile',
                        type=argparse.FileType('r'), nargs='?',
                        default=sys.stdin, help='input file')
    parser.add_argument('outfile',
                        type=argparse.FileType('w'), nargs='?',
                        default=sys.stdout, help='output file')
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Handle I/O.
    with args.infile as infile, args.outfile as outfile:
        marked = mark_columns(next(infile))
        for line in infile:
            outstr = []
            spline = line.rstrip('\n').split('\t')
            for mark in marked:
                outstr.append(spline[mark])
            print('\t'.join(outstr), file=outfile)


if __name__ == "__main__":
    main()
