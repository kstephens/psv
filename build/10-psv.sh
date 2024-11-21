bin-dir bin
lib-dir lib vendor/devdriven-python/lib
lint-dir bin lib
test-dir tests
requirements-dir . vendor/devdriven
requirements-file requirements.txt dev-requirements.txt
os_dependencies+='w3m sqlite3 '
export PSV_CONFIG_FILE=/dev/null

all_other+='README'
-README() {
	- README-help
	cat doc/README-*.md | x ${PYTHON} lib/psv/test_helper.py > README.md
}
-README-help() {
	bin/psv help --markdown --verbose | ${PYTHON} lib/psv/test_helper.py > tmp/README-10-help.md
	mv {tmp,doc}/README-10-help.md
}
