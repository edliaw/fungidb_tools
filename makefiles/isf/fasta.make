## Organism: Aspergillus fumigatus Af293
ID            ?= AfumAF293B
TAXID         ?= 330879
## Source/Data downloaded from:
SOURCE        ?= AspGD
TYPE          ?= Chr
VERSION       ?= s03-m02-r18
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.fasta
ZIP           ?= 
## Formatting:
FORMAT_RE     ?= (?P<type>Chr)(?:(?P<number>\d+)|(?P<letter>[A-Z]))_(?P<species>\w+)
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
FORMAT_FASTA_OPTS ?= --species $(ID) --type $(TYPE) --regex "$(FORMAT_RE)" --padding $(FORMAT_PAD)
GENERATE_MAP      = generate_chr_map
GENERATE_MAP_OPTS ?= genome.fasta
GREP_ALGIDS       = grep_algids
GREP_ALGIDS_OPTS  ?= $(LOG)
# ga:
INSERT_DB         = GUS::Supported::Plugin::InsertExternalDatabase
INSERT_DB_OPTS    ?= --name $(DB_NAME)
INSERT_RI         = GUS::Supported::Plugin::InsertExternalDatabaseRls
INSERT_RI_OPTS    ?= --databaseName $(DB_NAME) --databaseVersion $(VERSION)
LOAD_SEQS         = GUS::Supported::Plugin::LoadFastaSequences
LOAD_SEQS_OPTS    ?= --externalDatabaseName $(DB_NAME) --ncbiTaxId $(TAXID) --externalDatabaseVersion $(VERSION) --SOTermName $(LONG_TYPE) --regexSourceId '>(\S+)' --tableName DoTS::ExternalNASequence --sqlVerbose --debug $(CHR_MAP_OPT)
UNDO              = GUS::Community::Plugin::Undo


# Recipes:
.PHONY : all isf files clean link algid insertdb insertdb-c insertdb-u% insertdb-u%-c insertri insertri-c insertri-u% insertri-u%-c loadseqs loadseqs-c loadseqs-u% loadseqs-u%-c

all : isf
	${MAKE} link

isf :
	${MAKE} insertdb-c
	${MAKE} insertri-c
	${MAKE} loadseqs-c

files : genome.fasta $(CHR_MAP)

clean :
	rm genome.* $(CHR_MAP)

genome.fasta :
	# Filter out mitochondrial contigs and reformatted headers.
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_FASTA) $(FORMAT_FASTA_OPTS) >| $@

chromosomeMap.txt : genome.fasta
	# Generate chromosome map file.
	$(GENERATE_MAP) $(GENERATE_MAP_OPTS) >| $@

link : genome.fasta $(CHR_MAP)
	# Link files to the final directory.
	mkdir -p ../final
	cd ../final && \
	for file in $^; do \
	  ln -s ../workspace/$$file; \
	done


# ISF:
insertdb-c :
	ga $(INSERT_DB) $(INSERT_DB_OPTS) --commit >> $(LOG) 2>&1

insertdb :
	# Insert species table.
	ga $(INSERT_DB) $(INSERT_DB_OPTS)

insertri-c :
	ga $(INSERT_RI) $(INSERT_RI_OPTS) --commit >> $(LOG) 2>&1

insertri :
	# Add version to table.
	ga $(INSERT_RI) $(INSERT_RI_OPTS)

loadseqs-c : genome.fasta $(CHR_MAP)
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) --sequenceFile genome.fasta --commit >> $(LOG) 2>&1

loadseqs : genome.fasta $(CHR_MAP)
	# Load data into table.
	ga $(LOAD_SEQS) $(LOAD_SEQS_OPTS) --sequenceFile genome.fasta >| error.log 2>&1


# Undoing:
algid :
	$(GREP_ALGIDS) $(GREP_ALGIDS_OPTS)

loadseqs-u%-c :
	ga $(UNDO) --plugin $(LOAD_SEQS) --algInvocationId $* --commit

loadseqs-u% :
	# Undo sequence loading.
	ga $(UNDO) --plugin $(LOAD_SEQS) --algInvocationId $*

insertri-u%-c :
	ga $(UNDO) --plugin $(INSERT_RI) --algInvocationId $* --commit

insertri-u% :
	# Undo versioning.
	ga $(UNDO) --plugin $(INSERT_RI) --algInvocationId $*

insertdb-u%-c :
	ga $(UNDO) --plugin $(INSERT_DB) --algInvocationId $* --commit

insertdb-u% :
	# Undo species table.
	ga $(UNDO) --plugin $(INSERT_DB) --algInvocationId $*
