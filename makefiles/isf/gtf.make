## Organism: Coprinopsis cinerea okayama7#130
ID            ?= CcinOk7h130
TAXID         ?= 240176
## Source/Data downloaded from:
SOURCE        ?= Broad
TYPE          ?= Chr
VERSION       ?= 3
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.gtf
ZIP           ?= 
MAP_FILE      ?= ../../../*_$(SOURCE)_fasta/$(VERSION)/final/chromosomeMap.txt
## Formatting:
FORMAT_RE     ?= Chromosome_$(VERSION)\.(?:(?P<number>\d+)|(?P<letter>[A-Z]))
FORMAT_PAD    ?= 2
PREFIX_TERM   ?= 


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
ifeq ($(SOURCE), JGI)
  XML_MAP     ?= ${GUS_HOME}/lib/xml/isf/FungiDB/genericGFF2Gus.xml
else
  XML_MAP     ?= ${GUS_HOME}/lib/xml/isf/FungiDB/broadGFF32Gus.xml
endif
LOG           ?= isf.log


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

FORMAT_GTF        = format_gff
FORMAT_GTF_OPTS   ?= --filetype gtf --species $(ID) --type $(TYPE) --provider $(SOURCE) --regex "$(FORMAT_RE)" --padding $(FORMAT_PAD)
GREP_ALGIDS       = grep_algids
GREP_ALGIDS_OPTS  ?= $(LOG)
# ga:
INSERT_FEAT       = GUS::Supported::Plugin::InsertSequenceFeatures
INSERT_FEAT_OPTS  ?= --extDbName $(DB_NAME) --extDbRlsVer $(VERSION) --mapFile $(XML_MAP) --inputFileExtension gff --fileFormat gff3 --soCvsVersion 1.417 --organism $(TAXID) --seqSoTerm $(LONG_TYPE) --seqIdColumn source_id --naSequenceSubclass ExternalNASequence --sqlVerbose $(CHR_MAP_OPT) 
UNDO              = GUS::Supported::Plugin::InsertSequenceFeaturesUndo

ifeq ($(SOURCE), JGI)
  FORMAT_GTF_OPTS += --nostart
endif


files: report.txt $(CHR_MAP)

all: isf
	${MAKE} link

isf: insertf-c

clean:
	rm genome.* report.txt $(CHR_MAP)

genome.gtf:
	# Copy provider file and rename the id and source (first two columns).
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_GTF) $(FORMAT_GTF_OPTS) >| $@

genome.gff3: genome.gtf
ifeq ($(SOURCE), JGI)
	# JGI GTF transcript ids need to be prefixed when converting.
	gtf2gff3_3level.pl -prefix $(PREFIX_TERM) $< >| $@
else
        # Convert Broad GTF to GFF3 format.
	convertGTFToGFF3 $< >| $@
endif

genome.gff: genome.gff3
	# Convert GFF3 to pseudo GFF3 format (compatible with ISF).
	preprocessGFF3 --input_gff $< --output_gff $@

chromosomeMap.txt:
	# Copy the chromosome map file
	cp $(MAP_FILE) $@

report.txt: genome.gff
	# Generate feature qualifiers for genome.gff.
	reportFeatureQualifiers --format gff3 --file_or_dir $< >| $@

link: genome.gtf $(CHR_MAP)
	# Link files to the final directory.
	mkdir -p ../final
	cd ../final && \
	for file in $^; do \
	  ln -s ../workspace/$$file; \
	done

insertf-c: genome.gff $(CHR_MAP)
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out --commit >> $(LOG) 2>&1

insertf: genome.gff $(CHR_MAP)
	# Run ISF to insert features.
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out >| error.log 2>&1


# Undoing:
algid:
	$(GREP_ALGIDS) $(GREP_ALGIDS_OPTS)

insertf-u%-c:
	ga $(UNDO) --mapfile $(XML_MAP) --algInvocationId $* --commit

insertf-u%:
	# Undo feature insertion.
	ga $(UNDO) --mapfile $(XML_MAP) --algInvocationId $*


.PHONY: files all isf clean link algid insertf insertf-c insertf-u% insertf-u%-c
