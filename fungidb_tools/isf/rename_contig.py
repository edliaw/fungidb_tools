"""Reformat contig name.

Example:
    >>> Supercontig_12.1 of Neurospora crassa OR74A
    NcraOR74A_SC01

2013/07/16
Edward Liaw

"""
from __future__ import absolute_import, unicode_literals
from future.builtins import zip, int
import re
from . import roman

RE_DEFAULT = (r'Chr_(?:(?P<number>\d+)|(?:P<roman>[XIV]+)|(?P<letter>[A-Z]))',)


class NoMatchException(Exception):

    """Exception: Regular expression found no matches."""

    pass


class ContigRenamer(object):

    """Customizable renaming of contigs."""

    def __init__(self, abbrev, padding, soterm, regex):
        self.abbrev = abbrev
        self.padding = "{{:0{:d}d}}".format(padding)

        assert len(soterm) == len(regex), \
            "Every regular expression should be provided a SO term"
        self.soterm = soterm
        self.regex = [re.compile(rx) for rx in regex]

    @classmethod
    def from_args(cls, args):
        """Return new instance from cli arguments."""
        return cls(args.species, args.padding, args.soterm, args.regex)

    def _format_number(self, number):
        return self.padding.format(int(number))

    def rename(self, target):
        """Return renamed contig line."""
        for rx, so in zip(self.regex, self.soterm):
            match = rx.search(target)
            if match is None:
                continue
            match = match.groupdict()
            number = match.get('number', None)
            roman_num = match.get('roman', None)
            letter = match.get('letter', None)
            if number is not None:
                contig = self._format_number(number)
            elif roman_num is not None:
                if roman_num.isdigit():
                    contig = roman.roman_from_int(int(roman_num))
                else:
                    contig = roman_num
            elif letter is not None:
                contig = letter.upper()
            else:
                raise Exception("Regex {} doesn't contain a number, letter, "
                                "or roman numeral field.".format(rx.pattern))
            return "{}_{}{}".format(self.abbrev, so, contig)
        raise NoMatchException("Doesn't match any regular expression: "
                               "{}".format(target))


def add_rename_args(parser):
    """Add arguments to argument parser."""
    parser.add_argument('--species',
                        help='species abbreviation')
    parser.add_argument('--padding',
                        type=int, default=2,
                        help='number padding adds 0s to fix the width')
    parser.add_argument('--soterm',
                        nargs='*',
                        choices=('Chr', 'SC', 'LG'), default=('Chr',),
                        help='SO terms (per regular expression)')
    parser.add_argument('--regex',
                        nargs='*', default=RE_DEFAULT,
                        help='regular expressions matching contig identifiers')
