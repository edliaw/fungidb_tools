"""
2013-08-20
Edward Liaw
"""

from __future__ import print_function, unicode_literals
import re
import sys
from functools import total_ordering
from collections import OrderedDict, namedtuple


R_WHITESPACE = re.compile(r'\s+')

GFF3Row = namedtuple('GFF3Row', ['seqid', 'source', 'type', 'start', 'end',
                                 'score', 'strand', 'phase', 'attr'])


class Comment(object):

    """A GFF comment.

    # This is a comment.

    Attributes:
        text String: comment text.
    """

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return '# ' + self.text


class Directive(object):

    """A GFF directive.

    ##FASTA

    Attributes:
        name String: directive type.
        text String: body of directive.
    """

    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __str__(self):
        return '##' + '\t'.join((self.name, self.text))


@total_ordering
class Region(object):

    """A region of nucleotides on a contig.

    Attributes:
        seqid String: contig id.
        start Int: 1-based start position.
        end Int: 1-based end position.
        score String: . or floating point number E-value or P-value.
        strand String: + for positive strand, - minus strand, . not stranded,
            ? unknown strand.
        phase String: .,0,1,2 required for all CDS features indicating # of
            bases to remove from the beginning of this region to reach the first
            base of the next codon.
        attributes String List OrderedDict: attributes in tag/value format.
    """

    def __init__(self, seqid, start, end, score='.', strand='.', phase='.',
                 attributes=None):
        self.seqid = seqid
        self.start = start
        self.end = end
        self.score = score
        self.strand = strand
        self.phase = phase
        self.attributes = attributes or OrderedDict()

    def is_within(self, other):
        return (self.seqid == other.seqid and
                self.start >= other.start and
                self.end <= other.end)

    def contains(self, other):
        return (self.seqid == other.seqid and
                self.start <= other.start and
                self.end >= other.end)

    def intersects(self, other):
        return (self.seqid == other.seqid and
                other.start <= self.start <= other.end or
                other.start <= self.end <= other.end)

    def __eq__(self, other):
        return (self.seqid == other.seqid and
                self.start == other.start and
                self.end == other.end)

    def __lt__(self, other):
        if self.seqid != other.seqid:
            return self.seqid < other.seqid
        elif self.start != other.start:
            return self.start < other.start
        else:
            return self.end < other.end


class GFF3Feature(object):

    """A GFF3 feature.

    Attributes:
        seqid String: contig id.
        source String: source identifier.
        soterm String: type of feature.
        id String: attribute identifying this feature.
        parents GFF3Feature Set: parent feature(s).
        regions Region List: region(s) this feature occupies.
        children GFF3Feature Set: children feature(s).
    """

    def __init__(self, seqid, source, soterm, id,
                 parents=None, regions=None, children=None):
        self.seqid = seqid
        self.source = source
        self.soterm = soterm
        self.id = id
        self.parents = set(parents) if parents else set()
        self.regions = regions or []
        self.children = set(children) if children else set()

    @classmethod
    def from_row(cls, row):
        """Take input from a GFF entry."""
        # Separate id and parents
        _id = row.attr.pop("ID", None)
        parents = row.attr.pop("Parent", None)

        if _id is not None:
            assert len(_id) == 1, "Illegal character ',' in ID"
            id = _id.pop()
        else:
            #assert parents is not None, "No ID or Parents attribute"
            id = None

        regions = [Region(row.seqid, row.start, row.end, row.score, row.strand,
                          row.phase, row.attr)]
        return cls(row.seqid, row.source, row.soterm, id, parents, row.regions)

    def to_rows(self, split_parents=False):
        outstr = []

        a = []
        if self.id:
            a.append(("ID", [self.id]))
        if self.parents:
            a.append(("Parent", self.parents))

        for r in sorted(self.regions):
            attributes = a + list(r.attributes.items())
            attributes = ['='.join((k, ','.join(v))) for k, v in attributes]
            attributes = ';'.join(attributes)
            row = '\t'.join((r.seqid, self.source, self.soterm, r.start, r.end,
                             r.score, r.strand, r.phase, attributes))
            outstr.append(row)

        for c in sorted(self.children):
            outstr.append(c.format())

        return '\n'.join(outstr)

    def __str__(self):
        return self.format()

    def __lt__(self, other):
        return min(self.regions) < min(other.regions)


