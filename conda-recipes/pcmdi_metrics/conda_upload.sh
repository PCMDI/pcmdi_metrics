#!/usr/bin/env bash

PKG_NAME=pcmdi_metrics
USER=PCMDI
echo "Trying to upload conda"
if [ `uname` == "Linux" ]; then
    OS=linux-64
    echo "Linux OS"
    export PATH="$HOME/miniconda2/bin:$PATH"
    conda update -y -q conda
else
    echo "Mac OS"
    OS=osx-64
fi

mkdir ~/conda-bld
conda config --set anaconda_upload no
export CONDA_BLD_PATH=${HOME}/conda-bld
export VERSION=`date +%Y.%m.%d`
echo "Cloning recipes"
git clone git://github.com/UV-CDAT/conda-recipes
cd conda-recipes
# uvcdat creates issues for build -c uvcdat confises package and channel
rm -rf uvcdat
pwd
ln -s ../../conda-recipes/pcmdi_metrics pcmdi_metrics
echo "Starting prep for build"
python ./prep_for_build.py
echo "starting conda build"
conda build pcmdi_metrics -c conda-forge -c uvcdat
echo "starting anaconda upload"
anaconda -t $CONDA_UPLOAD_TOKEN upload -u $USER -l nightly $CONDA_BLD_PATH/$OS/$PKG_NAME-$VERSION-py27_0.tar.bz2 --force

