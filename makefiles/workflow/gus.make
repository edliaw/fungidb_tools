BRANCH ?= trunk
DB     ?= fungbl1n
USER   ?= edliaw

GUS_BLD     ?= CBIL DJob GusSchema ReFlow WDK WSF FgpUtil
GUS_NOBLD   ?= WSFTemplate install
APIDB_BLD   ?= DoTS ApiCommonShared ApiCommonData ApiCommonWorkflow GGTools EuPathDatasets EuPathPresenters
APIDB_NOBLD ?= FungiDBDatasets FungiDBPresenters

GUS        = $(GUS_BLD) $(GUS_NOBLD)
APIDB      = $(APIDB_BLD) $(APIDB_NOBLD)
BLD_DIRS   = $(GUS_BLD) $(APIDB_BLD) GUS
NOBLD_DIRS = $(GUS_NOBLD) $(APIDB_NOBLD)
ALL_DIRS   = $(GUS) $(APIDB) GUS

SVN_CO  = svn co
SVN_URL = https://www.cbil.upenn.edu/svn

ifeq ($(BRANCH),trunk)
  BRANCH_DIR = $(BRANCH)
else
  BRANCH_DIR = branches/$(BRANCH)
endif


common: ApiCommonData ApiCommonWorkflow

all: $(GUS) $(APIDB)

link:
	# Activate this branch as the project home.
	ln -fs $(shell basename $(shell readlink -f ${CURDIR}/..)) -T ~/GUS/current

tuning:
	tuningManager --instance $(DB) --propfile ${GUS_HOME}/config/tuningManagerProp.xml --doUpdate &

sql:
	sqlplus $(USER)@$(DB)

_clean_:
	rm -rf $(ALL_DIRS)

checkout:
	# Checkout GUS
	$(SVN_CO) $(SVN_URL)/gus/GusAppFramework/$(BRANCH_DIR) GUS
	# Checkout gus directories
	@for TARGET in $(GUS); do \
	  ${MAKE} $${TARGET}-gus-checkout; \
	done
	# Checkout apidb directories
	@for TARGET in $(APIDB); do \
	  ${MAKE} $${TARGET}-apidb-checkout; \
	done

%-gus-checkout:
	$(SVN_CO) $(SVN_URL)/gus/$*/$(BRANCH_DIR) $*

%-apidb-checkout:
	$(SVN_CO) $(SVN_URL)/apidb/$*/$(BRANCH_DIR) $*

%-u:
	svn up $*

GUS-b:
	touch ./GusSchema/Definition/config/gus_schema.xml
	bld GUS

%-b:
	bld $*

$(ALL_DIRS)::
	@${MAKE} $@-u

$(BLD_DIRS)::
	@${MAKE} $@-b


.PHONY: common all link tuning sql _clean_ checkout $(ALL_DIRS)
