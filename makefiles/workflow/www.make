BRANCH ?= trunk
DB     ?= fungbl3n
USER   ?= edliaw
SITE   = fungidb
URL    = $(USER).$(SITE).org
EMAIL  = $(USER)@$(SITE).org
WWW    = /var/www/$(URL)
TRUNK   = ~/GUS/trunk

GUS_BLD     ?= 
GUS_NOBLD   ?= CBIL WDK WSF FgpUtil install
APIDB_BLD   ?= ApiCommonShared ApiCommonData
APIDB_NOBLD ?= GBrowse ApiCommonWebService EuPathSiteCommon EuPathWebSvcCommon ApiCommonWebsite
WEB_BLDW    ?= ApiCommonWebsite

GUS        = $(GUS_BLD) $(GUS_NOBLD)
APIDB      = $(APIDB_BLD) $(APIDB_NOBLD)
BLD_DIRS   = $(GUS_BLD) $(APIDB_BLD)
NOBLD_DIRS = $(GUS_NOBLD) $(APIDB_NOBLD)
ALL_DIRS   = $(GUS) $(APIDB) $(WEB_BLDW)

SVN_CO  = svn co
SVN_URL = https://www.cbil.upenn.edu/svn
WEBAPP  = $(WWW)/etc/webapp.prop
GUSENV  = source ${PROJECT_HOME}/install/bin/gusEnv.bash

ifeq ($(BRANCH),trunk)
  BRANCH_DIR = $(BRANCH)
else
  BRANCH_DIR = branches/$(BRANCH)
endif


reload:
	# Reload the website cache.
	instance_manager manage FungiDB reload $(SITE).$(USER)

rebuild:
	# Update from svn and build everything.
	rebuilder $(URL)

reboot:
	# If the website stops functioning, this will do a hard reset on the service.
	sudo instance_manager stop FungiDB
	sudo instance_manager start FungiDB

link:
	# Activate this branch as the project home.
	ln -fs ${CURDIR}/.. -T $(WWW)/project_home

cattail:
	# View all events as they occur to the website -- useful for debugging.
	cattail -atc $(URL)

wdkXml:
	wdkXml -model FungiDB

wdkQuery-%:
	wdkQuery -model FungiDB -query $*

wdkCache:
	wdkCache -model FungiDB -new

all: $(GUS) $(APIDB)

tuning:
	cd $(TRUNK) && $(GUSENV) && cd ${PROJECT_HOME} && ${MAKE} tuning
	cd $(WWW) && $(GUSENV)

sql:
	sqlplus $(USER)@$(DB)

_clean_:
	rm -rf $(ALL_DIRS)

checkout:
	# Checkout GUS
	$(SVN_CO) $(SVN_URL)/gus/GusAppFramework/$(BRANCH_DIR) GUS
	# Checkout gus directories
	@for TARGET in $(GUS); do \
	  ${MAKE} $$(TARGET)-gus-checkout; \
	done
	# Checkout apidb directories
	for TARGET in $(APIDB); do \
	  ${MAKE} $$(TARGET)-apidb-checkout; \
	done

%-gus-checkout:
	$(SVN_CO) $(SVN_URL)/gus/$*/$(BRANCH_DIR) $*

%-apidb-checkout:
	$(SVN_CO) $(SVN_URL)/apidb/$*/$(BRANCH_DIR) $*

%-u:
	svn up $*

%-b:
	bld $*

%-bw:
	bldw $* $(WEBAPP)

$(ALL_DIRS)::
	@${MAKE} $@-u

$(WEB_BLDW)::
	@${MAKE} $@-bw

$(BLD_DIRS)::
	@${MAKE} $@-b


.PHONY: reload rebuild reboot link cattail all tuning sql _clean_ checkout $(ALL_DIRS)
