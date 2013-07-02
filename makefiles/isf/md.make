ID       ?= Test
SOURCE   ?= Broad
TYPE     ?= SC
FORMAT   ?= gtf
VERSION  ?= 6

# FORMAT = gff3, gtf, or gbf
ifeq ($(FORMAT), gff3)
  EXT = gff3 fasta
else ifeq ($(FORMAT), gtf)
  EXT = gff3 fasta
else ifeq ($(FORMAT), gbf)
  EXT = genbank
else
  EXT = $(FORMAT)
endif

# TYPE = SC, Chr, or Mito
ifeq ($(TYPE), SC)
  LONG_TYPE = supercontig
else ifeq ($(TYPE), Chr)
  LONG_TYPE = chromosome
else ifeq ($(TYPE), Mito)
  TYPE = Chr
  LONG_TYPE = mitochondrial
endif

MAKEFILES = /home/edliaw/repo/fungidb_tools/makefiles/isf


# Directory names:
BASE_DIRS = bindingSites cellularLocation chipChip chipSeq comparativeGenomics dbxref dnaSeq epitope EST function genePrediction genome genomeFeature interaction isolate massSpec microarrayExpression microarrayPlatform mRNA phenotype phylogeny reagent rnaSeq sageTag SNP structure
FUNCTION_NAMES = KEGG GO product_names
WORK_DIRS = workspace final fromProvider

GENOME_DIRS = $(addprefix $(LONG_TYPE)_$(SOURCE)_,$(EXT))
FUNCTION_DIRS = $(addprefix $(SOURCE)_,$(FUNCTION_NAMES))


# Shortcut recipes:
all: basedirs genome product function ;

# Make all the base directories for this organism.
basedirs: $(BASE_PATHS) ;

GENOME_EXT = $(addprefix genome_,$(EXT))
genome: $(GENOME_EXT) ;

function: $(FUNCTION_PATHS) ;


# Directory structure:
$(ID):
	mkdir $@

BASE_PATHS = $(addprefix $(ID)/,$(BASE_DIRS))
$(BASE_PATHS): | $(ID)
	mkdir $@

GENOME_ROOT = $(ID)/genome
GENOME_PATHS = $(addprefix $(GENOME_ROOT)/,$(GENOME_DIRS))
$(GENOME_PATHS): | $(GENOME_ROOT)
	mkdir $@

FUNCTION_ROOT = $(ID)/function
FUNCTION_PATHS = $(addprefix $(FUNCTION_ROOT)/,$(FUNCTION_DIRS))
$(FUNCTION_PATHS): | $(FUNCTION_ROOT)
	mkdir $@

VERSION_PATH = $(addprefix %/,$(VERSION))
$(VERSION_PATH): | %
	mkdir $@

WORK_PATHS = $(addprefix %/,$(WORK_DIRS))
$(WORK_PATHS): | %
	mkdir -p $(addprefix $*/,$(WORK_DIRS))

%/Makefile: | %
	touch $@

GENOME_MAKE = $(GENOME_ROOT)/$(LONG_TYPE)_$(SOURCE)_%/$(VERSION)/workspace/Makefile
genome_%: $(GENOME_MAKE)
	echo "# Organism: " >> $<
	echo "ID      = $(ID)" >> $<
	echo "TAXID   = " >> $<
	echo "# Source/Data downloaded from:" >> $<
	echo "SOURCE  = $(SOURCE)" >> $<
	echo "TYPE    = $(TYPE)" >> $<
	echo "# Version:" >> $<
	echo "VERSION = $(VERSION)" >> $<
	echo "# Target file:" >> $<
	echo "PROVIDER_FILE = " >> $<
	echo "ZIP           = " >> $<
	echo "include $(MAKEFILES)/$*.make" >> $<


PRODUCT_MAKE = $(FUNCTION_ROOT)/$(SOURCE)_product_names/$(VERSION)/workspace/Makefile
product: $(PRODUCT_MAKE)
	echo "# Organism: " >> $<
	echo "ID      = $(ID)" >> $<
	echo "SOURCE  = $(SOURCE)" >> $<
	echo "VERSION = $(VERSION)" >> $<
	echo "# Target file:" >> $<
	echo "PROVIDER_FILE = " >> $<
	echo "ZIP           = " >> $<
	echo "include $(MAKEFILES)/product_names.make" >> $<


.SECONDARY:
.PHONY: all basedirs genome product function genome_%
