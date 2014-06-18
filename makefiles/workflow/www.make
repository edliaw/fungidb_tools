GUS_BLD     ?= TuningManager ReFlow
GUS_NOBLD   ?= CBIL GusSchema WDK WSF FgpUtil install
APIDB_BLD   ?= ApiCommonShared
APIDB_NOBLD ?= ApiCommonData GBrowse ApiCommonWebService EuPathSiteCommon EuPathWebSvcCommon ApiCommonWebsite
WEB_BLDW    ?= ApiCommonWebsite

include /eupath/data/FungiDB/src/fungidb_tools/makefiles/workflow/gus.make

SITE   = fungidb
URL    = $(USER).$(SITE).org
EMAIL  = $(USER)@$(SITE).org
WWW    = /var/www/$(URL)

WEBAPP = $(WWW)/etc/webapp.prop


common: ApicommonData ApiCommonShared ApiCommonWebsite

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
	ln -fs $(shell basename ${CURDIR}) -T $(WWW)/project_home

cattail:
	# View all events as they occur to the website -- useful for debugging.
	cattail -atc $(URL)

wdkXml:
	wdkXml -model FungiDB

wdkQuery-%:
	wdkQuery -model FungiDB -query $*

wdkCache:
	wdkCache -model FungiDB -new

bw-%:
	bldw $* $(WEBAPP)

$(WEB_BLDW)::
	@${MAKE} bw-$@

.PHONY: reload rebuild reboot link cattail $(WEB_BLDW)
