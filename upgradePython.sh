#!/bin/sh
set -ex

# Python
#curl -O https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz
#tar -xzvf Python-2.7.10.tgz
#cd Python-2.7.10 && ./configure --prefix=/usr && make && sudo make install

# Expat
curl -O http://downloads.sourceforge.net/project/expat/expat/2.1.0/expat-2.1.0.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fexpat%2Ffiles%2Fexpat%2F2.1.0%2F&ts=1446690795&use_mirror=iweb
tar -xzvf expat-2.1.0.tar.gz
cd expat-2.1.0 && ./configure --prefix=/usr && make && sudo make install

# Tips: http://docs.travis-ci.com/user/installing-dependencies/#Installing-Projects-from-Source
