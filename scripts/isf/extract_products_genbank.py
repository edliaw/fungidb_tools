#!/usr/bin/env python
"""Extracts product names from genbank files.

2012/09/10
Edward Liaw
"""
import sys
import argparse
from warnings import warn
from Bio import SeqIO


def extract_products(infile):
    """Extract product names.

    Args:
        infile: A filestream to read from.
    """
    for record in SeqIO.parse(infile, 'genbank'):
        for feature in record.features:
            # Extract information from mRNA features.
            if feature.type == 'mRNA':
                locus = feature.qualifiers['locus_tag']
                product = feature.qualifiers['product']
                if len(locus) > 1:
                    warn("Locus has more than one element {}".format(locus))
                elif len(product) > 1:
                    warn("Product has more than one element {}".format(product))
                yield '; '.join(locus), '; '.join(product)


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
        for locus, product in extract_products(infile):
            outfile.write('\t'.join((locus, product)) + '\n')


if __name__ == "__main__":
    main()
