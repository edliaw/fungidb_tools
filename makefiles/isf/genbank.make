## Organism:
TAXID         ?= 
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.gbk
ZIP           ?= 
TYPE          ?= 


# Functions:
end_word       = $(word $(shell echo $(words $(2))-$(1)+1 | bc),$(2))
PWDLIST       := $(subst /, ,$(PWD))

ID             = $(call end_word,5,$(PWDLIST))
VERSION        = $(call end_word,2,$(PWDLIST))
SOURCE         = $(call end_word,2,$(subst _, ,$(call end_word,3,$(PWDLIST))))
LONG_TYPE      = $(call end_word,3,$(subst _, ,$(call end_word,3,$(PWDLIST))))


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
XML_MAP       ?= ${PROJECT_HOME}/ApiCommonData/Load/lib/xml/isf/FungiDB/fungiGenbank2gus.xml
ALGFILE       ?= algids
LOG           ?= isf.log


# Derived:
ifeq ($(LONG_TYPE),chromosome)
  TYPE        ?= Chr
  CHR_MAP      = chromosomeMap.txt
  CHR_MAP_OPT  = --chromosomeMapFile $(CHR_MAP)
else ifeq ($(LONG_TYPE),supercontig)
  TYPE        ?= SC
endif

ifdef ZIP
  CAT := zcat
else
  CAT := cat
endif

GENERATE_MAP      = generate_chr_map
SPLIT_ALGIDS      = split_algids --algfile $(ALGFILE)
UNDO_ALGIDS       = undo_algids $(ALGFILE) 2> /dev/null
MAKE_ALGIDS       = cat $(LOG) | $(SPLIT_ALGIDS) --all > /dev/null
# ISF:
COMMIT            = --commit 2>&1 | $(SPLIT_ALGIDS) >> $(LOG) 2>&1
TEST              = >| error.log 2>&1
INSERT_DB         = GUS::Supported::Plugin::InsertExternalDatabase
INSERT_DB_OPTS   ?= --name $(DB_NAME)
INSERT_RL         = GUS::Supported::Plugin::InsertExternalDatabaseRls
INSERT_RL_OPTS   ?= --databaseName $(DB_NAME) --databaseVersion $(VERSION)
INSERT_FEAT       = GUS::Supported::Plugin::InsertSequenceFeatures
INSERT_FEAT_OPTS ?= --extDbName $(DB_NAME) --extDbRlsVer $(VERSION) --mapFile $(XML_MAP) --fileFormat genbank --soCvsVersion 1.417 --organism $(TAXID) --seqSoTerm $(LONG_TYPE) --seqIdColumn source_id --sqlVerbose $(CHR_MAP_OPT) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out
# Undo:
UNDO              = GUS::Community::Plugin::Undo
UNDO_FEAT         = GUS::Supported::Plugin::InsertSequenceFeaturesUndo
UNDO_STR          = $(shell $(UNDO_ALGIDS))
UNDO_ALGID        = $(firstword $(UNDO_STR))
UNDO_PLUGIN       = $(lastword $(UNDO_STR))


files: report.txt $(CHR_MAP)

all: isf
	${MAKE} link

isf:
	${MAKE} insdb-c
	${MAKE} insv-c
	${MAKE} insf-c

clean:
	-rm genome.* report.txt

genome.gbf:
	# Concatenate provider files.
	$(CAT) $(PROVIDER_FILE) >| $@

#chromosomeMap.txt: genome.gbf
	# Generate chromosome map file.
	#$(GENERATE_MAP) $< >| $@

report.txt: genome.gbf
	# View feature qualifiers for genome.gbk.
	reportFeatureQualifiers --format genbank --file_or_dir $< >| $@

link: genome.gbf $(CHR_MAP)
	# Link files to the final directory.
	mkdir -p ../final
	-cd ../final && \
	for file in $^; do \
	  ln -fs ../workspace/$${file}; \
	done


# ISF:
insdb-c:
	ga $(INSERT_DB) $(INSERT_DB_OPTS) $(COMMIT)

insdb:
	# Create species table.
	ga $(INSERT_DB) $(INSERT_DB_OPTS)

insv-c:
	ga $(INSERT_RL) $(INSERT_RL_OPTS) $(COMMIT)

insv:
	# Add version to table.
	ga $(INSERT_RL) $(INSERT_RL_OPTS)

insf-c: genome.gbf $(CHR_MAP)
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) $(COMMIT)

insf: genome.gbf $(CHR_MAP)
	# Insert features and sequences.
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) $(TEST)


# Undoing:
$(ALGFILE): $(LOG)
	$(MAKE_ALGIDS)

undo: $(ALGFILE)
ifeq ($(UNDO_ALGID),)
	@echo "Nothing to undo."
else ifeq ($(UNDO_PLUGIN),$(INSERT_FEAT))
	ga $(UNDO_FEAT) --mapfile $(XML_MAP) --algInvocationId $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)
else
	ga $(UNDO) --plugin $(UNDO_PLUGIN) --algInvocationId $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)
endif


.PHONY: files all isf clean link undo
