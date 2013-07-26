## Organism:
TAXID         ?= 
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.fasta
ZIP           ?= 
## Formatting:
TYPE          ?= Chr
FORMAT_RE     ?= "$(firstword $(TYPE))(?:(?P<number>\d+)|(?P<roman>[XIV]+)|(?P<letter>[A-Z]))_"
FORMAT_PAD    ?= 2


# Functions:
from_end       = $(word $(shell echo $(words $(1))-$(2) | bc),$(1))
PWDLIST       := $(subst /, ,$(PWD))
ID             = $(call from_end,$(PWDLIST),4)
VERSION        = $(call from_end,$(PWDLIST),1)
SOURCE         = $(word 2,$(subst _, ,$(call from_end,$(PWDLIST),2)))


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
ALGFILE       ?= algids
LOG           ?= isf.log


# Derived:
ifeq ($(firstword $(TYPE)), Chr)
  LONG_TYPE    = chromosome
  CHR_MAP      = chromosomeMap.txt
  CHR_MAP_OPT  = --chromosomeMapFile $(CHR_MAP)
else ifeq ($(firstword $(TYPE)), SC)
  LONG_TYPE    = supercontig
endif

ifeq ($(ZIP), true)
  CAT := zcat
else
  CAT := cat
endif

FORMAT_FASTA      = format_fasta --species $(ID) --padding $(FORMAT_PAD) --soterm $(TYPE) --regex $(FORMAT_RE)
GENERATE_MAP      = generate_chr_map
SPLIT_ALGIDS      = split_algids --algfile $(ALGFILE)
UNDO_ALGIDS       = undo_algids $(ALGFILE)
MAKE_ALGIDS       = cat $(LOG) | $(SPLIT_ALGIDS) --all > /dev/null
# ISF:
COMMIT            = --commit | $(SPLIT_ALGIDS) >> $(LOG) 2>&1
TEST              = >| error.log 2>&1
INSERT_DB         = GUS::Supported::Plugin::InsertExternalDatabase
INSERT_DB_OPTS   ?= --name $(DB_NAME)
INSERT_RL         = GUS::Supported::Plugin::InsertExternalDatabaseRls
INSERT_RL_OPTS   ?= --databaseName $(DB_NAME) --databaseVersion $(VERSION)
LOAD_SEQS         = GUS::Supported::Plugin::LoadFastaSequences
LOAD_SEQS_OPTS   ?= --externalDatabaseName $(DB_NAME) --ncbiTaxId $(TAXID) --externalDatabaseVersion $(VERSION) --SOTermName $(LONG_TYPE) --regexSourceId '>(\S+)' --tableName DoTS::ExternalNASequence --sqlVerbose --debug $(CHR_MAP_OPT) --sequenceFile $<
# Undo:
UNDO              = GUS::Community::Plugin::Undo
UNDO_STR          = $(shell $(UNDO_ALGIDS))
UNDO_ALGID        = $(firstword $(UNDO_STR))
UNDO_PLUGIN       = $(lastword $(UNDO_STR))


files: genome.fasta $(CHR_MAP)

all: isf
	${MAKE} link

isf:
	${MAKE} insdb-c
	${MAKE} insv-c
	${MAKE} load-c

clean:
	-rm genome.* $(CHR_MAP)

genome.fasta:
	# Filter out mitochondrial contigs and reformatted headers.
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_FASTA) >| $@

chromosomeMap.txt: genome.fasta
	# Generate chromosome map file.
	$(GENERATE_MAP) $< >| $@

link: genome.fasta $(CHR_MAP)
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
	# Insert species table.
	ga $(INSERT_DB) $(INSERT_DB_OPTS)

insv-c:
	ga $(INSERT_RL) $(INSERT_RL_OPTS) $(COMMIT)

insv:
	# Add version to table.
	ga $(INSERT_RL) $(INSERT_RL_OPTS)

load-c: genome.fasta $(CHR_MAP)
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) $(COMMIT)

load: genome.fasta $(CHR_MAP)
	# Load data into table.
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) $(TEST)


# Undoing:
$(ALGFILE): $(LOG)
	$(MAKE_ALGIDS)

undo: $(ALGFILE)
	ga $(UNDO) --plugin $(UNDO_PLUGIN) --algInvocationID $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)


.PHONY: files all isf clean link undo
