#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""FungiDB conventions to standardize organism naming.

2013-06-10
Edward Liaw
"""
try:
    import re2 as re
except ImportError:
    import re
else:
    re.set_fallback_notification(re.FALLBACK_QUIETLY)
from warnings import warn
import functools


RE_NON_ALPHANUM = re.compile(r'[^a-zA-Z0-9]+')
RE_LONG_WORDS = re.compile(r'[a-zA-Z][a-z]{3,}')
RE_NON_ALPHA = re.compile(r'[^a-zA-Z]+')


def unique_abbrev(obj, length=4):
    """Takes a long name and tries to find a unique 4-letter abbreviation by
    substituting the last character."""
    cache = obj.cache = set()
    mod = length - 1

    @functools.wraps(obj)
    def unique_check(*args, **kwargs):
        long_name = obj(*args, **kwargs)
        for i in range(len(long_name) - mod):
            name = long_name[:mod] + long_name[i + mod]
            if name not in cache:
                break
        else:
            raise Exception("Couldn't find an abbreviation for %s" % name)
        cache.add(name)
        return name
    return unique_check


@unique_abbrev
def orthomcl(genus, species, strain):
    string = (genus[0] + species + strain).replace(" ", "")
    string = RE_NON_ALPHA.sub("", string).lower()
    return string


def filename(genus, species, strain):
    """Create a filename-appropriate name."""
    strain = abbrev_strain(strain)
    species = species.split(" ", 1)[0]
    return "_".join((genus[0].upper() + species.lower(), strain))


def genus_species(taxname):
    """Genus and shortened species name."""
    return " ".join(taxname.strip().split(" ", 2)[:2])


def abbrev_strain(strain):
    """Create an abbreviated strain name."""
    # Reduce long, lowercase words to 4 letters.
    shortened_words = []
    prev = 0
    for match in RE_LONG_WORDS.finditer(strain):
        shortened_words.append(strain[prev:match.start() + 4])
        prev = match.end()
    shortened_words.append(strain[prev:])
    normalized = "".join(shortened_words)

    # Remove spaces
    normalized = normalized.replace(" ", "")

    # Substitute none alpha-numeric characters with a -.
    normalized = RE_NON_ALPHANUM.sub("-", normalized)
    return normalized


def abbrev_dbname(genus, species, strain):
    """Create an abbreviated organism name for internal use."""
    strain = abbrev_strain(strain)
    return genus[0].upper() + species[:3].lower() + strain


def split_taxname(taxname):
    """Split a name taken from NCBI taxonomy."""
    split_name = taxname.strip().split(" ")
    genus = split_name.pop(0)
    species = split_name[0]
    strain = None

    # Handle special species names by looking for centralized abbreviations:
    #   neoformans var. neoformans
    #   oxysporum f. sp. lycopersici
    if len(split_name) > 2:
        for i in range(1, len(split_name) - 1):
            maybe_abbrev = split_name[i]
            if maybe_abbrev.endswith("."):
                # Found an abbreviation.
                species = " ".join(split_name[:i + 2])
                strain = " ".join(split_name[i + 2:])
            else:
                break
    if strain is None:
        # Not a special species name.
        strain = " ".join(split_name[1:])

    if not strain:
        # Empty strain name.
        warn("Organism %s does not have a strain." % taxname)

    return genus, species, strain


if __name__ == "__main__":
    import json

    with open("fungidb.json") as infile:
        organisms = json.load(infile)

    for o in organisms:
        taxname = o["fullnamencbi"]
        if taxname is not None:
            print(taxname)
            genus, species, strain = split_taxname(taxname)
            o_strain = o["strain"]
            if strain is not None:
                assert strain == o_strain
            else:
                strain = o_strain
            print(abbrev_dbname(genus, species, strain))
