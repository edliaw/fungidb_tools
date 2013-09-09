## Organism: 
## Target file:
PROVIDER_FILE ?=
ZIP           ?=
FORMAT        ?=


# Functions:
end_word       = $(word $(shell echo $(words $(2))-$(1)+1 | bc),$(2))
PWDLIST       := $(subst /, ,$(PWD))

ID             = $(call end_word,5,$(PWDLIST))
VERSION        = $(call end_word,2,$(PWDLIST))
SOURCE         = $(call end_word,2,$(subst _, ,$(call end_word,3,$(PWDLIST))))


# Constants:
DB_NAME       ?= $(ID)_genome_RSRC
ALGFILE       ?= algids
LOG           ?= isf.log


# Derived:
ifdef ZIP
  CAT := zcat
else
  CAT := cat
endif

SCRIPTS           = extract_products
SPLIT_ALGIDS      = split_algids
UNDO_ALGIDS       = undo_algids $(ALGFILE) 2> /dev/null
MAKE_ALGIDS       = $(SPLIT_ALGIDS) --all < $(LOG) >> $(ALGFILE)
# ISF:
COMMIT            = --commit 2>&1 | tee -a $(LOG) | $(SPLIT_ALGIDS) >> $(ALGFILE)
TEST              = >| error.log 2>&1
INSERT_P          = ApiCommonData::Load::Plugin::InsertGeneFeatProductFromTabFile
INSERT_P_OPTS     = --productDbName $(DB_NAME) --productDbVer $(VERSION) --file $<
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

undo: $(ALGFILE)
ifeq ($(UNDO_ALGID),)
	@echo "Nothing to undo."
else
	ga $(UNDO) --plugin $(UNDO_PLUGIN) --algInvocationId $(UNDO_ALGID) --commit
	$(UNDO_ALGIDS) --mark $(UNDO_ALGID)
endif


.PHONY: all isf files clean link undo
