## Organism: Aspergillus fumigatus Af293
ID            ?= AfumAF293B
TAXID         ?= 330879
## Source/Data downloaded from:
SOURCE        ?= AspGD
VERSION       ?= s03-m02-r18
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.fasta
ZIP           ?= 
## Formatting:
TYPE          ?= Chr
FORMAT_RE     ?= "(?P<type>Chr)(?:(?P<number>\d+)|(?P<roman>[XIV]+)|(?P<letter>[A-Z]))_(?P<species>\w+)"
FORMAT_PAD    ?= 2


# Constants:
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

DB_NAME           ?= $(ID)_genome_RSRC
LOG               ?= isf.log
FORMAT_FASTA      = format_fasta
FORMAT_FASTA_OPTS ?= --species $(ID) --padding $(FORMAT_PAD) --soterm $(TYPE) --regex $(FORMAT_RE)
GENERATE_MAP      = generate_chr_map
GENERATE_MAP_OPTS ?= genome.fasta
GREP_ALGIDS       = grep_algids
GREP_ALGIDS_OPTS  ?= $(LOG)
# ga:
INSERT_DB         = GUS::Supported::Plugin::InsertExternalDatabase
INSERT_DB_OPTS    ?= --name $(DB_NAME)
INSERT_RL         = GUS::Supported::Plugin::InsertExternalDatabaseRls
INSERT_RL_OPTS    ?= --databaseName $(DB_NAME) --databaseVersion $(VERSION)
LOAD_SEQS         = GUS::Supported::Plugin::LoadFastaSequences
LOAD_SEQS_OPTS    ?= --externalDatabaseName $(DB_NAME) --ncbiTaxId $(TAXID) --externalDatabaseVersion $(VERSION) --SOTermName $(LONG_TYPE) --regexSourceId '>(\S+)' --tableName DoTS::ExternalNASequence --sqlVerbose --debug $(CHR_MAP_OPT)
UNDO              = GUS::Community::Plugin::Undo


files: genome.fasta $(CHR_MAP)

all: isf
	${MAKE} link

isf:
	${MAKE} insdb-c
	${MAKE} insv-c
	${MAKE} load-c

clean:
	rm genome.* $(CHR_MAP)

genome.fasta:
	# Filter out mitochondrial contigs and reformatted headers.
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_FASTA) $(FORMAT_FASTA_OPTS) >| $@

chromosomeMap.txt: genome.fasta
	# Generate chromosome map file.
	$(GENERATE_MAP) $(GENERATE_MAP_OPTS) >| $@

link: genome.fasta $(CHR_MAP)
	# Link files to the final directory.
	mkdir -p ../final
	cd ../final && \
	for file in $^; do \
	  ln -s ../workspace/$${file}; \
	done


# ISF:
insdb-c:
	ga $(INSERT_DB) $(INSERT_DB_OPTS) --commit >> $(LOG) 2>&1

insdb:
	# Insert species table.
	ga $(INSERT_DB) $(INSERT_DB_OPTS)

insv-c:
	ga $(INSERT_RL) $(INSERT_RL_OPTS) --commit >> $(LOG) 2>&1

insv:
	# Add version to table.
	ga $(INSERT_RL) $(INSERT_RL_OPTS)

load-c: genome.fasta $(CHR_MAP)
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) --sequenceFile $< --commit >> $(LOG) 2>&1

load: genome.fasta $(CHR_MAP)
	# Load data into table.
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) --sequenceFile $< >| error.log 2>&1


# Undoing:
algid:
	$(GREP_ALGIDS) $(GREP_ALGIDS_OPTS)

load-u%-c:
	ga $(UNDO) --plugin $(LOAD_SEQS) --algInvocationId $* --commit

load-u%:
	# Undo sequence loading.
	ga $(UNDO) --plugin $(LOAD_SEQS) --algInvocationId $*

insv-u%-c:
	ga $(UNDO) --plugin $(INSERT_RL) --algInvocationId $* --commit

insv-u%:
	# Undo versioning.
	ga $(UNDO) --plugin $(INSERT_RL) --algInvocationId $*

insdb-u%-c:
	ga $(UNDO) --plugin $(INSERT_DB) --algInvocationId $* --commit

insdb-u%:
	# Undo species table.
	ga $(UNDO) --plugin $(INSERT_DB) --algInvocationId $*


.PHONY: files all isf clean link algid insdb insdb-c insv insv-c load load-c
