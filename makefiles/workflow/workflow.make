WORKFLOW = -h $(shell pwd -P)


summary:
	# Get the summary status.
	workflowSummary $(WORKFLOW)

start: 
	# Start the controller.
	workflow $(WORKFLOW) -r &

stop:
	# Stop the controller.
	workflowStopController $(WORKFLOW)

show_%:
	# Display jobs by category.
	workflow $(WORKFLOW) -s1 $*

undo_%:
	# Undo a step.
	workflow $(WORKFLOW) -r -u $* &

reundo_%:
	# Set an undo step to ready.
	workflowstep $(WORKFLOW) -p $* ready -u

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

lerr:
	tail -n 50 steps/`workflow $(WORKFLOW) -s1 FAILED | tail -n 1`/step.err

err_%:
	tail -n 50 steps/$*/step.err


.PHONY: summary start stop tail lerr
