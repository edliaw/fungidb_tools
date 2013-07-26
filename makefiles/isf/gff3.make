## Organism:
TAXID         ?= 
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.gff3
ZIP           ?= 
MAP_FILE      ?= ../../../*_$(SOURCE)_fasta/$(VERSION)/final/chromosomeMap.txt
## Formatting:
TYPE          ?= Chr
FORMAT_RE     ?= "$(firstword $(TYPE))(?:(?P<number>\d+)|(?P<roman>[XIV]+)|(?P<letter>[A-Z]))"
FORMAT_PAD    ?= 2


# Functions:
from_end       = $(word $(shell echo $(words $(1))-$(2) | bc),$(1))
PWDLIST       := $(subst /, ,$(PWD))
ID             = $(call from_end,$(PWDLIST),4)
VERSION        = $(call from_end,$(PWDLIST),1)
SOURCE         = $(word 2,$(subst _, ,$(call from_end,$(PWDLIST),2)))


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
XML_MAP       ?= ${GUS_HOME}/lib/xml/isf/FungiDB/genericGFF2Gus.xml
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

FORMAT_GFF3       = format_gff --filetype gff3 --species $(ID) --provider $(SOURCE) --padding $(FORMAT_PAD) --soterm $(TYPE) --regex $(FORMAT_RE) --comments
SPLIT_ALGIDS      = split_algids --algfile $(ALGFILE)
UNDO_ALGIDS       = undo_algids $(ALGFILE)
MAKE_ALGIDS       = cat $(LOG) | $(SPLIT_ALGIDS) --all > /dev/null
# ISF:
COMMIT            = --commit | $(SPLIT_ALGIDS) >> $(LOG) 2>&1
TEST              = >| error.log 2>&1
INSERT_FEAT       = GUS::Supported::Plugin::InsertSequenceFeatures
INSERT_FEAT_OPTS ?= --extDbName $(DB_NAME) --extDbRlsVer $(VERSION) --mapFile $(XML_MAP) --inputFileExtension gff --fileFormat gff3 --soCvsVersion 1.417 --organism $(TAXID) --seqSoTerm $(LONG_TYPE) --seqIdColumn source_id --naSequenceSubclass ExternalNASequence --sqlVerbose $(CHR_MAP_OPT) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out --commit
# Undo:
UNDO              = GUS::Supported::Plugin::InsertSequenceFeaturesUndo
UNDO_STR          = $(shell $(UNDO_ALGIDS))
UNDO_ALGID        = $(firstword $(UNDO_STR))
UNDO_PLUGIN       = $(lastword $(UNDO_STR))

ifdef PREFIX
  FORMAT_GFF3 += --prefix $(PREFIX)
endif


files: report.txt $(CHR_MAP)

all: isf
	${MAKE} link

isf: insf-c

clean:
	-rm genome.* report.txt $(CHR_MAP)

genome.gff3:
	# Copy provider file and rename the id and source (first two columns).
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_GFF3) >| $@

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
	-cd ../final && \
	for file in $^; do \
	  ln -fs ../workspace/$${file}; \
	done

insf-c: genome.gff $(CHR_MAP)
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) $(COMMIT)

insf: genome.gff $(CHR_MAP)
	# Run ISF to insert features.
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) $(TEST)


# Undoing:
$(ALGFILE): $(LOG)
	$(MAKE_ALGIDS)

undo: $(ALGFILE)
	ga $(UNDO) --mapfile $(XML_MAP) --algInvocationId $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)


.PHONY: files all isf clean link undo
