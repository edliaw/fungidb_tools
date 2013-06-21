ID      ?= Test
SOURCE  ?= Broad
TYPE    ?= SC
FORMAT  ?= gtf
VERSION ?= 6

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
  LONG_TYPE = mitochondrial
endif


# Constants
BASE_DIRS = bindingSites cellularLocation chipChip chipSeq comparativeGenomics dbxref dnaSeq epitope EST function genePrediction genome genomeFeature interaction isolate massSpec microarrayExpression microarrayPlatform mRNA phenotype phylogeny reagent rnaSeq sageTag SNP structure
WORK_DIRS = final fromProvider workspace
FUNCTION_NAMES = KEGG GO


# Recipes
.PHONY : all basedirs genome genome_% function products function_%

all : basedirs genome function

$(ID) :
	mkdir $(ID)

BASE_PATHS = $(addprefix $(ID)/,$(BASE_DIRS))
$(BASE_PATHS) : | $(ID)
	mkdir $@

basedirs : $(BASE_PATHS) ;

%_working :
	# Make final, workspace, and fromProvider dirs in this path.
	mkdir -p $*
	cd $* && mkdir -p $(WORK_DIRS)

genome :
	# Make genomic data dirs: working directories for each file type.
	for ext in $(EXT); do \
	  ${MAKE} genome_$$ext; \
	done

genome_% : GENOME_DIR = $(ID)/genome/$(LONG_TYPE)_$(SOURCE)_$*/$(VERSION)
genome_% :
	${MAKE} $(GENOME_DIR)_working

function :
	# Make functional data dirs: product names, KEGG, GO, etc.
	${MAKE} products
	for dir in $(FUNCTION_NAMES); do \
	  ${MAKE} function_$$dir; \
	done

products : PRODUCT_DIR = $(ID)/function/$(SOURCE)_product_names/$(VERSION)
products :
	${MAKE} $(PRODUCT_DIR)_working

function_% : FUNCTION_DIR = $(ID)/function/$(SOURCE)_$*
function_% :
	mkdir $(FUNCTION_DIR)
