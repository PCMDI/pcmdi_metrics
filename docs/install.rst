.. _install:

**********************
Installation
**********************

We offer an installation for `Anaconda`_ users under linux-64 or osx-64. 
Support for Windows is not available yet.

https://anaconda.org/conda-forge/pcmdi_metrics

All Platforms System Requirements
=================================
  * Install the `Anaconda`_ package (we recommend installing this for each user)
  * Alternatives include `Miniconda`_ or `Miniforge/Mambaforge`_
  * If using Anaconda or Miniconda, we recommend also installing `mamba`_ for better performance

  * Make sure anaconda is in your PATH (assuming anaconda is installed in ${HOME}/anaconda
      * ``export PATH=${HOME}/anaconda/bin:${PATH}`` # for [ba]sh
      * ``setenv PATH ${HOME}/anaconda/bin:${PATH}`` # for [t]csh

Make sure you have no environment variables set from an old UV-CDAT installation in your PATH/PYTHONPATH,LD_LIBRARY_PATH etc


Install PMP using conda/mamba
==========================================
You can install the PCMDI Metrics package from the PCMDI conda-forge channel. 
For the best performance, use `mamba`_. 
For faster installation without mamba, specify versions of python and pcmdi_metrics.

Create a new virtual environment and install PMP
  * Using `mamba`_   
      * ``mamba create -n [YOUR_CONDA_ENVIRONMENT] -c conda-forge pcmdi_metrics`` 
  
  * Using `conda`_
      * ``conda create -n [YOUR_CONDA_ENVIRONMENT] -c conda-forge python=[VERSION] pcmdi_metrics=[VERSION]``  
      * e.g. ``conda create -n pcmdi_metrics -c conda-forge python=3.10 pcmdi_metrics=3.0.1`` 
  
  * Using `conda`_ (alternative)
      * ``conda create -n [YOUR_CONDA_ENVIRONMENT]``
      * ``conda activate [YOUR_CONDA_ENVIRONMENT]``
      * ``conda install -c conda-forge python=[VERSION] pcmdi_metrics=[VERSION]``

  * (Another alternative) Install PMP in the current (or existing) virtual environment
      * Using `mamba`_: ``mamba install -c conda-forge pcmdi_metrics``
      * or using `conda`_: ``conda install -c conda-forge pcmdi_metrics``

To learn more about conda environments see: http://conda.pydata.org/docs/using/envs.html

.. _mamba: https://mamba.readthedocs.io/en/latest/installation.html
.. _Miniforge/Mambaforge: https://github.com/conda-forge/miniforge
.. _Miniconda: https://conda.io/miniconda.html
.. _Anaconda: https://www.anaconda.com/products/individual#Downloads
.. _conda: https://docs.conda.io/en/latest/

Note for Apple Silicon M1 or M2:

The CDAT dependency is not available for this architecture, so you will need to create an environment using x86 builds. This article from Towards Data Science has more information about managing Conda environments on Apple Silicon chips.

.. code-block:: python

  CONDA_SUBDIR=osx-64 conda create -n [YOUR_CONDA_ENVIRONMENT] -c conda-forge python=[VERSION]
  conda activate [YOUR_CONDA_ENVIRONMENT]
  conda config --env --set subdir osx-64
  mamba install -c conda-forge pcmdi_metrics or conda install -c conda-forge pcmdi_metrics=[VERSION]


Bypassing firewalls (optional)
==============================
If your institution has tight ssl certificate/security issues try before installing PMP:
  * ``conda config --set ssl_verify False``
  * ``binstar config --set ssl_verify False``
