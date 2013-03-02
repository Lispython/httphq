all: clean-pyc test

test:
	python setup.py nosetests --stop --tests tests.py

travis:
	python setup.py nosetests --tests tests.py

release:
	python setup.py sdist upload
	python setup.py bdist_wininst upload

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

compress-static:
	@echo "Compress static"
	venv/bin/python ./manage.py compress_static

remove-min:
	@echo "Remove min static files"
	-rm -rf static/css/*.min.css
	-rm -rf static/js/*.min.js

find-print:
	grep -r --include=*.py --exclude-dir=venv --exclude=fabfile* --exclude=tests.py --exclude-dir=tests --exclude-dir=commands 'print' ./
