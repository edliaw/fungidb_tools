BRANCH  ?= trunk
FBRANCH ?= $(TRUNK)
DB      ?= fungbl1n
USER    ?= edliaw
BUILD    = fung-build-6

GUS_BLD     ?= TuningManager CBIL DJob GusSchema ReFlow WDK WSF FgpUtil
GUS_NOBLD   ?= WSFTemplate install
APIDB_BLD   ?= DoTS ApiCommonShared ApiCommonData ApiCommonWorkflow ApiCommonWebsite EuPathSiteCommon GGTools EuPathDatasets
APIDB_NOBLD ?= EuPathPresenters
FUNGI_BLD   ?= FungiDBDatasets FungiDBPresenters
FUNGI_NOBLD ?= 

GUS        = $(GUS_BLD) $(GUS_NOBLD)
APIDB      = $(APIDB_BLD) $(APIDB_NOBLD)
FUNGI      = $(FUNGI_BLD) $(FUNGI_NOBLD)
BLD_DIRS   = $(GUS_BLD) $(APIDB_BLD) $(FUNGI_BLD) GUS
NOBLD_DIRS = $(GUS_NOBLD) $(APIDB_NOBLD) $(FUNGI_NOBLD)
ALL_DIRS   = $(GUS) $(APIDB) $(FUNGI) GUS

SVN_CO  = svn co
SVN_URL = https://www.cbil.upenn.edu/svn

ifeq ($(BRANCH),trunk)
  BRANCH_DIR = $(BRANCH)
else
  BRANCH_DIR = branches/$(BRANCH)
endif

ifeq ($(FBRANCH),trunk)
  FBRANCH_DIR = $(FBRANCH)
else
  FBRANCH_DIR = branches/$(FBRANCH)
endif

TUNING_PROP = ${GUS_HOME}/config/tuningManagerProp.xml
TUNING_CONFIG = ${PROJECT_HOME}/ApiCommonShared/Model/lib/xml/tuningManager/tuningManager.xml


common: ApiCommonData ApiCommonShared ApiCommonWorkflow

all: $(GUS) $(APIDB) $(FUNGI)

link:
	# Activate this branch as the project home.
	ln -fs $(shell basename $(shell readlink -f ${CURDIR}/..)) -T ~/GUS/current

tuning:
	tuningManager --instance $(DB) --propfile $(TUNING_PROP) --configFile $(TUNING_CONFIG) --doUpdate &

tuning-%:
	tuningManager --instance $(DB) --propfile $(TUNING_PROP) --configFile $(TUNING_CONFIG) --doUpdate --tables $* &

add-tuning:
	# Run once for new database instance.
	tuningMgrMgr addinstance -connectName=$(DB) -instanceNickname=$(DB) -propfile $(TUNING_PROP) -family=$(BUILD) -svn=$(BRANCH_DIR)

sql:
	sqlplus $(USER)@$(DB)

_clean_:
	# Remove SVN directories.
	-rm -rf $(ALL_DIRS)

checkout:
	# Checkout GUS.
	$(SVN_CO) $(SVN_URL)/gus/GusAppFramework/$(BRANCH_DIR) GUS
	# Checkout gus directories.
	for TARGET in $(GUS); do \
	  ${MAKE} $${TARGET}-gus-checkout; \
	done
	# Checkout apidb directories.
	for TARGET in $(APIDB); do \
	  ${MAKE} $${TARGET}-apidb-checkout; \
	done
	for TARGET in $(FUNGI); do \
	  ${MAKE} $${TARGET}-fungi-checkout; \
	done

%-gus-checkout:
	$(SVN_CO) $(SVN_URL)/gus/$*/$(BRANCH_DIR) $*

%-apidb-checkout:
	$(SVN_CO) $(SVN_URL)/apidb/$*/$(BRANCH_DIR) $*

%-fungi-checkout:
	$(SVN_CO) $(SVN_URL)/apidb/$*/$(FBRANCH_DIR) $*

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

_dropschema_:
	# Wipe out database!
	installApidbSchema --db $(DB) --dropApiDB --allowFailures
	installApidbSchema --db $(DB) --dropGUS

_initschema_:
	# Initialize new database schema.
	build GUS install -append -installDBSchemaSkipRoles
	installApidbSchema --db $(DB) --create
	rm GUS/Model/lib/perl/generated
	${MAKE} GUS ApiCommonData


.PHONY: common all link tuning add_tuning sql _clean_ checkout $(ALL_DIRS) _dropschema_ _initschema_
