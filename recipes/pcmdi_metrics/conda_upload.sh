#!/usr/bin/env bash

PKG_NAME=pcmdi_metrics
USER=PCMDI
echo "Trying to upload conda in "`pwd`
if [ `uname` == "Linux" ]; then
    OS=linux-64
    echo "Linux OS"
    export PATH="$HOME/miniconda2/bin:$PATH"
    conda update -y -q conda
else
    echo "Mac OS"
    OS=osx-64
fi

mkdir conda-bld
cd conda-bld
echo "WE are in :"`pwd`
conda config --set anaconda_upload no
export CONDA_BLD_PATH=`pwd`/build_conda
mkdir build_conda
echo "BUILDING IN:",$CONDA_BLD_PATH
export VERSION=`date +%Y.%m.%d`
echo "Cloning recipes"
git clone git://github.com/UV-CDAT/conda-recipes
cd conda-recipes
rm -rf cdp
# uvcdat creates issues for build -c uvcdat confises package and channel
#ln -s ../../recipes/pcmdi_metrics .
echo "cp -r ../../recipes/pcmdi_metrics ."
cp -r ../../recipes/pcmdi_metrics .
echo "Starting prep for build"
python ./prep_for_build.py
echo "starting conda build"
conda build pcmdi_metrics -c conda-forge -c uvcdat
echo "starting anaconda upload"
anaconda -t $CONDA_UPLOAD_TOKEN upload -u $USER -l nightly $CONDA_BLD_PATH/$OS/$PKG_NAME-*$VERSION*-0.tar.bz2 --force

