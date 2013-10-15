"""XML generator for dataset workflow configuration files.

2013-10-11
Edward Liaw
"""
import os
from lxml import etree
from warnings import warn
from .. import naming
from .. import elementlib


class DEFAULT(object):
    """Constants: Default paths."""
    JSON = os.path.expanduser("~/workspace/FungiDB.json")
    XML = os.path.expanduser("~/GUS/current/project_home/FungiDBDatasets/Datasets/lib/xml/datasets/FungiDB.xml")
    DATASETS = os.path.expanduser("~/GUS/current/project_home/FungiDBDatasets/Datasets/lib/xml/datasets/FungiDB")
    GDOC = "FungiDB Genomes"
    GSHEET = "Edit"


class COL(object):
    """Constants: Column names in the spreadsheet."""
    ABBREV = "abbreviation"
    TAXNAME = "ncbiname"
    SPECIES = "species"
    STRAIN = "strain"
    CLADE = "clade"
    SUBCLADE = "subclade"
    FAMILY = "family"
    TAXID = "strainncbitaxid"
    SPECIESTAXID = "speciesncbitaxid"
    FAMILYTAXID = "familyncbitaxid"
    SOURCE = "source"
    SOTERM = "soterm"
    FORMAT = "genomeformat"
    VERSION = "assemblyversion"
    IDPREFIX = "idprefix"
    OLDABBREVS = "oldabbreviations"
    ISLOADED = "loaded"
    ISREFSTRAIN = "referencestrain"
    ISFAMREP = "familyrepresentative"
    MITO = "mitochondrialchromosomesloaded"
    PRODUCTS = "productsloaded"
    ORTHOMCL = "orthomclname"


def bool_from_sheet(b):
    """Check if a spreadsheet entry is equivalent to True (Yes, Reload)."""
    return (b in ("Yes", "Ready", "Reload"))


def str_from_bool(b):
    """String equivalent of python boolean value, for use in XML."""
    return "true" if b else "false"


def xml_dataset(parent, cls):
    """Mutator: create an xml dataset subelement."""
    dataset = etree.SubElement(parent, "dataset", **{"class": cls})
    return dataset


def xml_prop(parent, name, text):
    """Mutator: create an xml property subelement."""
    if isinstance(text, bool):
        text = str_from_bool(text)
    prop = etree.SubElement(parent, "prop", name=name).text = text
    return prop


def xml_constant(parent, name, value):
    """Mutator: create an xml constant."""
    if isinstance(value, bool):
        value = str_from_bool(value)
    constant = etree.SubElement(parent, "constant", name=name, value=value)
    return constant


