"""Reformat a data file for ISF.

2013/04/11
Edward Liaw
"""
from __future__ import print_function
import re
import sys
import argparse
from warnings import warn
from . import roman


RE_DEFAULT = r'(?P<species>\w+)_(?P<type>Chr|SC)(?:(?P<number>\d+)|(?P<letter>[A-Z]+))'
NUMBER_FORMAT = '{{number:0{padding:d}d}}'
CONTIG_FORMAT = '{species}_{type}{contig}'


def init_argparse():
    parser = argparse.ArgumentParser(description=__doc__,
                                     fromfile_prefix_chars='@')
    parser.add_argument('infile',
                        type=argparse.FileType('r'), nargs='?',
                        default=sys.stdin, help='input file')
    parser.add_argument('outfile',
                        type=argparse.FileType('w'), nargs='?',
                        default=sys.stdout, help='output file')
    parser.add_argument('-r', '--regex',
                        default=RE_DEFAULT,
                        help='regular expression for the contig names')
    parser.add_argument('-s', '--species',
                        help='replacement text for species')
    parser.add_argument('-t', '--type',
                        help='replacement text for type')
    parser.add_argument('-m', '--mito',
                        help='output mitochondrial contigs')
    parser.add_argument('-p', '--padding',
                        type=int, default=2,
                        help='number of digits to pad')
    parser.add_argument('--roman',
                        action='store_true',
                        help='chromosomes enumerated by roman numerals')
    return parser


def parse_arguments():
    """Handle command-line arguments.

    Returns:
        args: Arguments passed in from the command-line.
    """
    parser = init_argparse()
    return parser.parse_args()


def _do_nothing(*args, **kwargs):
    return None


class NoMatchException(Exception):
    pass


class ContigFormatter(object):
    """Configurable formatter to rename contigs.  Improve this later.
    """
    def __init__(self, regex, number_format, contig_format=CONTIG_FORMAT,
                 species=None, type=None, roman=None):
        self.regex = re.compile(regex)
        self.number_format = number_format
        self.contig_format = contig_format
        terms = {}
        if species is not None:
            terms['species'] = species
        if type is not None:
            terms['type'] = type
        self.terms = terms
        if not roman:
            self.convert_roman = _do_nothing

    @classmethod
    def from_args(cls, args):
        number_format = NUMBER_FORMAT.format(padding=args.padding)
        return cls(number_format=number_format, species=args.species,
                   regex=args.regex, type=args.type, roman=args.roman)

    def convert_roman(self, terms):
        terms['number'] = roman.roman_to_int(terms['letter'])

    def remap_terms(self, terms):
        for term, default in self.terms.items():
            terms[term] = default
        self.convert_roman(terms)
        if terms.get('number'):
            terms['contig'] = self.number_format.format(number=int(terms['number']))
        elif terms.get('letter'):
            terms['contig'] = terms['letter'].upper()
        else:
            raise NoMatchException()

    def format(self, line):
        """ContigFormatter.format generates a formatted contig name from a
        dictionary of terms.

        Raises NoMatchException if no number or letter identifier is present
        for that contig.
        """
        match = self.regex.match(line)
        terms = match.groupdict()
        self.remap_terms(terms)
        return self.contig_format.format(**terms)


def main():
    args = parse_arguments()
    formatter = ContigFormatter.from_args(args)

    with args.infile as infile, args.outfile as outfile:
        for line in infile:
            try:
                print(formatter.format(line), file=outfile)
            except NoMatchException:
                warn("SKIPPED: re fails to match component of {line}".format(line=line))
                continue
            except AttributeError:
                warn("SKIPPED: re does not match {line}".format(line=line))
                continue


if __name__ == "__main__":
    main()
