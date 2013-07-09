from lxml import etree
from .. import naming


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


def make_datasets_xml(organisms, orthomcl, debug=False):
    """Make a datasets xml file for a set of organisms.

    Args:
        organisms: pulled in as a JSON object from the FungiDB spreadsheet.
    """
    datasets = etree.Element("datasets")
    make_constant(datasets, "projectName", "FungiDB")

    loaded = [o for o in organisms if o["loaded"] in ("Yes", "Reload")]
    # Put representative organisms into dictionaries.
    species_reps, family_reps = extract_reps(loaded, debug)

    for o in loaded:
        # Check spreadsheet values against our naming scheme.
        taxname = o["fullnamencbi"]
        genus, species, strain = naming.split_taxname(taxname)
        o_strain = o["strain"]
        if strain:
            # Check that strain in full NCBI name matches spreadsheet.
            if debug and strain != o_strain:
                raise InvalidSpreadsheetException("{} strain does not match {} in spreadsheet.".format(strain, o_strain))
        else:
            # NCBI name doesn"t have a strain name: set it to the spreadsheet
            # value.
            strain = o_strain
        abbrev = naming.abbrev_dbname(genus, species, strain)
        filename = naming.filename(genus, species, strain)

        # Check that our spreadsheet values are consistent.
        o_abbrev = o["fungidbabbreviation"]
        if debug and abbrev != o_abbrev:
            raise InvalidSpreadsheetException("{} abbreviation does not match {} in spreadsheet.".format(abbrev, o_abbrev))
        if debug and " ".join((genus, species)) != o["speciesnamencbi"]:
            raise InvalidSpreadsheetException("{} species name does not match {} in spreadsheet.".format(" ".join((genus, species)), o["speciesnamencbi"]))

        # Representative species and family.
        is_species_rep = (o["speciesrepresentative"] == "Yes")
        is_family_rep = (o["familyrepresentative"] == "Yes")
        species_rep = species_reps[naming.genus_species(o["speciesnamencbi"])]
        family_name = o["subclade"]
        family_rep, family_rep_taxid = family_reps[family_name]
        if debug and is_species_rep != (species_rep == abbrev):
            raise InvalidSpreadsheetException("{} reference strain incorrect for {}".format(species_rep, abbrev))
        if debug and is_family_rep != (family_rep == abbrev):
            raise InvalidSpreadsheetException("{} family representative incorrect for {}".format(family_rep, abbrev))
        if not is_family_rep:
            # The family name and taxid are blank for non-representative
            # species.
            family_name = ""
            family_rep_taxid = ""

        # Write fields into the xml file.
        ds = make_dataset(datasets, "organism")
        make_prop(ds, "projectName", "$$projectName$$")
        make_prop(ds, "organismFullName", taxname)
        make_prop(ds, "ncbiTaxonId", o["strainncbitaxid"])
        make_prop(ds, "speciesNcbiTaxonId", o["speciesncbitaxid"])
        make_prop(ds, "organismAbbrev", abbrev)
        make_prop(ds, "publicOrganismAbbrev", abbrev)
        make_prop(ds, "organismNameForFiles", filename)
        make_prop(ds, "strainAbbrev", abbrev[4:])
        make_prop(ds, "orthomclAbbrev", naming.orthomcl(genus, species, strain))
        make_prop(ds, "taxonHierarchyForBlastxFilter", " ".join(("Eukaryota", "Fungi", genus)))
        make_prop(ds, "genomeSource", o["source"])
        make_prop(ds, "genomeVersion", o["assemblyversion"])
        # Species representative / reference strain.
        make_prop(ds, "isReferenceStrain", xml_bool(is_species_rep))
        make_prop(ds, "referenceStrainOrganismAbbrev", species_rep)
        # Family representative.
        make_prop(ds, "isFamilyRepresentative", xml_bool(is_family_rep))
        make_prop(ds, "familyRepOrganismAbbrev", family_rep)
        make_prop(ds, "familyNcbiTaxonIds", family_rep_taxid)
        make_prop(ds, "familyNameForFiles", family_name)
        # May need to add some of these parameters to the spreadsheet if they
        # vary.
        make_prop(ds, "isHaploid", xml_bool(True))
        make_prop(ds, "isAnnotatedGenome", xml_bool(True))
        make_prop(ds, "annotationIncludesTRNAs", xml_bool(False))
        make_prop(ds, "hasDeprecatedGenes", xml_bool(False))
        make_prop(ds, "hasTemporaryNcbiTaxonId", xml_bool(False))
        make_prop(ds, "runExportPred", xml_bool(False))
        make_prop(ds, "skipOrfs", xml_bool(False))
        make_prop(ds, "maxIntronSize", "1000")

        if is_species_rep:
            rs = make_dataset(datasets, "referenceStrain")
            make_prop(rs, "organismAbbrev", species_rep)
            make_prop(rs, "isAnnotatedGenome", xml_bool(True))

    for ortho in ("orthomcl", "orthomclPhyletic", "orthomclTree"):
        omcl = make_dataset(datasets, ortho)
        make_prop(omcl, "projectName", "$$projectName$$")
        make_prop(omcl, "version", orthomcl)

    return datasets
