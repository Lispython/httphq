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

mongo-start:
	rm -rf /var/lib/mongodb/mongod.lock
	sudo mongod --fork -f /etc/mongodb.conf --auth --logpath /var/log/mongodb/mongodb.log --logappend


redis-start:
	sudo redis-server /etc/redis/redis.conf