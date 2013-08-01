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
    def __init__(self, cols, attr, comment="", children=None):
        self.seqid, self.source, self.soterm, start, end, self.score, self.strand, self.phase = cols
        self.pos = [(start, end)]
        self.attr = attr
        self.comment = comment
        self.children = [] if children is None else children

    def to_gff(self):
        for start, end in self.pos:
            cols = [self.seqid, self.source, self.soterm, start, end, self.score, self.strand, self.phase]
            yield cols, self.attr, self.comment
        for child in self.children:
            for sub in child.to_gff():
                yield sub

    def append(self, other):
        added = False
        if self.attr['ID'] == other.attr['ID'] and self.soterm == other.soterm:
            self.pos += other.pos
            warn("Multi-line feature: %s" % self)
            added = True
        else:
            for parent in other.attr['Parent'].split(','):
                if self.attr['ID'] == parent:
                    self.children.append(other)
                    added = True
                else:
                    for child in self.children:
                        added = child.append(other) or added
        return added

    def rename(self, name):
        self.attr['ID'] = name
        for child in self.children:
            child.attr['Parent'] = name

    def __str__(self):
        start, end = self.pos[0]
        return "{}: {}{}-{}".format(self.seqid, self.strand, start, end)


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
            # Comments
            if line.startswith('#'):
                if line.startswith('##FASTA'):
                    if self.fasta:
                        commentfile.write(line)
                        commentfile.writelines(infile)
                    break
                elif line.startswith('##'):
                    commentfile.write(line)
                elif self.comments:
                    commentfile.write(line)
                continue

            line = line.rstrip()
            # Columns
            cols = line.split(col_d, 9)
            # Attributes column
            attr_col = cols.pop()
            attr = OrderedDict()

            comment = ""
            c = attr_col.find('#')
            if c >= 0:
                if self.comments:
                    comment = attr_col[c:]
                else:
                    warn("WARNING: inline comment present:\n%s" % line)
                attr_col = attr_col[:c]

            for pair in attr_col.rstrip(attr_d).split(attr_d):
                pair = pair.strip()
                try:
                    key, val = pair.split(key_d, 2)
                except:
                    raise Exception("FAILED to split: " + pair)
                attr[key] = val.strip(val_d)
            yield cols, attr, comment

    def parse_features(self, infile, commentfile=sys.stdout):
        """Parse lines as Features instead of (columns, attributes)."""
        for cols, attr, comment in self.parse(infile, commentfile):
            yield Feature(cols, attr, comment)

    def parse_3level(self, infile, commentfile=sys.stdout):
        features = {}
        for feat in self.parse_features(infile, commentfile):
            added = False
            try:
                added = features[feat.attr['Parent']].append(feat)
            except KeyError:
                pass
            if not added:
                features[feat.attr['ID']] = feat
        return features

    def join(self, cols, attr, comment=""):
        attrs = (self.delim['key'].join((key, surround(val, self.delim['val']))) for key, val in attr.items())
        cols = cols + [self.delim['attr'].join(attrs)]
        return self.delim['col'].join(cols) + comment

    def join_feature(self, feature):
        for cols, attr, comment in feature.to_gff():
            yield self.join(cols, attr, comment)

    def join_all(self, rows):
        for cols, attr, comment in rows:
            yield self.join(self, cols, attr, comment)


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