class GFF3Parser(object):
    def __init__(self, fasta=False, comments=True):
        self.fasta = fasta
        self.comments = comments

    def parse_flat(self, infile):
        for i, line in enumerate(infile):
            line = line.rstrip()

            if line.startswith('###'):
                continue
            elif line.startswith('##FASTA'):
                if self.fasta:
                    for f in self.parse_fasta(infile):
                        yield f
                break
            elif line.startswith('##'):
                yield self.parse_directive(line)
            elif line.startswith('#'):
                if self.comments:
                    yield self.parse_comment(line)
            else:
                try:
                    yield self.parse_feature(line)
                except Exception as e:
                    sys.stderr.write("Failed on line %d:\n%s\n" % (i, line))
                    raise e

    def parse(self, infile):
        features = OrderedDict()
        buffer = set()

        def return_parents():
            if buffer:
                sys.stdout.write("Wasn't able to find parents for:\n")
                sys.stdout.write('\n'.join([f.format() for f in buffer]))
                raise
            for f in features.values():
                if not f.parents:
                    yield f
            features.clear()

        def tier_feature(feat):
            # Add to list of features or concatenate multi-line features as one
            # feature.
            try:
                f = features[feat.id]
            except KeyError:
                if feat.id is not None:
                    features[feat.id] = feat
            else:
                f.regions += feat.regions
                feat = f

            # Look for children in the buffer.
            for f in list(buffer):
                try:
                    for p in f.parents:
                        features[p].children.add(f)
                except KeyError:
                    pass
                else:
                    buffer.remove(f)

            # Look for parents or send to the buffer.
            for p in feat.parents:
                try:
                    features[p].children.add(feat)
                except KeyError:
                    buffer.add(feat)

        for i, line in enumerate(infile):
            line = line.rstrip()

            if line.startswith('###'):
                for f in return_parents():
                    yield f
            elif line.startswith('##FASTA'):
                for f in return_parents():
                    yield f
                if self.fasta:
                    for f in self.parse_fasta(infile):
                        yield f
                break
            elif line.startswith('##'):
                yield self.parse_directive(line)
            elif line.startswith('#'):
                if self.comments:
                    yield self.parse_comment(line)
            else:
                try:
                    feat = self.parse_feature(line)
                except Exception as e:
                    sys.stderr.write("Failed on line %d:\n%s\n" % (i, line))
                    raise e
                else:
                    tier_feature(feat)
        else:
            for f in return_parents():
                yield f

    def parse_directive(self, line):
        line = line.lstrip('#')
        name, text = R_WHITESPACE.split(line, 1)
        return Directive(name, text)

    def parse_comment(self, line):
        line = line.lstrip('#').lstrip()
        return Comment(line)

    def parse_feature(self, line):
        columns = line.split('\t')
        assert len(columns) == 9, "Line does not have 9 columns:\n%s" % line

        seqid, source, soterm, start, end, score, strand, phase, _attr = columns

        attributes = self.parse_attributes(_attr)

        f = GFF3Feature.from_row(GFF3Row(seqid, source, soterm, start, end,
                                         score, strand, phase, attributes))
        return f

    def parse_attributes(self, attributes):
        attr = [a.split('=', 1) for a in attributes.split(';')]
        attr = OrderedDict((k, v.split(',')) for k, v in attr)
        return attr

    def parse_fasta(self, infile):
        from Bio import SeqIO
        return SeqIO.parse(infile)