class OrganismXMLGenerator(object):
    def __init__(self, abbrev, taxname, strain, family, source, version,
                 taxid, species_taxid,
                 species_rep, family_rep, family_rep_taxid, orthomcl_abbrev):
        self.abbrev = abbrev
        self.taxname = taxname
        self.strain = strain
        self.family = family
        self.source = source
        self.version = version
        self.taxid = taxid
        self.species_taxid = species_taxid
        self.species_rep = species_rep
        self.family_rep = family_rep
        self.family_rep_taxid = family_rep_taxid
        self.orthomcl_abbrev = orthomcl_abbrev

        genus, species, _ = naming.split_taxname(taxname)
        self.genus = genus
        self.strain_abbrev = naming.abbrev_strain(strain)
        self.filename = naming.filename(genus, species, strain)
        self.is_species_rep = (abbrev == species_rep)
        self.is_family_rep = (abbrev == family_rep)

        if not self.is_family_rep:
            self.family = ""
            self.family_rep_taxid = ""

    @classmethod
    def from_json(cls, json, species_rep, family_rep, family_rep_taxid,
                  orthomcl_abbrev, debug=False):
        abbrev = json[COL.ABBREV]
        taxname = json[COL.TAXNAME]
        strain = json[COL.STRAIN]
        family = json[COL.FAMILY]
        taxid = json[COL.TAXID]
        species_taxid = json[COL.SPECIESTAXID]
        source = json[COL.SOURCE]
        version = json[COL.VERSION]

        genus, species, d_strain = naming.split_taxname(taxname)
        d_abbrev = naming.abbrev_dbname(genus, species, strain)
        abbrev = abbrev or d_abbrev
        strain = strain or d_strain

        if debug:
            if abbrev != d_abbrev:
                warn("Non-matching abbreviation: {} / {}".format(abbrev, d_abbrev))

            if strain != d_strain:
                warn("Non-matching strain: {} / {}".format(strain, d_strain))

            genus_species = json[COL.SPECIES]
            d_genus_species = " ".join((genus, species))
            if genus_species != d_genus_species:
                warn("Non-matching species: {} / {}".format(genus_species, d_genus_species))

            d_orthomcl_abbrev = json[COL.ORTHOMCL]
            if orthomcl_abbrev != d_orthomcl_abbrev:
                warn("Non-matching orthomcl abbrev: {} / {}".format(orthomcl_abbrev, d_orthomcl_abbrev))

            is_species_rep = bool_from_sheet(json[COL.ISREFSTRAIN])
            d_is_species_rep = (abbrev == species_rep)
            if is_species_rep != d_is_species_rep:
                warn("Non-matching reference strain: {} / {}".format(abbrev, species_rep))

            is_family_rep = bool_from_sheet(json[COL.ISFAMREP])
            d_is_family_rep = (abbrev == family_rep)
            if is_family_rep != d_is_family_rep:
                warn("Non-matching family representative: {} / {}".format(abbrev, family_rep))

        return cls(abbrev, taxname, strain, family, source, version,
                   taxid, species_taxid,
                   species_rep, family_rep, family_rep_taxid, orthomcl_abbrev)

    def append_to_datasets(self, parent):
        """Mutator: creates subelements for each organism under the parent
        "datasets" element.
        """
        d = xml_dataset(parent, "organism")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismFullName", self.taxname)
        xml_prop(d, "ncbiTaxonId", self.taxid)
        xml_prop(d, "speciesNcbiTaxonId", self.species_taxid)
        xml_prop(d, "organismAbbrev", self.abbrev)
        xml_prop(d, "publicOrganismAbbrev", self.abbrev)
        xml_prop(d, "organismNameForFiles", self.filename)
        xml_prop(d, "strainAbbrev", self.strain_abbrev)
        xml_prop(d, "orthomclAbbrev", self.orthomcl_abbrev)
        xml_prop(d, "taxonHierarchyForBlastxFilter", " ".join(("Eukaryota", "Fungi", self.genus)))
        xml_prop(d, "genomeSource", self.source)
        xml_prop(d, "genomeVersion", self.version)
        # Species representative / reference strain.
        xml_prop(d, "isReferenceStrain", self.is_species_rep)
        xml_prop(d, "referenceStrainOrganismAbbrev", self.species_rep)
        # Family representative.
        xml_prop(d, "isFamilyRepresentative", self.is_family_rep)
        xml_prop(d, "familyRepOrganismAbbrev", self.family_rep)
        xml_prop(d, "familyNcbiTaxonIds", self.family_rep_taxid)
        xml_prop(d, "familyNameForFiles", self.family)
        # May need to add some of these parameters to the spreadsheet if they
        # vary.
        xml_prop(d, "isHaploid", True)
        xml_prop(d, "isAnnotatedGenome", True)
        xml_prop(d, "annotationIncludesTRNAs", False)
        xml_prop(d, "hasDeprecatedGenes", False)
        xml_prop(d, "hasTemporaryNcbiTaxonId", False)
        xml_prop(d, "runExportPred", False)
        xml_prop(d, "isHugeGenome", False)
        xml_prop(d, "maxIntronSize", "1000")

        if self.is_species_rep:
            d = xml_dataset(parent, "referenceStrain")
            xml_prop(d, "organismAbbrev", self.abbrev)
            xml_prop(d, "isAnnotatedGenome", True)


