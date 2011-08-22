#!/bin/sh
virtualenv --python=python2.6 --clear venv
./venv/bin/easy_install pip
./venv/bin/pip install -E venv -r ./req.txt