"""
2013-08-20
Edward Liaw
"""

from __future__ import print_function
import re
import sys
from functools import total_ordering
from collections import OrderedDict


R_WHITESPACE = re.compile(r'\s+')


class Comment(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return '# ' + self.text


class Directive(object):
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __str__(self):
        return '##' + '\t'.join(self.name, self.text)


@total_ordering
class Region(object):
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
    def __init__(self, seqid, source, soterm, id,
                 parents=None, regions=None, children=None):
        self.seqid = seqid
        self.source = source
        self.soterm = soterm
        self.id = id
        self.parents = set(parents) if parents else set()
        self.regions = regions or []
        self.children = children or set()

    @classmethod
    def from_file(cls, seqid, source, soterm, start, end, score, strand,
                  phase, id, parents, attributes):
        regions = [Region(seqid, start, end, score, strand, phase, attributes)]
        return cls(seqid, source, soterm, id, parents, regions)

    def format(self, split_parents=False):
        outstr = []

        a = []
        if self.id:
            a.append(("ID", [self.id]))
        if self.parents:
            a.append(("Parent", self.parents))

        for r in sorted(self.regions):
            attributes = a + r.attributes.items()
            attributes = ['='.join((k, ','.join(v))) for k, v in attributes]
            attributes = ';'.join(attributes)
            row = '\t'.join((r.seqid, self.source, self.soterm, r.start, r.end,
                             r.score, r.strand, r.phase, attributes))
            outstr.append(row)

        for c in sorted(self.children):
            outstr.append(c.format())

        return '\n'.join(outstr)

    def __lt__(self, other):
        return min(self.regions) < min(other.regions)


class GFF3Parser(object):
    def __init__(self, fasta=False, comments=True):
        self.fasta = fasta
        self.comments = comments

    def parse_file(self, infile):
        features = OrderedDict()
        for i, line in enumerate(infile):
            line = line.rstrip()
            if line.startswith('###'):
                yield self.tier_features(features)
            elif line.startswith('##FASTA'):
                yield self.tier_features(features)
                if self.fasta:
                    yield self.parse_fasta(infile)
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
                    sys.stderr.write("Failed on line %d\n" % i)
                    raise e

                try:
                    f = features[feat.id]
                except KeyError:
                    features[feat.id] = feat
                else:
                    f.regions += feat.regions
        else:
            yield self.tier_features(features)

    def parse_directive(self, line):
        line = line.lstrip('#')
        name, text = R_WHITESPACE.split(line, 1)
        return Directive(name, text)

    def parse_comment(self, line):
        line = line.lstrip('#').lstrip()
        return Comment(line)

    def parse_feature(self, line):
        columns = line.split('\t')
        assert len(columns) == 9, "Line does not have 9 columns."

        seqid, source, soterm, start, end, score, strand, phase, _attr = columns

        id, parents, attributes = self.parse_attributes(_attr)

        f = GFF3Feature.from_file(seqid, source, soterm, start, end, score,
                                  strand, phase, id, parents, attributes)
        return f

    def parse_attributes(self, attributes):
        attr = [a.split('=', 1) for a in attributes.split(';')]
        attr = OrderedDict((k, v.split(',')) for k, v in attr)

        # Separate id and parents
        _id = attr.pop("ID", None)
        parents = attr.pop("Parent", None)

        assert _id is not None, "Feature missing ID"
        assert len(_id) == 1, "Illegal character ',' in ID"
        id = _id[0]

        return id, parents, attr

    def parse_fasta(self, infile):
        from Bio import SeqIO
        return SeqIO.parse(infile)

    def tier_features(self, features):
        """Follows parent attribute to link parents to children.
        Returns a dict of only parents.
        Has side-effect of clearing the dict of features.
        """
        tiered_features = OrderedDict()
        for id, f in features.iteritems():
            if f.parents:
                for p in f.parents:
                    features[p].children.add(f)
            else:
                tiered_features[id] = f
        features.clear()
        return tiered_features
