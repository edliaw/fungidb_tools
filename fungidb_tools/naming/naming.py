"""FungiDB naming conventions to standardize organism names in the database.

2013-06-10
Edward Liaw
"""
import re
from warnings import warn
import unicodedata

RE_WHITESPACE = re.compile(r'\s+')
RE_UNFRIENDLY = re.compile(r'[^\w\s]+')
RE_LONG_WORDS = re.compile(r'[a-zA-Z][a-z]{3,}')
RE_NON_ALPHA = re.compile(r'[^a-zA-Z]+')


class OrthoAbbrev(object):
    """Generate a unique 4-letter orthomcl abbreviation for the organism.

    >>> ortho = OrthoAbbrev()
    >>> ortho.abbrev('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.49')
    'mcir'
    >>> ortho.abbrev('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.50')
    'mcis'
    """
    def __init__(self, seed=None):
        self.abbrevs = {} if seed is None else seed

    def abbrev(self, genus, species, strain):
        if (genus, species, strain) in self.abbrevs:
            return self.abbrevs[(genus, species, strain)]
        else:
            abbrevs = self.abbrevs.values()

            long_name = genus[0] + species + abbrev_strain(strain)
            long_name = RE_NON_ALPHA.sub("", long_name).lower()

            length = 4
            prefix = long_name[:length - 1]
            mod = ord(long_name[length - 1])
            for i in range(26):
                name = prefix + chr(mod + i)
                if name not in abbrevs:
                    self.abbrevs[(genus, species, strain)] = name
                    return name
            else:
                raise Exception("Couldn't find a unique abbreviation for {} {} {}".format(genus, species, strain))


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


def filename(genus, species, strain):
    """Returns a filename-appropriate name.

    >>> filename('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.49')
    'Mcircinelloides_CBS277-49'
    """
    strain = abbrev_strain(strain)
    species = species.split(" ", 1)[0]
    return "_".join((genus[0].upper() + species.lower(), strain))


def abbrev_strain(strain):
    """Create an abbreviated strain name.

    >>> abbrev_strain('CBS 277.49')
    'CBS277-49'
    >>> abbrev_strain('NRRL 1555(-)')
    'NRRL1555-'
    >>> abbrev_strain('C735 delta SOWgp')
    'C735deltSOWgp'
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

    >>> abbrev_dbname('Tremella', 'mesenterica', 'DSM 1558')
    'TmesDSM1558'
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

    >>> split_taxname('Tremella mesenterica DSM 1558')
    ('Tremella', 'mesenterica', 'DSM 1558')
    >>> split_taxname('Mucor circinelloides f. lusitanicus CBS 277.49')
    ('Mucor', 'circinelloides f. lusitanicus', 'CBS 277.49')
    >>> split_taxname('Puccinia graminis f. sp. tritici CRL 75-36-700-3')
    ('Puccinia', 'graminis f. sp. tritici', 'CRL 75-36-700-3')
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


def split_species(species):
    """Split long species name into 2-tuple of species name and varietas/forma
    (infraspecific).

    >>> split_species('mesenterica')
    ('mesenterica', '')
    >>> split_species('circinelloides f. lusitanicus')
    ('circinelloides', 'f. lusitanicus')
    """
    split = species.split(" ")
    species = " ".join(split[:1])
    infra = " ".join(split[1:])
    return species, infra


if __name__ == "__main__":
    import doctest
    doctest.testmod()
