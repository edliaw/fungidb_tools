#!/usr/bin/env python
"""

Spreadsheet requirements that will be checked:
    Naming conventions:
        Abbreviation rules
        Genus, species, strain match NCBI name (unless NCBI name is missing strain)
    Reference species must be first. Order matters!
"""

from __future__ import print_function
from lxml import etree
from .. import naming


def make_prop(orgn, name, text):
    prop = etree.SubElement(orgn, "prop", name=name).text = text
    return prop


def extract_columns(organisms):
    species_refs = {}
    family_refs = {}
    for o in organisms:
        abbrev = o["fungidbabbreviation"]

        genus_species = naming.genus_species(o["fullnamencbi"])
        if o["speciesrepresentative"] == "Yes":
            assert genus_species not in species_refs, "Species has more than one reference: %s" % genus_species
            species_refs[genus_species] = abbrev
        assert genus_species in species_refs, "Reference species missing or not in order (reference must be first): %s" % genus_species

        family = o["class"]
        if o["familyrepresentative"] == "Yes":
            assert family not in family_refs, "Family has more than one reference: %s" % family
            family_refs[family] = (abbrev, o["strainncbitaxid"])
    return species_refs, family_refs


def xml_bool(b):
    if b:
        return "true"
    else:
        return "false"


if __name__ == "__main__":
    import json

    with open("fungidb.json") as infile:
        organisms = json.load(infile)

    datasets = etree.Element("datasets")
    etree.SubElement(datasets, "constant", name="projectName", value="FungiDB")

    loaded = [o for o in organisms if o["loaded"] in ("Yes", "Reload")]
    # Isolate columns as dictionaries to check references against.
    species_refs, family_refs = extract_columns(loaded)

    for o in loaded:
        # Check spreadsheet values against our naming scheme.
        taxname = o["fullnamencbi"]
        genus, species, strain = naming.split_taxname(taxname)
        o_strain = o["strain"]
        if strain:
            # Check that strain in full NCBI name matches spreadsheet
            assert strain == o_strain, "%s : %s" % (strain, o_strain)
        else:
            # NCBI name doesn"t have a strain name: set it to the spreadsheet value
            strain = o_strain
        abbrev = naming.abbrev_dbname(genus, species, strain)
        filename = naming.filename(genus, species, strain)

        # Check that our spreadsheet values are consistent.
        assert abbrev == o["fungidbabbreviation"]
        assert " ".join((genus, species)) == o["speciesnamencbi"]

        # Reference species and family
        is_species_ref = (o["speciesrepresentative"] == "Yes")
        is_family_ref = (o["familyrepresentative"] == "Yes")
        species_ref = species_refs[naming.genus_species(o["speciesnamencbi"])]
        family_name = o["class"]
        family_ref, family_ref_taxid = family_refs[family_name]
        assert is_species_ref == (species_ref == abbrev), "Reference species incorrect: %s" % species_ref
        assert is_family_ref == (family_ref == abbrev), "Reference family incorrect: %s" % family_ref
        if not is_family_ref:
            # Only the family representative will contain the family name and
            # taxid.
            family_name = ""
            family_ref_taxid = ""

        # Write fields into the xml file.
        ds = etree.SubElement(datasets, "dataset", **{"class": "organism"})
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
        # Species representative / reference strain
        make_prop(ds, "isReferenceStrain", xml_bool(is_species_ref))
        make_prop(ds, "referenceStrainOrganismAbbrev", species_ref)
        # Family representative
        make_prop(ds, "isFamilyRepresentative", xml_bool(is_family_ref))
        make_prop(ds, "familyRepOrganismAbbrev", family_ref)
        make_prop(ds, "familyNcbiTaxonIds", family_ref_taxid)
        make_prop(ds, "familyNameForFiles", family_name)
        # May need to add some of these parameters to the spreadsheet
        make_prop(ds, "isHaploid", xml_bool(True))
        make_prop(ds, "isAnnotatedGenome", xml_bool(True))
        make_prop(ds, "annotationIncludesTRNAs", xml_bool(False))
        make_prop(ds, "hasDeprecatedGenes", xml_bool(False))
        make_prop(ds, "hasTemporaryNcbiTaxonId", xml_bool(False))
        make_prop(ds, "runExportPred", xml_bool(False))
        make_prop(ds, "skipOrfs", xml_bool(False))
        make_prop(ds, "maxIntronSize", "1000")

        if is_species_ref:
            rs = etree.SubElement(datasets, "dataset", **{"class": "referenceStrain"})
            make_prop(rs, "organismAbbrev", species_ref)
            make_prop(rs, "isAnnotatedGenome", xml_bool(True))

    for ortho in ("orthomcl", "orthomclPhyletic", "orthomclTree"):
        omcl = etree.SubElement(datasets, "dataset", **{"class": ortho})
        make_prop(omcl, "projectName", "$$projectName$$")
        make_prop(omcl, "version", "5.11")

    with open("FungiDB.xml", "w") as outfile:
        print(etree.tostring(datasets, pretty_print=True), file=outfile)
