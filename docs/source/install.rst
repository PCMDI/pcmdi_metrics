.. _install:

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
Using the conda package manager, you can install the PCMDI Metrics package from the PCMDI conda-forge channel.

Create a new virtual environment and install PMP
  * ``conda create -n [YOUR_CONDA_ENVIRONMENT] -c conda-forge pcmdi_metrics``

or

  * ``conda create -n [YOUR_CONDA_ENVIRONMENT]``
  * ``conda activate [YOUR_CONDA_ENVIRONMENT]``
  * ``conda install -c conda-forge pcmdi_metrics``

alternatively,

Install PMP in the current (or existing) virtual environment
  * ``conda install -c conda-forge pcmdi_metrics``


To learn more about conda environments see: http://conda.pydata.org/docs/using/envs.html
