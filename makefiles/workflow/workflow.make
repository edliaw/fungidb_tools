WORKFLOW := -h $(shell pwd -P)
FAILED = workflow $(WORKFLOW) -s1 FAILED 2>/dev/null
RUNNING = workflow $(WORKFLOW) -s1 RUNNING 2>/dev/null
LAST_FAILED = $$($(FAILED) | tail -n 1)
FIRST_FAILED = $$($(FAILED) | head -n 1)
LAST_RUNNING = $$($(RUNNING) | tail -n 1)
FIRST_RUNNING = $$($(RUNNING) | head -n 1)
TAIL = tail -n 50


summary:
	# Get the summary status.
	workflowSummary $(WORKFLOW)

test:
	# Test the controller
	workflow $(WORKFLOW) -t &

Reset:
	# Reset the controller.
	workflow $(WORKFLOW) -reset

start: 
	# Start the controller.
	workflow $(WORKFLOW) -r &

stop:
	# Stop the controller.
	workflowStopController $(WORKFLOW)


%-r:
	@${MAKE} -s $*-RUNNING

%-f:
	@${MAKE} -s $*-FAILED

show-%:
	@workflow $(WORKFLOW) -s1 $*

err-all-%:
	@${MAKE} -s show-$* | awk '{ print "steps/" $$0 "/step.err" }'

log-all-%:
	@${MAKE} -s show-$* | awk '{ print "steps/" $$0 "/step.log" }'

err:
	vim $$(for f in $$($(FAILED)); do echo "steps/$$f/step.err"; done)

%-a:
	@${MAKE} $*-$(FIRST_FAILED)

%-z:
	@${MAKE} $*-$(LAST_FAILED)

%-A:
	@${MAKE} $*-$(FIRST_RUNNING)

%-Z:
	@${MAKE} $*-$(LAST_RUNNING)

cundo-%:
	# List steps that will be undone.
	workflow $(WORKFLOW) -c -u $* &

undo-%:
	# Undo a step.
	workflow $(WORKFLOW) -r -u $*

tundo-%:
	# Test undo a step.
	workflow $(WORKFLOW) -t -u $* &

reundo-all:
	@${FAILED} | while read f; do \
	  ${MAKE} reundo-$$f; \
	done

reundo-%:
	# Set an undo step to ready.
	workflowstep $(WORKFLOW) -p $* ready -u

redo-all:
	@${FAILED} | while read f; do \
	  ${MAKE} redo-$$f; \
	done

redo-%:
	# Set a step to ready.
	workflowstep $(WORKFLOW) -p $* ready

Fail-%:
	# Fail a step if workflow is stopped and step need to update as FAILED.
	workflowForceStepState $(WORKFLOW) $* FAILED

kill-%:
	# End a step.
	workflowstep $(WORKFLOW) -p $* kill

offline-%:
	# Off-line a step.
	workflowstep $(WORKFLOW) -p $* offline

online-%:
	# On-line a step.
	workflowstep $(WORKFLOW) -p $* online

tail:
	tail -f logs/controller.log


.PHONY: summary start stop tail redo-all
