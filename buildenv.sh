#!/bin/sh

#sudo apt-get install binutils gdal-bin postgresql-8.4-postgis libgeoip1 gdal-bin libgdal-dev swig

CURRENT_PATH=$(pwd)

py(){

    curl https://raw.github.com/pypa/virtualenv/master/virtualenv.py > ./virtualenv.py

    if [ ! -d "./venv/" ]; then
	echo "Virtualenv not exists, creating..."
	python ./virtualenv.py --python=python2.7 --clear venv
    else
	echo "Virtualenv exists"
    fi
    . ./venv/bin/activate
    ./venv/bin/easy_install pip
    ./venv/bin/pip install -U -r ./req.txt
    python ./virtualenv.py --relocatable venv
}



case $1 in
	*) py;;
esac