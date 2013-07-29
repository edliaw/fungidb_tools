"""Relatively dumb GTF/GFF2/GFF3 parser and Feature class to encapsulate it.
Assumes each line is a "feature".

Not implemented:
    Multi-line attributes
    Inheritance

2013-07-16
Edward Liaw
"""

from __future__ import print_function
import sys
from warnings import warn
from collections import OrderedDict


class Feature(object):
    def __init__(self, cols, attr):
        self.seqid, self.source, self.soterm, self.start, self.end, self.score, self.strand, self.phase = cols
        self.attr = attr

    def to_gff(self):
        cols = [self.seqid, self.source, self.soterm, self.start, self.end, self.score, self.strand, self.phase]
        return cols, self.attr


class GFFParser(object):
    """GTF/GFF2/GFF3 parser.  Initialize with options then parse file."""
    def __init__(self, filetype, fasta=False, comments=True):
        self.delim = self._set_filetype(filetype)
        self.fasta = fasta
        self.comments = comments

    @classmethod
    def from_args(cls, args):
        return cls(args.filetype, args.fasta, args.comments)

    @staticmethod
    def _set_filetype(filetype):
        delim = {}
        delim['col'] = '\t'
        delim['attr'] = ';'
        if filetype in ('gtf', 'gff2'):
            delim['key'] = ' '
            delim['val'] = '"'
        elif filetype == 'gff3':
            delim['key'] = '='
            delim['val'] = ''
        else:
            raise Exception('Invalid filetype: must be gtf, gff2, or gff3.')
        return delim

    def parse(self, infile, commentfile=sys.stdout):
        col_d = self.delim['col']
        attr_d = self.delim['attr']
        key_d = self.delim['key']
        val_d = self.delim['val']

        for line in infile:
            line = line.rstrip()

            # Comments
            if line.startswith('#'):
                if line.startswith('##'):
                    if not self.fasta and line.startswith('##FASTA'):
                        break
                    print(line, file=commentfile)
                elif self.comments:
                    print(line, file=commentfile)
                continue

            # Columns
            cols = line.split(col_d, 9)
            # Attributes column
            attr_col = cols.pop()
            attr = OrderedDict()
            for pair in attr_col.rstrip(attr_d).split(attr_d):
                pair = pair.strip()
                if pair.startswith('#'):
                    # Try to cut out comments; warn in case it's a bug
                    warn("WARNING: inline comment present:\n{}".format(line))
                    break
                try:
                    key, val = pair.split(key_d, 2)
                except:
                    raise Exception(pair)
                attr[key] = val.strip(val_d)
            yield cols, attr

    def parse_features(self, infile, commentfile=sys.stdout):
        """Parse lines as Features instead of (columns, attributes)."""
        for cols, attr in self.parse(infile, commentfile):
            yield Feature(cols, attr)

    def join(self, cols, attr):
        attrs = (self.delim['key'].join((key, surround(val, self.delim['val']))) for key, val in attr.items())
        cols = cols + [self.delim['attr'].join(attrs),]
        return self.delim['col'].join(cols)

    def join_feature(self, feature):
        return self.join(*feature.to_gff())

    def join_all(self, rows):
        for cols, attr in rows:
            yield self.join(self, cols, attr)


def surround(value, delim):
    return "{1}{0}{1}".format(value, delim)


def add_gff_args(parser):
    parser.add_argument('-t', '--filetype',
                        choices=('gtf', 'gff2', 'gff3'), default='gtf',
                        help='filetype to parse')
    parser.add_argument('-c', '--comments',
                        action='store_true',
                        help='retain comments')
    parser.add_argument('-f', '--fasta',
                        action='store_true',
                        help='retain FASTA sequences')
