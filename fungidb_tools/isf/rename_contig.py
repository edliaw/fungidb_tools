"""Reformat contig name.
Example
Input:
    Supercontig_12.1 of Neurospora crassa OR74A
Output:
    NcraOR74A_SC01

2013/07/16
Edward Liaw
"""
import re

class NoMatchException(Exception):
    pass


class ContigRenamer(object):
    def __init__(self, abbrev, soterm, padding, regex=None, is_roman=False):
        self.abbrev = abbrev
        self.soterm = soterm
        self.padding = "{{:0{:d}d}}".format(padding)

        if is_roman:
            from .roman import roman_to_int
            def format_letter(self, letter):
                return self._format_number(roman_to_int(letter))
            self._format_letter = format_letter

        if regex is None:
            regex = r'_(?:(?P<number>\d+)|(?P<letter>[A-Z]+))'
        self.regex = re.compile(regex)

    @classmethod
    def from_args(cls, args):
        return cls(args.species, args.type, args.padding, args.regex, args.roman)

    def _format_number(self, number):
        return self.padding.format(int(number))

    def _format_letter(self, letter):
        return letter.upper()

    def rename(self, target):
        match = self.regex.search(target).groupdict()
        if 'number' in match:
            contig = self._format_number(match['number'])
        elif 'letter' in match:
            contig = self._format_letter(match['letter'])
        else:
            raise NoMatchException("Regular expression didn't find a number or letter.")

        return "{}_{}{}".format(self.abbrev, self.soterm, contig)


def add_rename_args(parser):
    parser.add_argument('--species',
                        help='species abbreviation')
    parser.add_argument('--type',
                        choices=('Chr', 'SC'),
                        help='SO term')
    parser.add_argument('--padding',
                        type=int, default=2,
                        help='number padding adds 0s to fix the width')
    parser.add_argument('--roman',
                        action='store_true',
                        help='if chromosomes are enumerated by roman numerals')
    parser.add_argument('--regex',
                        help='regular expression to search the contig identifier')
