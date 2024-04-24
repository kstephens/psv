PYTHON=python3.11
PYTHONPATH_OTHER:=vendor/devdriven-python/lib
DIRS_OTHER:=vendor/devdriven-python
TEST_DIRS+=tests
export PSV_CONFIG_FILE=/dev/null
include vendor/devdriven-python/Makefile.common

README.md: doc/README-*.md
	cat doc/README-*.md | $(PYTHON) lib/psv/test_helper.py > README.md

doc/README-10-help.md: lib/psv/* Makefile
	bin/psv help --markdown --verbose | $(PYTHON) lib/psv/test_helper.py > tmp/README-10-help.md
	mv tmp/README-10-help.md $@
