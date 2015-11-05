#!/bin/sh
set -ex
curl -O https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz
tar -xzvf Python-2.7.10.tgz
cd Python-2.7.10 && ./configure --prefix=/usr && make && sudo make install

# Tips: http://docs.travis-ci.com/user/installing-dependencies/#Installing-Projects-from-Source
