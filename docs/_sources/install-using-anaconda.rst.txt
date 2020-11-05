.. _install-anaconda:

**********************
Install using Anaconda
**********************

We offer an installation for anaconda users under linux-64 or osx-64.
Support for Windows is not available yet.

https://anaconda.org/PCMDI/pcmdi_metrics/files

All Platforms System Requirements
=================================
  * Install the `Anaconda for Python 3.7 <https://www.anaconda.com/products/individual#Downloads>`_ package (we recommend installing this for each user)
  * Make sure anaconda is in your PATH (assuming anaconda is installed in ${HOME}/anaconda
      * ``export PATH=${HOME}/anaconda/bin:${PATH}`` # for [ba]sh
      * ``setenv PATH ${HOME}/anaconda/bin:${PATH}`` # for [t]csh

Make sure you have no environment variables set from an old UV-CDAT installation in your PATH/PYTHONPATH,LD_LIBRARY_PATH etc

Bypassing firewalls
===================
If your institution has tight ssl certificate/security issues try:
  * ``conda config --set ssl_verify False``
  * ``binstar config --set ssl_verify False``

Installing the PCMDI Metrics Package (PMP)
==========================================
Using the conda package manager, you can install the PCMDI Metrics package from the PCMDI conda channel, and from an environment containing [CDAT](https://cdat.llnl.gov/).
  * ``source activate [YOUR_CDAT_ENABLED_CONDA_ENVIRONMENT]`` (See `CDAT Install <https://github.com/CDAT/cdat/wiki/install>`_)
  * ``conda install pcmdi_metrics -c cdat-forge``

Getting the latest nightly of PMP and CDAT
==========================================
  * ``conda create -n [YOUR_ENV_NAME_HERE] -c cdat/label/nightly -c pcmdi/label/nightly -c conda-forge -c cdat pcmdi_metrics``
  * ``source activate [YOUR_ENV_NAME_HERE]``


To learn more about conda environments see: http://conda.pydata.org/docs/using/envs.html