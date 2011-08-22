#!/bin/bash
source ./venv/bin/activate
manage(){
	./venv/bin/python manage.py $@
}

minor_update(){
	git push origin master;
	fab-2.6 production minor_update;
}
restart()
{
    ./venv/bin/python manage.py stop
}

deploy(){
	git push origin master;
	fab-2.6 production deploy;
}

start(){
    ./venv/bin/python manage.py --logging=none start
}

stop(){
    ./venv/bin/python manage.py stop
}

case $1 in
    "minor_update") minor_update;;

    "deploy") deploy;;

	"restart") restart;;

    "start") start;;

	"stop") stop;;

    *) ./venv/bin/python manage.py $@;;

esac