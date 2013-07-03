## Organism: Trichoderma reesei QM6a
ID            ?= TreeQM6a
TAXID         ?= 431241
## Source/Data downloaded from:
SOURCE        ?= JGI
TYPE          ?= SC
VERSION       ?= 2
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.gbk.gz
ZIP           ?= 


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
LOG           ?= isf.log
XML_MAP       ?= ${PROJECT_HOME}/ApiCommonData/Load/lib/xml/isf/FungiDB/fungiGenbank2gus.xml


# Derived:
ifeq ($(TYPE), Chr)
  LONG_TYPE     = chromosome
  CHR_MAP       = chromosomeMap.txt
  CHR_MAP_OPT   = --chromosomeMapFile $(CHR_MAP)
else ifeq ($(TYPE), SC)
  LONG_TYPE     = supercontig
endif

ifeq ($(ZIP), true)
  CAT := zcat
else
  CAT := cat
endif

GREP_ALGIDS       = grep_algids
GREP_ALGIDS_OPTS  ?= $(LOG)
# ga:
INSERT_DB         = GUS::Supported::Plugin::InsertExternalDatabase
INSERT_DB_OPTS    ?= --name $(DB_NAME)
INSERT_RI         = GUS::Supported::Plugin::InsertExternalDatabaseRls
INSERT_RI_OPTS    ?= --databaseName $(DB_NAME) --databaseVersion $(VERSION)
INSERT_FEAT       = GUS::Supported::Plugin::InsertSequenceFeatures
INSERT_FEAT_OPTS  ?= --extDbName $(DB_NAME) --extDbRlsVer $(VERSION) --mapFile $(XML_MAP) --fileFormat genbank --soCvsVersion 1.417 --organism $(TAXID) --seqSoTerm $(LONG_TYPE) --seqIdColumn source_id --sqlVerbose
UNDO              = GUS::Community::Plugin::Undo
UNDO_INSERTF      = GUS::Supported::Plugin::InsertSequenceFeaturesUndo


files: report.txt

all: isf
	${MAKE} link

isf:
	${MAKE} insertdb-c
	${MAKE} insertri-c
	${MAKE} insertf-c

clean:
	rm genome.* report.txt

genome.gbf:
	# Concatenate files and filter out mitochondrial contigs.
	$(CAT) $(PROVIDER_FILE) >| $@

report.txt: genome.gbf
	# Generate feature report.
	reportFeatureQualifiers --format genbank --file_or_dir $< >| $@

link: genome.gbf
	# Link files to the final directory.
	mkdir -p ../final
	cd ../final && \
	for file in $^; do \
	  ln -s ../workspace/$$file; \
	done


# ISF:
insertdb-c:
	ga $(INSERT_DB) $(INSERT_DB_OPTS) --commit >> $(LOG) 2>&1

insertdb:
	# Insert species table.
	ga $(INSERT_DB) $(INSERT_DB_OPTS)

insertri-c:
	ga $(INSERT_RI) $(INSERT_RI_OPTS) --commit >> $(LOG) 2>&1

insertri:
	# Add version to table.
	ga $(INSERT_RI) $(INSERT_RI_OPTS)

insertf-c: genome.gbf
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out --commit >> $(LOG) 2>&1

insertf: genome.gbf
	# Run ISF to insert features.
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out >| error.log 2>&1


# Undoing:
algid:
	$(GREP_ALGIDS) $(GREP_ALGIDS_OPTS)

insertf-u%-c:
	ga $(UNDO_INSERTF) --mapfile $(XML_MAP) --algInvocationId $* --commit

insertf-u%:
	# Undo feature insertion.
	ga $(UNDO_INSERTF) --mapfile $(XML_MAP) --algInvocationId $*

insertri-u%-c:
	ga $(UNDO) --plugin $(INSERT_RI) --algInvocationId $* --commit

insertri-u%:
	# Undo versioning.
	ga $(UNDO) --plugin $(INSERT_RI) --algInvocationId $*

insertdb-u%-c:
	ga $(UNDO) --plugin $(INSERT_DB) --algInvocationId $* --commit

insertdb-u%:
	# Undo species table.
	ga $(UNDO) --plugin $(INSERT_DB) --algInvocationId $*


.PHONY: files all isf clean link algid insertdb insertdb-c insertdb-u% insertdb-u%-c insertri insertri-c insertri-u% insertri-u%-c insertf insertf-c insertf-u% insertf-u%-c
