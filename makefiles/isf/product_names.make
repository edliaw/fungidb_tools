## Organism: 
ID            ?=
## Source/Data downloaded from:
SOURCE        ?=
VERSION       ?=
## Target file:
PROVIDER_FILE ?=
ZIP           ?=
FORMAT        ?=


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
ALGFILE       ?= algids
LOG           ?= isf.log


# Derived:
ifeq ($(ZIP), true)
  CAT := zcat
else
  CAT := cat
endif

SCRIPTS           = extract_products
SPLIT_ALGIDS      = split_algids --algfile $(ALGFILE)
UNDO_ALGIDS       = undo_algids $(ALGFILE)
MAKE_ALGIDS       = cat $(LOG) | $(SPLIT_ALGIDS) -a > /dev/null
# ISF:
COMMIT            = --commit | $(SPLIT_ALGIDS) >> $(LOG) 2>&1
TEST              = >| error.log 2>&1
INSERT_P          = ApiCommonData::Load::Plugin::InsertGeneFeatProductFromTabFile
INSERT_P_OPTS     = --productDbName $(DB_NAME) --productDbVer $(VERSION) --sqlVerbose --file $<
# Undo:
UNDO              = GUS::Community::Plugin::Undo
UNDO_STR          = $(shell $(UNDO_ALGIDS))
UNDO_ALGID        = $(firstword $(UNDO_STR))
UNDO_PLUGIN       = $(lastword $(UNDO_STR))

ifeq ($(FORMAT), gbf)
  EXTRACT_PRODUCTS = $(SCRIPTS)/extract_products_genbank.py
else ifeq ($(SOURCE), Broad)
  EXTRACT_PRODUCTS = $(SCRIPTS)/extract_products_broad.py
else ifeq ($(SOURCE), JGI)
  EXTRACT_PRODUCTS = $(SCRIPTS)/extract_products_jgi.py -i transcriptId -s kogdefline -p $(PREFIX_TERM)
endif


all: isf
	${MAKE} link

isf: insertp-c

files: products.txt

clean:
	rm products.txt

products.txt:
	$(CAT) "$(PROVIDER_FILE)" | $(EXTRACT_PRODUCTS) >| $@

link: products.txt
	# Link files to the final directory.
	mkdir -p ../final
	-cd ../final && \
	for file in $^; do \
	  ln -fs ../workspace/$${file}; \
	done

insertp-c: products.txt
	ga $(INSERT_P) $(INSERT_P_OPTS) $(COMMIT)

insertp: products.txt
	# Insert products into table.
	ga $(INSERT_P) $(INSERT_P_OPTS) $(TEST)


# Undoing:
$(ALGFILE): $(LOG)
	$(MAKE_ALGIDS)

undo:
	ga $(UNDO) --plugin $(UNDO_PLUGIN) --algInvocationId $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)


.PHONY: all isf files clean link undo