class SpeciesXMLGenerator(object):
    def __init__(self, old_xml, abbrev, taxname, strain,
                 species_rep, family_rep, taxid, species_taxid, family_taxid,
                 source, version, file_format, soterm, idprefix,
                 has_mito, has_products):
        self.old_xml = old_xml
        self.abbrev = abbrev
        self.taxname = taxname
        self.strain = strain
        self.species_rep = species_rep
        self.family_rep = family_rep
        self.taxid = taxid
        self.species_taxid = species_taxid
        self.family_taxid = family_taxid
        self.source = source
        self.version = version
        self.file_format = file_format
        self.soterm = soterm
        self.idprefix = idprefix
        self.has_mito = has_mito
        self.has_products = has_products

        self.strain_abbrev = naming.abbrev_strain(strain)
        self.is_species_rep = (abbrev == species_rep)
        self.is_family_rep = (abbrev == family_rep)

    @classmethod
    def from_json(cls, json, old_xml, species_rep, family_rep, debug=False):
        abbrev = json[COL.ABBREV]
        taxname = json[COL.TAXNAME]
        strain = json[COL.STRAIN]
        taxid = json[COL.TAXID]
        species_taxid = json[COL.SPECIESTAXID]
        family_taxid = json[COL.FAMILYTAXID]
        source = json[COL.SOURCE]
        version = json[COL.VERSION]
        file_format = json[COL.FORMAT]
        soterm = json[COL.SOTERM].lower()
        idprefix = json[COL.IDPREFIX] or ""
        has_mito = bool_from_sheet(json[COL.MITO])
        has_products = bool_from_sheet(json[COL.PRODUCTS])

        genus, species, d_strain = naming.split_taxname(taxname)
        d_abbrev = naming.abbrev_dbname(genus, species, strain)
        abbrev = abbrev or d_abbrev
        strain = strain or d_strain

        if debug:
            if abbrev != d_abbrev:
                warn("Non-matching abbreviation: {} / {}".format(abbrev, d_abbrev))

            if strain != d_strain:
                warn("Non-matching strain: {} / {}".format(strain, d_strain))

            is_species_rep = bool_from_sheet(json[COL.ISREFSTRAIN])
            d_is_species_rep = (abbrev == species_rep)
            if is_species_rep != d_is_species_rep:
                warn("Non-matching reference strain: {} / {}".format(abbrev, species_rep))

            is_family_rep = bool_from_sheet(json[COL.ISFAMREP])
            d_is_family_rep = (abbrev == family_rep)
            if is_family_rep != d_is_family_rep:
                warn("Non-matching family representative: {} / {}".format(abbrev, family_rep))

        return cls(old_xml, abbrev, taxname, strain,
                   species_rep, family_rep, taxid, species_taxid, family_taxid,
                   source, version, file_format, soterm, idprefix,
                   has_mito, has_products)

    def find_and_append(self, parent, lookup):
        for cls in self.old_xml.iterfind('dataset[@class="{}"]'.format(lookup)):
            parent.append(cls)

    def genbank_dataset(self, parent):
        d = xml_dataset(parent, "genbank_primary_genome")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "version", "$$genomeVersion$$")
        xml_prop(d, "name", "$$source$$")
        xml_prop(d, "soTerm", "$$soTerm$$")
        xml_prop(d, "mapFile", "FungiDB/fungiGenbank2gus.xml")
        if self.has_mito:
            d = xml_dataset(parent, "genbank_organelle_genome")
            xml_prop(d, "projectName", "$$projectName$$")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
            xml_prop(d, "version", "$$genomeVersion$$")
            xml_prop(d, "name", "$$source$$")
            xml_prop(d, "soTerm", "mitochondrial_chromosome")
            xml_prop(d, "mapFile", "FungiDB/fungiGenbank2gus.xml")
            xml_prop(d, "organelle", "mitochondrion")

    def fasta_dataset(self, parent):
        d = xml_dataset(parent, "fasta_primary_genome_sequence")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "version", "$$genomeVersion$$")
        xml_prop(d, "name", "$$source$$")
        xml_prop(d, "soTerm", "$$soTerm$$")
        xml_prop(d, "table", "DoTS::ExternalNASequence")
        xml_prop(d, "sourceIdRegex", "^>(\S+)")
        xml_prop(d, "releaseDate", "")
        # Genome features
        d = xml_dataset(parent, "NoPreprocess_primary_genome_features")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "version", "$$genomeVersion$$")
        xml_prop(d, "source", "$$source$$")
        xml_prop(d, "soTerm", "$$soTerm$$")
        xml_prop(d, "mapFile", "FungiDB/genericGFF2Gus.xml")
        if self.has_mito:
            d = xml_dataset(parent, "fasta_organelle_genome")
            xml_prop(d, "projectName", "$$projectName$$")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
            xml_prop(d, "version", "$$genomeVersion$$")
            xml_prop(d, "name", "$$source$$")
            xml_prop(d, "soTerm", "mitochondrial_chromosome")
            xml_prop(d, "table", "DoTS::ExternalNASequence")
            xml_prop(d, "sourceIdRegex", "^>(\S+)")
            xml_prop(d, "organelle", "mitochondrion")

            d = xml_dataset(parent, "NoPreprocess_organelle_genome_features")
            xml_prop(d, "projectName", "$$projectName$$")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
            xml_prop(d, "version", "$$genomeVersion$$")
            xml_prop(d, "name", "$$source$$")
            xml_prop(d, "soTerm", "mitochondrial_chromosome")
            xml_prop(d, "mapFile", "FungiDB/genericGFF2Gus.xml")

    def reference_strain(self, parent):
        d = xml_dataset(parent, "transcriptsFromReferenceStrain")
        xml_prop(d, "referenceStrainOrganismAbbrev", "$$referenceStrainOrganismAbbrev$$")

        d = xml_dataset(parent, "epitopesFromReferenceStrain")
        xml_prop(d, "referenceStrainOrganismAbbrev", "$$referenceStrainOrganismAbbrev$$")

        if self.is_species_rep:
            d = xml_dataset(parent, "referenceStrain-dbEST")
            xml_prop(d, "projectName", "$$projectName$$")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "speciesNcbiTaxonId", "$$speciesNcbiTaxonId$$")

            d = xml_dataset(parent, "referenceStrain-epitope_sequences_IEDB")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "speciesNcbiTaxonId", "$$speciesNcbiTaxonId$$")
            xml_prop(d, "version", "2.4")

            self.find_and_append(parent, "referenceStrain-ESTsFromFasta")

    def family_representative(self, parent):
        d = xml_dataset(parent, "isolatesFromFamilyRepresentative")
        xml_prop(d, "name", "genbank")
        xml_prop(d, "familyRepOrganismAbbrev", "$$familyRepOrganismAbbrev$$")

        if self.is_family_rep:
            d = xml_dataset(parent, "familyRepresentative-isolatesGenbank")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "ncbiTaxonId", "$$familyNcbiTaxonIds$$")

    def compare_old(self, parent):
        attribs = [d.attrib['class'] for d in parent.findall('dataset')]
        for c in self.old_xml.iterfind('dataset'):
            if c.attrib['class'] not in attribs:
                warn("Removed from {}: {}".format(self.abbrev, c.attrib['class']))

    def append_to_datasets(self, parent):
        """Mutator: creates subelements for each dataset under the parent
        "datasets" element.
        """
        # Constants
        xml_constant(parent, "organismAbbrev", self.abbrev)
        xml_constant(parent, "strainAbbrev", self.strain_abbrev)
        xml_constant(parent, "referenceStrainOrganismAbbrev", self.species_rep)
        xml_constant(parent, "familyRepOrganismAbbrev", self.family_rep)
        xml_constant(parent, "projectName", "FungiDB")
        xml_constant(parent, "ncbiTaxonId", self.taxid)
        xml_constant(parent, "speciesNcbiTaxonId", self.species_taxid)
        xml_constant(parent, "familyNcbiTaxonIds", self.family_taxid)
        xml_constant(parent, "genomeVersion", self.version)
        xml_constant(parent, "soTerm", self.soterm)
        xml_constant(parent, "source", self.source)
        xml_constant(parent, "idPrefix", self.idprefix)

        # Organism info
        d = xml_dataset(parent, "validateOrganismInfo")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "strainAbbrev", "$$strainAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "speciesNcbiTaxonId", "$$speciesNcbiTaxonId$$")
        xml_prop(d, "genomeVersion", "$$genomeVersion$$")

        # Genome
        if self.file_format == 'Genbank':
            self.genbank_dataset(parent)
        else:
            self.fasta_dataset(parent)

        # Function
        if self.has_products:
            d = xml_dataset(parent, "productNames")
            xml_prop(d, "projectName", "$$projectName$$")
            xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
            xml_prop(d, "version", "$$genomeVersion$$")
            xml_prop(d, "name", "$$source$$")

        # Other datasets
        for target in ('geneName', 'aliases', 'EnzymeCommissionAssociations',
                       'GeneOntologyAssociations', 'yeastTwoHybrid',
                       'microarrayPlatform', 'microarrayExpressionExperiment',
                       'microarrayPlatformWithProviderMapping',
                       'rnaSeqExperiment', 'SNPs_HTS_Experiment'):
            self.find_and_append(parent, target)

        # Cross-references
        d = xml_dataset(parent, "dbxref_gene2Entrez")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "genomeVersion", "$$genomeVersion$$")
        xml_prop(d, "version", "2011-11-29")

        d = xml_dataset(parent, "dbxref_gene2Uniprot")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "genomeVersion", "$$genomeVersion$$")
        xml_prop(d, "version", "2011-11-29")

        d = xml_dataset(parent, "dbxref_gene2PubmedFromNcbi")
        xml_prop(d, "projectName", "$$projectName$$")
        xml_prop(d, "organismAbbrev", "$$organismAbbrev$$")
        xml_prop(d, "ncbiTaxonId", "$$ncbiTaxonId$$")
        xml_prop(d, "genomeVersion", "$$genomeVersion$$")
        xml_prop(d, "version", "2011-12-17")

        # Custom cross-references
        self.find_and_append(parent, 'dbxref_unity')

        # Reference strain
        self.reference_strain(parent)

        # Family representative
        self.family_representative(parent)

        # Check for any attributes that were left out
        self.compare_old(parent)


