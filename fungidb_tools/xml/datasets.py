from lxml import etree
from .. import naming
import os

DEFAULTS = {
    "json": os.path.expanduser("~/workspace/FungiDB.json"),
    "xml": os.path.expanduser("~/workspace/FungiDB.xml"),
    "gdoc": "multi-species fungal genome db targets",
    "gsheet": "Target Genomes for Release",
}


class InvalidSpreadsheetException(Exception):
    pass


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
        abbrev = o["fungidbabbreviation"]

        genus_species = naming.genus_species(o["fullnamencbi"])
        if o["speciesrepresentative"] == "Yes":
            if debug and genus_species in species_reps:
                raise InvalidSpreadsheetException("{} species has too many representatives: {}.".format(genus_species, (species_reps[genus_species], abbrev)))
            species_reps[genus_species] = abbrev
        elif debug and genus_species not in species_reps:
            raise InvalidSpreadsheetException("{} species missing representative or out of order (representative must come first).".format(genus_species))

        family = o["subclade"]
        if o["familyrepresentative"] == "Yes":
            if debug and family in family_reps:
                raise InvalidSpreadsheetException("{} family has too many representatives: {}.".format(family, (family_reps[family][0], abbrev,)))
            family_reps[family] = (abbrev, o["strainncbitaxid"])

    return species_reps, family_reps
