## Organism:
TAXID         ?= 
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.fasta
ZIP           ?= 
## Formatting:
TYPE          ?= 
FORMAT_RE     ?= "$(firstword $(TYPE))(?:(?P<number>\d+)|(?P<roman>[XIV]+)|(?P<letter>[A-Z]))_"
FORMAT_PAD    ?= 2


# Functions:
end_word       = $(word $(shell echo $(words $(2))-$(1)+1 | bc),$(2))
PWDLIST       := $(subst /, ,$(PWD))

ID             = $(call end_word,5,$(PWDLIST))
VERSION        = $(call end_word,2,$(PWDLIST))
SOURCE         = $(call end_word,2,$(subst _, ,$(call end_word,3,$(PWDLIST))))
LONG_TYPE      = $(call end_word,3,$(subst _, ,$(call end_word,3,$(PWDLIST))))


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
ALGFILE       ?= algids
LOG           ?= isf.log


# Derived:
ifeq ($(LONG_TYPE),chromosome)
  TYPE        ?= Chr
else ifeq ($(LONG_TYPE),supercontig)
  TYPE        ?= SC
endif

ifdef ZIP
  CAT := zcat
else
  CAT := cat
endif

FORMAT_FASTA      = format_fasta --species $(ID) --padding $(FORMAT_PAD) --soterm $(TYPE) --regex $(FORMAT_RE)
GENERATE_MAP      = generate_chr_map
SPLIT_ALGIDS      = split_algids
UNDO_ALGIDS       = undo_algids $(ALGFILE) 2> /dev/null
MAKE_ALGIDS       = $(SPLIT_ALGIDS) --all < $(LOG) >> $(ALGFILE)
# ISF:
COMMIT            = --commit 2>&1 | tee -a $(LOG) | $(SPLIT_ALGIDS) >> $(ALGFILE)
TEST              = >| error.log 2>&1
INSERT_DB         = GUS::Supported::Plugin::InsertExternalDatabase
INSERT_DB_OPTS   ?= --name $(DB_NAME)
INSERT_RL         = GUS::Supported::Plugin::InsertExternalDatabaseRls
INSERT_RL_OPTS   ?= --databaseName $(DB_NAME) --databaseVersion $(VERSION)
LOAD_SEQS         = GUS::Supported::Plugin::LoadFastaSequences
LOAD_SEQS_OPTS   ?= --externalDatabaseName $(DB_NAME) --ncbiTaxId $(TAXID) --externalDatabaseVersion $(VERSION) --SOTermName $(LONG_TYPE) --regexSourceId '>(\S+)' --tableName DoTS::ExternalNASequence --debug --chromosomeMapFile chromosomeMap.txt --sequenceFile $<
# Undo:
UNDO              = GUS::Community::Plugin::Undo
UNDO_STR          = $(shell $(UNDO_ALGIDS))
UNDO_ALGID        = $(firstword $(UNDO_STR))
UNDO_PLUGIN       = $(lastword $(UNDO_STR))


files: genome.fasta chromosomeMap.txt

all: isf
	${MAKE} link

isf:
	${MAKE} insdb-c
	${MAKE} insv-c
	${MAKE} load-c

clean:
	-rm genome.* chromosomeMap.txt

genome.fasta:
	# Copy provider file and reformat headers
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_FASTA) >| $@

chromosomeMap.txt: genome.fasta
	# Generate chromosome map file.
ifeq ($(LONG_TYPE),chromosome)
	$(GENERATE_MAP) $< >| $@
else
	touch $@
endif

link: genome.fasta chromosomeMap.txt
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

load-c: genome.fasta chromosomeMap.txt
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) $(COMMIT)

load: genome.fasta chromosomeMap.txt
	# Load data into table.
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) $(TEST)


# Undoing:
$(ALGFILE): $(LOG)
	$(MAKE_ALGIDS)

undo: $(ALGFILE)
ifeq ($(UNDO_ALGID),)
	@echo "Nothing to undo."
else
	ga $(UNDO) --plugin $(UNDO_PLUGIN) --algInvocationID $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)
endif


.PHONY: files all isf clean link undo
