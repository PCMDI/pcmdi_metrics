PKG_NAME=pcmdi_metrics
USER=PCMDI
OS=linux-64

mkdir ~/conda-bld
conda config --set anaconda_upload no
export CONDA_BLD_PATH=~/conda-bld
export VERSION=`date +%Y.%m.%d`

git clone git://github.com/UV-CDAT/conda-recipes
cd conda-recipes

python ./prep_for_build.py -v $VERSION
conda build .
anaconda -t $CONDA_UPLOAD_TOKEN upload -u $USER -l nightly $CONDA_BLD_PATH/$OS/$PKG_NAME-$VERSION-0.tar.bz2 --force

python ./prep_for_build.py -v $VERSION -f nox
conda build .
anaconda -t $CONDA_UPLOAD_TOKEN upload -u $USER -l nightly $CONDA_BLD_PATH/$OS/$PKG_NAME-nox-$VERSION-py27_0.tar.bz2 --force
