WORKFLOW = -h $(shell pwd -P)
FAILED = workflow $(WORKFLOW) -s1 FAILED 2>/dev/null
LAST_FAILED = `$(FAILED) | tail -n 1`
TAIL = tail -n 50


summary:
	# Get the summary status.
	workflowSummary $(WORKFLOW)

test:
	# Test the controller
	workflow $(WORKFLOW) -t &

start: 
	# Start the controller.
	workflow $(WORKFLOW) -r &

reset:
	# Reset the controller.
	workflow $(WORKFLOW) -reset

stop:
	# Stop the controller.
	workflowStopController $(WORKFLOW)

show_%:
	# Display jobs by category.
	workflow $(WORKFLOW) -s1 $*

undo_%:
	# Undo a step.
	workflow $(WORKFLOW) -r -u $* &

tundo_%:
	# Undo a step.
	workflow $(WORKFLOW) -t -u $* &

reundo_%:
	# Set an undo step to ready.
	workflowstep $(WORKFLOW) -p $* ready -u

redo_all:
	@for f in $$(${FAILED}); do \
	  ${MAKE} redo_$$f; \
	done

redo_last:
	${MAKE} redo_$(LAST_FAILED)

redo_%:
	# Set a step to ready.
	workflowstep $(WORKFLOW) -p $* ready

offline_%:
	# Off-line a step.
	workflowstep $(WORKFLOW) -p $* offline

online_%:
	# On-line a step.
	workflowstep $(WORKFLOW) -p $* online

tail:
	tail -f logs/controller.log

err_last:
	$(TAIL) steps/$(LAST_FAILED)/step.err

err_%:
	@workflow $(WORKFLOW) -s1 $* 2>/dev/null | awk '{ print "steps/" $$0 "/step.err" }'

log_%:
	@workflow $(WORKFLOW) -s1 $* 2>/dev/null | awk '{ print "steps/" $$0 "/step.err\nsteps/" $$0 "/step.log" }'


.PHONY: summary start stop tail redo_all redo_last err_last
