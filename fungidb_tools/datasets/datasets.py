from lxml import etree
from .. import naming
import os

defaults = {
    "json": os.path.expanduser("~/workspace/FungiDB.json"),
    "xml": os.path.expanduser("~/workspace/FungiDB.xml"),
    "gdoc": "multi-species fungal genome db targets",
    "gsheet": "Target Genomes for Release",
}
_rows = {
    "abbrev": "fungidbabbreviation",
    "fullname": "fullnamencbi",
    "species": "speciesnamencbi",
    "strain": "strain",
    "subclade": "subclade",
    "taxid": "strainncbitaxid",
    "speciestaxid": "speciesncbitaxid",
    "version": "assemblyversion",
    "source": "source",
    "isloaded": "loaded",
    "isrefstrain": "speciesrepresentative",
    "isfamrep": "familyrepresentative",
    "idprefix": "idprefix",
    "oldabbrevs": "oldabbreviations",
}


class InvalidSpreadsheetException(Exception):
    pass


def get_row(o, row):
    return o[_rows[row]]


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
    ds = etree.SubElement(parent, "dataset", **{"class": cls})
    return ds


def extract_reps(organisms, debug=False):
    """Make dictionaries of all the representative species and families. Also,
    perform some checks to ensure that the representative species are unique
    and present.
    """
    species_reps = {}
    family_reps = {}
    for o in organisms:
        abbrev = get_row(o, 'abbrev')

        genus_species = naming.short_species(get_row(o, 'fullname'))
        if get_row(o, 'isrefstrain') == "Yes":
            if debug and genus_species in species_reps:
                raise InvalidSpreadsheetException("{} species has too many representatives: {}.".format(genus_species, (species_reps[genus_species], abbrev)))
            species_reps[genus_species] = abbrev
        elif debug and genus_species not in species_reps:
            raise InvalidSpreadsheetException("{} species missing representative or out of order (representative must come first).".format(genus_species))

        family = get_row(o, 'subclade')
        if get_row(o, 'isfamrep') == "Yes":
            if debug and family in family_reps:
                raise InvalidSpreadsheetException("{} family has too many representatives: {}.".format(family, (family_reps[family][0], abbrev,)))
            family_reps[family] = (abbrev, get_row(o, 'taxid'))

    return species_reps, family_reps


def old_abbrevs(organisms):
    sub_abbrev = {}

    for o in organisms:
        abbrev = get_row(o, 'abbrev')
        genus_species = naming.short_species(get_row(o, 'fullname'))
        subclade = get_row(o, 'subclade')

        old_abbrevs = get_row(o, 'oldabbrevs')
        if old_abbrevs is not None:
            for old in old_abbrevs.split(','):
                sub_abbrev[old] = abbrev

    return sub_abbrev
