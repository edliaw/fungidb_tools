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
    def __init__(self, seqid, source, soterm, pos, score, strand, phase, attr, comment, children):
        """Create a new Feature.
        pos should be list of tuples (start, end)
        attr should be an OrderedDict of attributes
        children should be a list of child Features
        """
        self.seqid = seqid
        self.source = source
        self.soterm = soterm
        self.pos = pos
        self.score = score
        self.strand = strand
        self.phase = phase
        self.attr = attr
        self.comment = comment
        self.children = children

    @classmethod
    def unflatten(cls, cols, attr, comment="", children=None):
        """Make new Feature out of list of GFF columns and OrderedDict of attributes."""
        seqid, source, soterm, start, end, score, strand, phase = cols
        pos = [(start, end)]
        children = [] if children is None else children
        return cls(seqid, source, soterm, pos, score, strand, phase, attr, comment, children)

    def flatten(self):
        """Reduce Feature into GFF columns, attributes, and comment."""
        for vals in self._flatten():
            yield vals
        for vals in self._flatten_children():
            yield vals

    def _flatten(self):
        for start, end in self.pos:
            cols = [self.seqid, self.source, self.soterm, start, end, self.score, self.strand, self.phase]
            yield cols, self.attr, self.comment

    def _flatten_children(self):
        for child in self.children:
            for multichild in child._flatten():
                yield multichild
        for child in self.children:
            for subchild in child._flatten_children():
                yield subchild

    def append(self, other):
        """Add multi-line position, child feature, or sub-child feature."""
        try:
            # Check for multiline feature.
            if self.attr['ID'] == other.attr['ID']:
                self.append_multiline(other)
                return True

            # Check for multiple inheritance (alt-splicing) and children-of-children.
            added = False
            for parent in other.attr['Parent'].split(','):
                if added:
                    warn("Multiple parents:\t{}\t{}".format(other, other.attr['Parent']))
                added = False
                if self.attr['ID'] == parent:
                    self.children.append(other)
                    added = True
                else:
                    # See if any of the children are parents.
                    for child in self.children:
                        if child.append(other):
                            added = True
                            break
            return added
        except KeyError:
            # Self or other lacks a Parent or ID attribute.
            return False

    def append_multiline(self, other):
        """Add multiline feature's position."""
        self.pos += other.pos
        warn("Multi-line feature:\t{}\t{}".format(self, other))

    def append_child(self, other):
        assert self.attr['ID'] in other.attr['Parent'].split(',')
        self.children.append(other)

    def rename(self, name):
        self.attr['ID'] = name
        for child in self.children:
            child.attr['Parent'] = name

    def __str__(self):
        start, end = self.pos[0]
        return "{}:{}{}{}-{}".format(self.soterm, self.seqid, self.strand, start, end)

    def __gt__(self, other):
        if self.chrom != other.chrom:
            return self.chrom > other.chrom
        elif self.min != other.min:
            return self.min > other.min
        else:
            return self.min > other.max


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
            delim['quot'] = '"'
        elif filetype == 'gff3':
            delim['key'] = '='
            delim['quot'] = ''
        else:
            raise Exception('Invalid filetype: must be gtf, gff2, or gff3.')
        return delim

    def parse_flat(self, infile, commentfile=sys.stdout):
        col_d = self.delim['col']
        attr_d = self.delim['attr']
        key_d = self.delim['key']
        quot_d = self.delim['quot']

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
            if not line:
                warn("Empty line in file.")
                continue
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
                    raise Exception("FAILED to split: %s" % line)
                attr[key] = val.strip(quot_d)
            yield cols, attr, comment

    def parse(self, infile, commentfile=sys.stdout):
        """Parse lines as Features instead of (columns, attributes)."""
        for cols, attr, comment in self.parse_flat(infile, commentfile):
            yield Feature.unflatten(cols, attr, comment)

    def parse_3level_sorted(self, infile, commentfile=sys.stdout):
        """Fill features with children and yield top-level parents only.
        Assumes children follow parent.
        """
        top = None
        for feat in self.parse(infile, commentfile):
            if top is None:
                top = feat
            elif not top.append(feat):
                yield top
                top = feat

    def join_flat(self, cols, attr, comment=""):
        """Convert flattened feature attributes into a GFF string."""
        attrs = [self.delim['key'].join((key, surround(val, self.delim['quot']))) for key, val in attr.items()]
        if comment:
            attrs.append(comment)
        cols = cols + [self.delim['attr'].join(attrs)]
        return self.delim['col'].join(cols)

    def join(self, feature):
        for cols, attr, comment in feature.flatten():
            yield self.join_flat(cols, attr, comment)

    def join_all(self, rows):
        for cols, attr, comment in rows:
            yield self.join_flat(self, cols, attr, comment)


def surround(value, delim):
    return value.join((delim, delim))


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
