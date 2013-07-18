## Organism: Aspergillus fumigatus Af293
ID            ?= AfumAF293B
TAXID         ?= 330879
## Source/Data downloaded from:
SOURCE        ?= AspGD
TYPE          ?= Chr
VERSION       ?= s03-m02-r18
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.gff3
ZIP           ?= 
MAP_FILE      ?= ../../../*_$(SOURCE)_fasta/$(VERSION)/final/chromosomeMap.txt
## Formatting:
FORMAT_RE     ?= $(TYPE)(?:(?P<number>\d+)|(?P<letter>[A-Z]))
FORMAT_PAD    ?= 2
FORMAT_ROMAN  ?=


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
XML_MAP       ?= ${GUS_HOME}/lib/xml/isf/FungiDB/genericGFF2Gus.xml
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

FORMAT_GFF3       = format_gff
FORMAT_GFF3_OPTS  ?= --filetype gff3 --species $(ID) --type $(TYPE) --provider $(SOURCE) --regex "$(FORMAT_RE)" --padding $(FORMAT_PAD) --comments
ifdef PREFIX
  FORMAT_GFF3_OPTS  += --prefix $(PREFIX)
endif
GREP_ALGIDS       = grep_algids
GREP_ALGIDS_OPTS  ?= $(LOG)
# ga:
INSERT_FEAT       = GUS::Supported::Plugin::InsertSequenceFeatures
INSERT_FEAT_OPTS  ?= --extDbName $(DB_NAME) --extDbRlsVer $(VERSION) --mapFile $(XML_MAP) --inputFileExtension gff --fileFormat gff3 --soCvsVersion 1.417 --organism $(TAXID) --seqSoTerm $(LONG_TYPE) --seqIdColumn source_id --naSequenceSubclass ExternalNASequence --sqlVerbose $(CHR_MAP_OPT)
UNDO              = GUS::Supported::Plugin::InsertSequenceFeaturesUndo

ifeq ($(FORMAT_ROMAN), true)
  FORMAT_GTF_OPTS += --roman
endif


files: report.txt $(CHR_MAP)

all: isf
	${MAKE} link

isf: insertf-c

clean:
	rm genome.* report.txt $(CHR_MAP)

genome.gff3:
	# Copy provider file and rename the id and source (first two columns).
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_GFF3) $(FORMAT_GFF3_OPTS) >| $@

genome.gff: genome.gff3
	# Convert GFF3 to pseudo GFF3 format (compatible with ISF).
	preprocessGFF3 --input_gff $< --output_gff $@

chromosomeMap.txt:
	# Copy the chromosome map file
	cp $(MAP_FILE) $@

report.txt: genome.gff
	# Generate feature qualifiers for genome.gff.
	reportFeatureQualifiers --format gff3 --file_or_dir $< >| $@

link: genome.gff $(CHR_MAP)
	# Link files to the final directory.
	mkdir -p ../final
	cd ../final && \
	for file in $^; do \
	  ln -s ../workspace/$${file}; \
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
