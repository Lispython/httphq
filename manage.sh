#!/bin/sh


build_certs(){
    openssl genrsa -des3 -out server.key 1024
    openssl rsa -in server.key -out server.key.insecure && mv server.key server.key.secure && mv server.key.insecure server.key
    openssl req -new -key server.key -out server.csr
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
    wget http://www.startssl.com/certs/sub.class1.server.ca.pem
    cat server.crt sub.class1.server.ca.pem > ./server.pem

}

case $1 in

    "build_certs") build_certs;;
esac