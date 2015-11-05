#!/bin/sh
set -ex

# Expat
curl -O http://tcpdiag.dl.sourceforge.net/project/expat/expat/2.1.0/expat-2.1.0.tar.gz
tar -xzvf expat-2.1.0.tar.gz
chmod -R 755 expat-2.1.0
cd expat-2.1.0 && ./configure --prefix=/usr && make && sudo make install

# Python
curl -O https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz
tar -xzvf Python-2.7.10.tgz
cd Python-2.7.10 && ./configure --prefix=/usr && make && sudo make install

# Setuptools 1.4
curl -O http://uv-cdat.llnl.gov/cdat/resources/setuptools-1.4.tar.gz
tar -xzvf setuptools-1.4.tar.gz
cd setuptools-1.4 && ./configure --prefix=/usr && make && sudo make install

# Setuptools 18.5
curl -O http://uv-cdat.llnl.gov/cdat/resources/setuptools-18.5.tar.gz
tar -xzvf setuptools-18.5.tar.gz
cd setuptools-18.5 && ./configure --prefix=/usr && make && sudo make install

# Tips: http://docs.travis-ci.com/user/installing-dependencies/#Installing-Projects-from-Source
