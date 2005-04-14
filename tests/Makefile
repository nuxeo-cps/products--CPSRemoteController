# 
# This should work even when there is a symbolic link in the path.
# 
INSTANCE_HOME=$(shell python -c "import os.path; print os.path.normpath('$(PWD)/../../..')")
SOFTWARE_HOME=$(INSTANCE_HOME)/lib/python
PYTHON=$(INSTANCE_HOME)/bin/python
PYTHONPATH=$(INSTANCE_HOME)/lib/python2.1

.PHONY: test clean coverage

test:
	INSTANCE_HOME=$(INSTANCE_HOME) \
	SOFTWARE_HOME=$(SOFTWARE_HOME) \
	PYTHONPATH=$(PYTHONPATH) \
	$(PYTHON) runalltests.py

cover:
	mkdir cover

coverage: cover
	INSTANCE_HOME=$(INSTANCE_HOME) \
	SOFTWARE_HOME=$(SOFTWARE_HOME) \
	PYTHONPATH=$(PYTHONPATH) \
	$(PYTHON) coverage.py -x runalltests.py
	$(PYTHON) coverage.py -r ../*.py ../boxes/*.py
	$(PYTHON) coverage.py -a -d cover ../*.py ../boxes/*.py
	echo "Annotated files saved in cover/*.py,cover"

clean:
	rm -rf *.pyc *~ cover .coverage
