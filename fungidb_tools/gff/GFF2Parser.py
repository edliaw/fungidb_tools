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
R_ATTR_TOKENS = re.compile(r';|#.*|"[^"]*"|[^";\s]+')


class Comment(object):
    def __init__(self, text):
        self.text = text

    @classmethod
    def from_gff(cls, text):
        return cls(text.lstrip('#').lstrip())

    def __str__(self):
        return '# ' + self.text


class Directive(object):
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __str__(self):
        return '##' + '\t'.join(self.name, self.text)


@total_ordering
class GFF2Feature(object):
    def __init__(self, seqid, source, feature, start, end, score, strand,
                 phase, attributes=None, comment=None):
        self.seqid = seqid
        self.source = source
        self.feature = feature
        self.start = start
        self.end = end
        self.score = score
        self.strand = strand
        self.phase = phase
        self.attributes = attributes or OrderedDict()
        self.comment = comment

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

    def format(self):
        attributes = [' '.join((k, ' '.join(v))) for k, v in self.attributes.items()]
        if self.comment:
            attributes.append(str(self.comment))
        attributes = ';'.join(attributes)
        return '\t'.join((self.seqid, self.source, self.feature, self.start,
                          self.end, self.score, self.strand, self.phase,
                          attributes))


class GFF2Parser(object):
    def __init__(self, fasta=False, comments=True):
        self.fasta = fasta
        self.comments = comments

    def parse(self, infile):
        for i, line in enumerate(infile):
            line = line.rstrip()
            if line.startswith('##'):
                yield self.parse_directive(line)
            elif line.startswith('#'):
                yield self.parse_comment(line)
            else:
                try:
                    yield self.parse_feature(line)
                except Exception as e:
                    sys.stderr.write("Failed on line %d\n" % i)
                    raise e

    def parse_directive(self, line):
        line = line.lstrip('#')
        name, text = R_WHITESPACE.split(line, 1)
        return Directive(name, text)

    def parse_comment(self, line):
        line = line.lstrip('#').lstrip()
        return Comment(line)

    def parse_feature(self, line):
        columns = line.split('\t', 8)
        seqid, source, feature, start, end, score, strand, phase, _attr = columns

        attributes, comment = self.parse_attributes(_attr)

        f = GFF2Feature(seqid, source, feature, start, end, score, strand,
                        phase, attributes, comment)
        return f

    def parse_attributes(self, attributes):
        attr = OrderedDict()
        values = []
        comment = None
        for t in R_ATTR_TOKENS.findall(attributes):
            if t == ';':
                tag = values.pop(0)
                attr[tag] = values
                values = []
            elif t.startswith('#'):
                comment = self.parse_comment(t)
                break
            else:
                values.append(t)
        if values:
            tag = values.pop(0)
            attr[tag] = values
        return attr, comment
