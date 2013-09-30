#!/usr/bin/env python2.7
"""Extract columns from a tab-separated summary file.

2012/10/01
Edward Liaw
"""
from __future__ import print_function
import sys
import argparse


def mark_tsv_columns(header, save):
    spline = header.rstrip('\n').split('\t')
    headers = {col: i for (i, col) in enumerate(spline)}
    return [headers[s] for s in save]


def extract_tsv_columns(infile, save):
    for line in infile:
        spline = line.rstrip('\n').split('\t')
        yield '\t'.join(spline[s] for s in save)


def parse_broad(infile):
    columns = ['LOCUS', 'NAME']
    save = mark_tsv_columns(next(infile), columns)
    for line in extract_tsv_columns(infile, save):
        yield line


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
        for line in parse_broad(infile):
            outfile.write(line + '\n')


if __name__ == "__main__":
    main()
