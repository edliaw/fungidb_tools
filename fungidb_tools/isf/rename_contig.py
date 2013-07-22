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
from .roman import roman_to_int

RE_DEFAULT = (r'Chr_(?:(?P<number>\d+)|(?:P<roman>[XIV]+)|(?P<letter>[A-Z]))',)


class NoMatchException(Exception):
    pass


class ContigRenamer(object):
    def __init__(self, abbrev, padding, soterm, regex):
        self.abbrev = abbrev
        self.padding = "{{:0{:d}d}}".format(padding)

        assert len(soterm) == len(regex), "Every regular expression should be provided a SO term"
        self.soterm = soterm
        self.regex = [re.compile(rx) for rx in regex]

    @classmethod
    def from_args(cls, args):
        return cls(args.species, args.padding, args.soterm, args.regex)

    def _format_number(self, number):
        return self.padding.format(int(number))

    def rename(self, target):
        for rx, so in zip(self.regex, self.soterm):
            match = rx.search(target)
            if match is not None:
                match = match.groupdict()
                if 'number' in match:
                    contig = self._format_number(match['number'])
                elif 'roman' in match:
                    contig = match['roman']
                elif 'letter' in match:
                    contig = match['letter'].upper()
                else:
                    raise Exception("Regex {} doesn't contain a number, letter, or roman numeral field.".format(rx.pattern))
                return "{}_{}{}".format(self.abbrev, so, contig)
        else:
            raise NoMatchException("No regular expression matched.")


def add_rename_args(parser):
    parser.add_argument('--species',
                        help='species abbreviation')
    parser.add_argument('--padding',
                        type=int, default=2,
                        help='number padding adds 0s to fix the width')
    parser.add_argument('--soterm',
                        nargs='*', choices=('Chr', 'SC'), default=('Chr',),
                        help='SO terms (per regular expression)')
    parser.add_argument('--regex',
                        nargs='*', default=RE_DEFAULT,
                        help='regular expressions to search the contig identifier')
