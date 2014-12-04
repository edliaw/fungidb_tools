BRANCH  ?= trunk
FBRANCH ?= $(BRANCH)
DB      ?= fungbl1n
USER    ?= edliaw
BUILD    = fung-build-7

GUS_BLD     ?= GusSchema DJob FgpUtil WSF WDK CBIL ReFlow TuningManager
GUS_NOBLD   ?= WSFTemplate install
APIDB_BLD   ?= DoTS GGTools EuPathSiteCommon EuPathWebSvcCommon GBrowse ApiCommonData ApiCommonWorkflow ApiCommonShared ApiCommonWebsite ApiCommonWebService
APIDB_NOBLD ?= EuPathPresenters EuPathDatasets
FUNGI_BLD   ?= FungiDBPresenters FungiDBDatasets
FUNGI_NOBLD ?= 

GUS        = $(GUS_BLD) $(GUS_NOBLD)
APIDB      = $(APIDB_BLD) $(APIDB_NOBLD)
FUNGI      = $(FUNGI_BLD) $(FUNGI_NOBLD)
BLD_DIRS   = GUS $(GUS_BLD) $(APIDB_BLD) $(FUNGI_BLD)
NOBLD_DIRS = $(GUS_NOBLD) $(APIDB_NOBLD) $(FUNGI_NOBLD)
ALL_DIRS   = GUS $(GUS) $(APIDB) $(FUNGI)

SVN_CO  = svn co
SVN_URL = https://www.cbil.upenn.edu/svn
TUNING_PROP = ${GUS_HOME}/config/tuningManagerProp.xml
TUNING_CONFIG = ${PROJECT_HOME}/ApiCommonShared/Model/lib/xml/tuningManager/tuningManager.xml

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


common: ApiCommonData ApiCommonShared ApiCommonWorkflow

all: $(ALL_DIRS)

link:
	# Activate this branch as the project home.
	ln -fs $(shell basename $(shell readlink -f ${CURDIR}/..)) -T ../current

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

checkout: checkout-GUS-GUS checkout-GUS checkout-APIDB checkout-FUNGI

checkout-GUS-GUS:
	$(SVN_CO) $(SVN_URL)/gus/GusAppFramework/$(BRANCH_DIR) GUS

checkout-GUS-%:
	$(SVN_CO) $(SVN_URL)/gus/$*/$(BRANCH_DIR) $*

checkout-APIDB-%:
	$(SVN_CO) $(SVN_URL)/apidb/$*/$(BRANCH_DIR) $*

checkout-FUNGI-%:
	$(SVN_CO) $(SVN_URL)/apidb/$*/$(FBRANCH_DIR) $*

checkout-%:
	for TARGET in $($*); do \
	  ${MAKE} checkout-$*-$${TARGET}; \
	done

u-%:
	svn up $*

b-GUS:
	touch ./GusSchema/Definition/config/gus_schema.xml
	bld GUS

b-%:
	bld $*

$(ALL_DIRS)::
	@${MAKE} u-$@

$(BLD_DIRS)::
	@${MAKE} b-$@

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

props:
	propertiesFromDatasets FungiDBDatasets

inject:
	presenterInjectTemplates -presentersDir ${PROJECT_HOME}/FungiDBPresenters/Model/lib/xml/datasetPresenters -templatesDir ${PROJECT_HOME}/ApiCommonShared/Model/lib/dst -contactsXmlFile ${PROJECT_HOME}/FungiDBPresenters/Model/lib/xml/datasetPresenters/contacts/contacts.xml

.PHONY: common all link tuning add_tuning sql _clean_ checkout $(ALL_DIRS) _dropschema_ _initschema_
