"""FungiDB naming conventions to standardize organism names in the database.

2013-06-10
Edward Liaw
"""
import re
from warnings import warn
from decorator import decorator
import unicodedata


RE_WHITESPACE = re.compile(r'\s+')
RE_UNFRIENDLY = re.compile(r'[^\w\s]+')
RE_LONG_WORDS = re.compile(r'[a-zA-Z][a-z]{3,}')
RE_NON_ALPHA = re.compile(r'[^a-zA-Z]+')


def slugify(string, whitespace="_", unfriendly="-"):
    """Reduces a string into ASCII and substitutes for whitespace and
    non-alphabetic characters.
    """
    string = RE_UNFRIENDLY.sub(
        unfriendly,
        unicodedata.normalize('NFKD', unicode(string)).encode('ascii', 'ignore')
    )
    string = RE_WHITESPACE.sub(whitespace, string)
    return string


def _unique_abbrev(func, *args, **kwargs):
    """Decorator: Uses caching to check that we only generate unique names
    of length 4 (by default).
    """
    long_name = func(*args, **kwargs)
    mod = func.length - 1
    for i in range(len(long_name) - mod):
        name = long_name[:mod] + long_name[i + mod]
        if name not in func.cache:
            break
    else:
        # Should only be raised if there are more than 26 organisms that
        # have the same 3-letter prefix.
        raise Exception("Couldn't find a unique abbreviation for " + name)
    func.cache.add(name)
    return name


def unique_abbrev(f, length=4):
    """Decorator: Uses caching to check that we only generate unique names
    of length 4 (by default).
    """
    f.cache = set()
    f.length = length
    return decorator(_unique_abbrev, f)


@unique_abbrev
def orthomcl(genus, species, strain):
    """Returns a unique 4-letter orthomcl abbreviation each time it is called.
    Context sensitive.

    >>> orthomcl('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.49')
    'mcir'
    >>> orthomcl('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.50')
    'mcis'
    """
    string = (genus[0] + species + strain).replace(" ", "")
    string = RE_NON_ALPHA.sub("", string).lower()
    return string


def filename(genus, species, strain):
    """Returns a filename-appropriate name.

    >>> filename('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.49')
    'McircinelloidesCBS277-49'
    """
    strain = abbrev_strain(strain)
    species = species.split(" ", 1)[0]
    return "_".join((genus[0].upper() + species.lower(), strain))


def genus_species(taxname):
    """Genus and shortened species name if the species name is long.

    >>> genus_species('Mucor circinelloides f. lusitanicus CBS 277.49')
    'Mucor circinelloides'
    """
    return " ".join(taxname.strip().split(" ", 2)[:2])


def abbrev_strain(strain):
    """Create an abbreviated strain name.

    >>> abbrev_strain('CBS 277.49')
    'CBS277-49'
    """
    # Reduce long, lowercase words to 4 letters.
    shortened_words = []
    prev = 0
    for match in RE_LONG_WORDS.finditer(strain):
        shortened_words.append(strain[prev:match.start() + 4])
        prev = match.end()
    shortened_words.append(strain[prev:])
    normalized = "".join(shortened_words)

    # Remove spaces and substitute non-alphanumeric characters.
    normalized = slugify(normalized, whitespace="", unfriendly="-")

    return normalized


def abbrev_dbname(genus, species, strain):
    """Create an abbreviated organism name for internal use.

    >>> abbrev_dbname('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.49')
    'McirCBS277-49'
    """
    strain = abbrev_strain(strain)
    return genus[0].upper() + species[:3].lower() + strain


def split_taxname(taxname):
    """Split a name taken from NCBI taxonomy.
    Returns: 3-tuple of (genus, species, strain).

    Assumptions:
        Words are separated by spaces.
        Genus is one word.
        Species may be more than one word, so long as the inner words are
            abbreviations (end with a .).
        Strain immediately follows species and it can be any number of words.
        Strain may be None if the taxonomy name is only of the species.
            In this case, you'll need to provide the strain name some other
            way.

    >>> split_taxname('Mucor circinelloides f. lusitanicus CBS 277.49')
    ('Mucor', 'circinelloides f. lusitanicus',  'CBS 277.49')
    """
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
        # Not a special species name.  Species is just one word, so strain is
        # the rest.
        strain = " ".join(split_name[1:])

    if not strain:
        # No strain name.  Some strains don't have an NCBI taxid so we had to
        # use the species NCBI taxid (and species names).
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
