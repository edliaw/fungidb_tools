## Organism:
TAXID         ?= 
## Target file:
PROVIDER_FILE ?= ../fromProvider/*.gtf
ZIP           ?= 
MAP_FILE      ?= ../../../*_$(SOURCE)_fasta/$(VERSION)/final/chromosomeMap.txt
## Formatting:
TYPE          ?= 
FORMAT_RE     ?= "_$(VERSION)\.(?:(?P<number>\d+)|(?P<roman>[XIV]+)|(?P<letter>[A-Z]))"
FORMAT_PAD    ?= 2
PREFIX_TERM   ?= 


# Functions:
end_word       = $(word $(shell echo $(words $(2))-$(1)+1 | bc),$(2))
PWDLIST       := $(subst /, ,$(PWD))

ID             = $(call end_word,5,$(PWDLIST))
VERSION        = $(call end_word,2,$(PWDLIST))
SOURCE         = $(call end_word,2,$(subst _, ,$(call end_word,3,$(PWDLIST))))
LONG_TYPE      = $(call end_word,3,$(subst _, ,$(call end_word,3,$(PWDLIST))))


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
XML_MAP       ?= ${PROJECT_HOME}/ApiCommonData/Load/lib/xml/isf/FungiDB/genericGFF2Gus.xml
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

FORMAT_GTF        = format_gff --filetype gtf --species $(ID) --provider $(SOURCE) --padding $(FORMAT_PAD) --soterm $(TYPE) --regex $(FORMAT_RE) --comments
ifeq ($(SOURCE), JGI)
  FORMAT_GTF     += --nostart
  CONVERT_GTF     = convertGTFToGFF3_JGI -prefix $(PREFIX_TERM)
else
  CONVERT_GTF     = convertGTFToGFF3_Broad
endif
SPLIT_ALGIDS      = split_algids
UNDO_ALGIDS       = undo_algids $(ALGFILE) 2> /dev/null
MAKE_ALGIDS       = $(SPLIT_ALGIDS) --all < $(LOG) >> $(ALGFILE)
# ISF:
COMMIT            = --commit 2>&1 | tee -a $(LOG) | $(SPLIT_ALGIDS) >> $(ALGFILE)
TEST              = >| error.log 2>&1
INSERT_FEAT       = GUS::Supported::Plugin::InsertSequenceFeatures
INSERT_FEAT_OPTS ?= --extDbName $(DB_NAME) --extDbRlsVer $(VERSION) --mapFile $(XML_MAP) --inputFileExtension gff --fileFormat gff3 --soCvsVersion 1.417 --organism $(TAXID) --seqSoTerm $(LONG_TYPE) --seqIdColumn source_id --naSequenceSubclass ExternalNASequence $(CHR_MAP_OPT) --inputFileOrDir $< --validationLog val.log --bioperlTreeOutput bioperlTree.out
# Undo:
UNDO              = GUS::Supported::Plugin::InsertSequenceFeaturesUndo
UNDO_STR          = $(shell $(UNDO_ALGIDS))
UNDO_ALGID        = $(firstword $(UNDO_STR))
UNDO_PLUGIN       = $(lastword $(UNDO_STR))


files: report.txt $(CHR_MAP)

all: isf
	${MAKE} link

isf: insf-c

clean:
	-rm genome.* report.txt $(CHR_MAP)

genome.gtf:
	# Copy provider file and reformat names
	$(CAT) $(PROVIDER_FILE) | $(FORMAT_GTF) >| $@

genome.gff3: genome.gtf
        # Convert GTF to GFF3 format.
	# JGI GTF transcript ids need to be prefixed when converting.
	$(CONVERT_GTF) $< >| $@

genome.gff: genome.gff3
	# Convert GFF3 to pseudo GFF3 format (compatible with ISF).
	preprocessGFF3 --input_gff $< --output_gff $@

chromosomeMap.txt:
	# Copy the chromosome map file from the fasta directory.
	cp $(MAP_FILE) $@

report.txt: genome.gff
	# View feature qualifiers for genome.gff.
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

insf: genome.gff $(CHR_MAP)algid 
	# Run ISF to insert features.
	ga $(INSERT_FEAT) $(INSERT_FEAT_OPTS) $(TEST)


# Undoing:
$(ALGFILE): $(LOG)
	$(MAKE_ALGIDS)

undo: $(ALGFILE)
ifeq ($(UNDO_ALGID),)
	@echo "Nothing to undo."
else
	ga $(UNDO) --mapfile $(XML_MAP) --algInvocationId $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)
endif


.PHONY: files all isf clean link undo
