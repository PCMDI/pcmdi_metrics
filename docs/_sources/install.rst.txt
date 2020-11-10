.. _install:

*******
Install
*******

We offer two paths to install the PCMDI Metrics package. The recommended method is to install the Anaconda package and then install PCMDI Metrics using our conda channel. Alternatively, the older, more complex build method (from the source install method) is also supported, and used by developers contributing to the Github repository.   

Anaconda installation (recommended)
===================================
A primary advantage of the Anaconda install path is that it is user-centric. This allows users on super computing systems with limited permissions to fully configure their local PMP install. We offer an installation for anaconda users under linux-64 or osx-64. Support for Windows is not available yet.

Anaconda package: https://anaconda.org/PCMDI/pcmdi_metrics/files

All Platforms System Requirements
---------------------------------

  * Install the `Anaconda for Python 3.7 <https://www.anaconda.com/products/individual#Downloads>`_ package (we recommend installing this for each user)

  * Make sure anaconda is in your PATH (assuming anaconda is installed in ${HOME}/anaconda

      - ``export PATH=${HOME}/anaconda/bin:${PATH}`` for [ba]sh
      - ``setenv PATH ${HOME}/anaconda/bin:${PATH}`` for [t]csh

Make sure you have no environment variables set from an old UV-CDAT installation in your PATH/PYTHONPATH,LD_LIBRARY_PATH etc

To learn more about conda environments see: http://conda.pydata.org/docs/using/envs.html

Bypassing firewalls
-------------------

If your institution has tight ssl certificate/security issues try:

::

	conda config --set ssl_verify False
	binstar config --set ssl_verify False

Installing the PCMDI Metrics Package (PMP)
------------------------------------------

Using the conda package manager, you can install the PCMDI Metrics package from the PCMDI conda channel. Your environment must contain `CDAT <https://cdat.llnl.gov/>`_. See `CDAT Install <https://github.com/CDAT/cdat/wiki/install>`_ for more instructions.

::

	source activate [YOUR_CDAT_ENABLED_CONDA_ENVIRONMENT]
	conda install pcmdi_metrics -c cdat-forge

Getting the latest nightly of PMP and CDAT (recommended)
--------------------------------------------------------

These commands create a new conda environment containing the nightly builds of PMP and CDAT:

::

	conda create -n [YOUR_ENV_NAME_HERE] -c cdat/label/nightly -c pcmdi/label/nightly -c conda-forge -c cdat pcmdi_metrics
	source activate [YOUR_ENV_NAME_HERE]

Install from Source
====================

In some cases, it may be necessary to install PMP via the source code. Some example instructions are provided here to clone the pcmdi_metrics repo, install PMP from a branch, and run tests.

::

	conda create -n test_pcmdi -c cdat/label/v8.2.1 -c pcmdi/label/nightly -c conda-forge cdat pcmdi_metrics testsrunner
	conda activate test_pcmdi
	git clone https://github.com/pcmdi/pcmdi_metrics.git
	cd pcmdi_metrics
	git checkout -b <your branch>
	python setup.py install
	python run_tests.py -H -v 2
