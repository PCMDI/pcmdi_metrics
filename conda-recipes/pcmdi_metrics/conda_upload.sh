PKG_NAME=pcmdi_metrics
USER=PCMDI
OS=linux-64

mkdir ~/conda-bld
conda config --set anaconda_upload no
export CONDA_BLD_PATH=~/conda-bld
export VERSION=`date +%Y.%m.%d`
conda build .
anaconda -t $CONDA_UPLOAD_TOKEN upload -u $USER -l nightly $CONDA_BLD_PATH/$OS/$PKG_NAME-`date +%Y.%m.%d`-0.tar.bz2 --force
<<<<<<< HEAD

=======
>>>>>>> 011f004843960dc9ebd6ed8ea528c5a920cab8ae
