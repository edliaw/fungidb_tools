# Organism: 
ID            ?=
# Source/Data downloaded from:
SOURCE        ?=
VERSION       ?=
# Target file:
PROVIDER_FILE ?=
ZIP           ?=
FORMAT        ?=


# Constants:
ifeq ($(ZIP), true)
CAT := zcat
else
CAT := cat
endif

ifeq ($(FORMAT), gbf)
EXTRACT_PRODUCTS = $(SCRIPTS)/extract_products_genbank.py
else ifeq ($(SOURCE), Broad)
EXTRACT_PRODUCTS = $(SCRIPTS)/extract_products_broad.py
else ifeq ($(SOURCE), JGI)
EXTRACT_PRODUCTS = $(SCRIPTS)/extract_products_jgi.py
EXTRACT_PRODUCTS_OPTS = -i transcriptId -s kogdefline -p $(PREFIX_TERM)
endif

DB_NAME           ?= $(ID)_genome_RSRC
LOG               ?= isf.log
SCRIPT_ROOT       = /home/edliaw/repo/fungidb-tools/isf
SCRIPTS           = $(SCRIPT_ROOT)/extract_products
GREP_ALGIDS       = $(SCRIPT_ROOT)/format_features/grep_algids.py
GREP_ALGIDS_OPTS  ?= $(LOG)
# ga
INSERT_P          = ApiCommonData::Load::Plugin::InsertGeneFeatProductFromTabFile
INSERT_P_OPTS     = --productDbName $(DB_NAME) --productDbVer $(VERSION) --sqlVerbose
UNDO              = GUS::Community::Plugin::Undo


# Recipes:
.PHONY : all isf files clean link algid insertp insertp-c insertp-u% insertp-u%-c

all : isf
	${MAKE} link

isf : insertp-c

files : products.txt

clean :
	rm products.txt

products.txt :
	$(CAT) "$(PROVIDER_FILE)" | $(EXTRACT_PRODUCTS) $(EXTRACT_PRODUCTS_OPTS) >| $@

link : products.txt
	# Link files to the final directory.
	mkdir -p ../final
	cd ../final && \
	for file in $^; do \
	  ln -s ../workspace/$$file; \
	done

insertp-c : products.txt
	ga $(INSERT_P) $(INSERT_P_OPTS) --file $< >> $(LOG) 2>&1

insertp : products.txt
	# Insert products into table.
	ga $(INSERT_P) $(INSERT_P_OPTS) --file $< >| error.log 2>&1


# Undoing:
algid :
	$(GREP_ALGIDS) $(GREP_ALGIDS_OPTS)

insertp-u%-c :
	ga $(UNDO) --plugin $(INSERT_P) --algInvocationId $* --commit

insertp-u% :
	ga $(UNDO) --plugin $(INSERT_P) --algInvocationId $*
