#!/bin/sh

. ./venv/bin/activate

manage(){
	./venv/bin/python manage.py $@
}

minor_update(){
	git push origin master;
	fab-2.6 production minor_update;
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

restart()
{
    ./venv/bin/python manage.py stop
    ./venv/bin/python manage.py start
}

tests()
{
    ./venv/bin/python tests.py
}

debug(){
    . ./venv/bin/activate
    python debug.py
}

build_certs(){
    openssl genrsa -des3 -out server.key 1024
    openssl rsa -in server.key -out server.key.insecure && mv server.key server.key.secure && mv server.key.insecure server.key
    openssl req -new -key server.key -out server.csr
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

}

case $1 in
    "minor_update") minor_update;;

    "deploy") deploy;;

	"restart") restart;;

    "start") start;;

	"stop") stop;;

	"debug") debug;;

	"tests") tests;;

	"build_certs") build_certs;;

    *) ./venv/bin/python manage.py $@;;

esac