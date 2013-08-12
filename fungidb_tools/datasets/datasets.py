"""Common functions used to generate xml dataset configurations
from the FungiDB Genomes spreadsheet.

2013-07-16
Edward Liaw
"""

from lxml import etree
from .. import naming
import os

defaults = {
    "json": os.path.expanduser("~/workspace/FungiDB.json"),
    "xml": os.path.expanduser("~/GUS/current/project_home/FungiDBDatasets/Datasets/lib/xml/datasets/FungiDB.xml"),
    "datasets": os.path.expanduser("~/GUS/current/project_home/FungiDBDatasets/Datasets/lib/xml/datasets/FungiDB"),
    "gdoc": "FungiDB Genomes",
    "gsheet": "Edit",
}
# If a dataset column is renamed we can alter the value in
# _row and use the same key to access it using get_row().
_rows = {
    "abbrev": "abbreviation",
    "fullname": "ncbiname",
    "species": "species",
    "strain": "strain",
    "clade": "clade",
    "subclade": "subclade",
    "taxid": "strainncbitaxid",
    "speciestaxid": "speciesncbitaxid",
    "source": "source",
    "soterm": "soterm",
    "format": "genomeformat",
    "version": "assemblyversion",
    "idprefix": "idprefix",
    "oldabbrevs": "oldabbreviations",
    "isloaded": "loaded",
    "isrefstrain": "referencestrain",
    "isfamrep": "familyrepresentative",
    "mito": "mitochondrialchromosomesloaded",
    "products": "productsloaded",
}


class InvalidFormatException(Exception):
    pass


def get_row(o, row):
    return o[_rows[row]]


def ds_to_bool(b):
    """Check if a spreadsheet entry is equivalent to True (Yes, Reload)."""
    return (b in ("Yes", "Ready", "Reload"))


def xml_bool(b):
    """Write out boolean as a string for the xml file."""
    return "true" if b else "false"


def make_constant(parent, name, value):
    """Create an xml constant."""
    const = etree.SubElement(parent, "constant", name=name, value=value)
    return const


def make_prop(parent, name, text):
    """Create an xml property subelement."""
    prop = etree.SubElement(parent, "prop", name=name).text = text
    return prop


def make_dataset(parent, cls):
    """Create an xml dataset subelement."""
    ds = etree.SubElement(parent, "dataset", **{"class": cls})
    return ds


def file_format(fmt):
    """Return generic naming conventions used to call file formats in EuPathDB."""
    fmt = fmt.split(' ')[-1].lower()
    if fmt in ("gff3", "gff", "gtf"):
        return "gff3"
    elif fmt in ("genbank"):
        return "genbank"
    else:
        raise InvalidFormatException("Unknown file format")


def extract_reps(organisms, debug=False):
    """\
    Make dictionaries of all the representative species and families.
    Also, perform some checks to ensure that the representative species
    are unique and present.
    """
    species_reps = {}
    family_reps = {}
    for o in organisms:
        abbrev = get_row(o, 'abbrev')

        genus_species = naming.short_species(get_row(o, 'fullname'))
        if get_row(o, 'isrefstrain') == "Yes":
            if debug and genus_species in species_reps:
                raise InvalidFormatException(
                    "{} species has too many reference strains: {}.".format(
                        genus_species, (species_reps[genus_species], abbrev)))
            species_reps[genus_species] = abbrev
        elif debug and genus_species not in species_reps:
            raise InvalidFormatException((
                "{} species missing representative or out of order"
                "(representative must come first).").format(genus_species))

        # We arbitrarily use the "subclade" as the "family" grouping.
        # Doesn't really map to the taxonomic family.
        family = get_row(o, 'subclade')
        if get_row(o, 'isfamrep') == "Yes":
            if debug and family in family_reps:
                raise InvalidFormatException(
                    "{} family has too many representatives: {}.".format(
                        family, (family_reps[family][0], abbrev,)))
            family_reps[family] = (abbrev, get_row(o, 'taxid'))

    return species_reps, family_reps


def old_abbrevs(organisms):
    """\
    Create a dictionary that maps old abbreviations to their new one.
    Useful for changing organisms' abbrevation with scripts.
    """
    sub_abbrev = {}

    for o in organisms:
        abbrev = get_row(o, 'abbrev')
        #genus_species = naming.short_species(get_row(o, 'fullname'))
        #subclade = get_row(o, 'subclade')

        old_abbrevs = get_row(o, 'oldabbrevs')
        if old_abbrevs is not None:
            for old in old_abbrevs.split(','):
                sub_abbrev[old] = abbrev

    return sub_abbrev