class FungiDBXMLGenerator(object):
    """Handles initialization loop to determine representatives and orthomcl
    abbreviations."""
    def __init__(self, json, species_reps, family_reps, orthomcl_abbrevs,
                 orthomcl_version, debug=False):
        self.json = json
        self.species_reps = species_reps
        self.family_reps = family_reps
        self.orthomcl_abbrevs = orthomcl_abbrevs
        self.orthomcl_version = orthomcl_version
        self.debug = debug

    @classmethod
    def from_json(cls, json, orthomcl_version, debug=False):
        species_reps = {}
        family_reps = {}
        orthomcl_abbrevs = {}
        for o in json:
            abbrev = o[COL.ABBREV]
            taxid = o[COL.TAXID]
            taxname = o[COL.TAXNAME]
            orthomcl = o[COL.ORTHOMCL]
            is_species_rep = o[COL.ISREFSTRAIN]
            family = o[COL.FAMILY]
            is_family_rep = o[COL.ISFAMREP]

            genus, species, strain = naming.split_taxname(taxname)
            genus_species = (genus, species)

            if orthomcl:
                orthomcl_abbrevs[(genus, species, strain)] = orthomcl

            if debug:
                species_name = " ".join(genus_species)
                if is_species_rep and genus_species in species_reps:
                    warn("More than one reference strains: {} in {}".format(abbrev, species_name))
                elif not is_species_rep and genus_species not in species_reps:
                    warn("Missing reference strain or out of order: {} in {}".format(abbrev, species_name))

                if is_family_rep and family in family_reps:
                    warn("More than one family representative: {} in {}".format(abbrev, family))

            if is_species_rep:
                species_reps[genus_species] = abbrev
            if is_family_rep:
                family_reps[family] = (abbrev, taxid)

        return cls(json, species_reps, family_reps, orthomcl_abbrevs,
                   orthomcl_version, debug)

    def make_fungidb_xml(self):
        generate_orthomcl_abbrev = naming.OrthoAbbrev(seed=self.orthomcl_abbrevs).abbrev

        datasets = etree.Element("datasets")
        xml_constant(datasets, "projectName", "FungiDB")

        for o in self.json:
            genus, species, strain = naming.split_taxname(o[COL.TAXNAME])
            family = o[COL.FAMILY]
            try:
                species_rep = self.species_reps[(genus, species)]
            except KeyError:
                raise Exception("No reference strain for species: %s" % " ".join((genus, species)))
            try:
                family_rep, family_rep_taxid = self.family_reps[family]
            except KeyError:
                raise Exception("No family representative for family: %s" % family)

            orthomcl_abbrev = generate_orthomcl_abbrev(genus, species, strain)

            g = OrganismXMLGenerator.from_json(o, species_rep, family_rep,
                                               family_rep_taxid,
                                               orthomcl_abbrev, self.debug)
            g.append_to_datasets(datasets)

        for ortho in ("orthomcl", "orthomclPhyletic", "orthomclTree"):
            d = xml_dataset(datasets, ortho)
            xml_prop(d, "projectName", "$$projectName$$")
            xml_prop(d, "version", self.orthomcl_version)

        elementlib.indent(datasets)
        return datasets

    def make_species_xmls(self, outdir):
        for o in self.json:
            abbrev = o[COL.ABBREV]
            family = o[COL.FAMILY]
            genus, species, strain = naming.split_taxname(o[COL.TAXNAME])
            try:
                species_rep = self.species_reps[(genus, species)]
            except KeyError:
                raise Exception("No reference strain for species: %s" % " ".join((genus, species)))
            try:
                family_rep, family_rep_taxid = self.family_reps[family]
            except KeyError:
                raise Exception("No family representative for family: %s" % family)

            filename = os.path.join(outdir, abbrev + '.xml')
            try:
                old_xml = etree.parse(filename)
            except IOError:
                warn("Creating new xml file: %s" % filename)
                old_xml = etree.Element("datasets")

            g = SpeciesXMLGenerator.from_json(o, old_xml, species_rep, family_rep)
            datasets = etree.Element("datasets")
            g.append_to_datasets(datasets)
            elementlib.indent(datasets)
            yield filename, datasets
