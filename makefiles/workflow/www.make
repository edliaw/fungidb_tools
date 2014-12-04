GUS_BLD     ?= TuningManager ReFlow
GUS_NOBLD   ?= CBIL GusSchema WDK WSF FgpUtil install
APIDB_BLD   ?= ApiCommonShared
APIDB_NOBLD ?= ApiCommonData GBrowse ApiCommonWebService EuPathSiteCommon EuPathWebSvcCommon ApiCommonWebsite
WEB_BLDW    ?= ApiCommonWebsite

SITE   = fungidb
URL    = $(USER).$(SITE).org
EMAIL  = $(USER)@$(SITE).org
WWW    = /var/www/$(URL)

WEBAPP = $(WWW)/etc/webapp.prop


rebuild:
	# Update from svn and build everything.
	rebuilder $(URL)

common: ApiCommonData ApiCommonShared ApiCommonWebsite

reload:
	# Reload the website cache.
	instance_manager manage FungiDB reload $(SITE).$(USER)

reboot:
	# If the website stops functioning, this will do a hard reset on the service.
	sudo instance_manager stop FungiDB
	sudo instance_manager start FungiDB

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

include /eupath/data/FungiDB/src/fungidb_tools/makefiles/workflow/gus.make

link:
	# Activate this branch as the project home.
	ln -fs $(shell basename $(shell readlink -f ${CURDIR})) -T ../project_home

.PHONY: reload rebuild reboot link cattail $(WEB_BLDW)
