.. title:: PMP Installation

.. _install:

************
Installation
************

The PCMDI Metrics Package (PMP) is available for **Linux-64** and **macOS-64** (including Intel and Apple Silicon via Rosetta 2). Support for Windows is currently unavailable.

You can find the package details on `conda-forge <https://anaconda.org/conda-forge/pcmdi_metrics>`_.

System Requirements
===================

To use PMP, you must have a conda-based distribution installed. We recommend one of the following:

* Install the `Anaconda`_ package (we recommend installing this for each user)
* Alternatives include `Miniconda`_ or `Miniforge/Mambaforge`_
* If using Anaconda or Miniconda, we recommend also installing `mamba`_ for better performance

Ensure anaconda is in your PATH (assuming anaconda is installed in ${HOME}/anaconda

.. code-block:: bash

   # For bash/zsh
   export PATH="${HOME}/anaconda/bin:${PATH}"

   # For tcsh
   setenv PATH "${HOME}/anaconda/bin:${PATH}"

Ensure your conda distribution is in your ``PATH``. For example, if installed in your home directory:

Standard Installation
=====================

We recommend creating a fresh virtual environment for PMP to avoid dependency conflicts.

Using Mamba (Recommended)
-------------------------
.. code-block:: bash

   mamba create -n pmp_env -c conda-forge pcmdi_metrics
   conda activate pmp_env

Using Conda
-----------
.. code-block:: bash

   conda create -n pmp_env -c conda-forge pcmdi_metrics
   conda activate pmp_env

To speed up installation with conda, you can explicitly specify the Python and PMP versions.

.. code-block:: bash

   conda create -n pmp_env -c conda-forge python=3.10 pcmdi_metrics=4.0.2
   conda activate pmp_env

Installation in Existing Environments
-------------------------------------
.. code-block:: bash

   mamba install -c conda-forge pcmdi_metrics
   # OR
   conda install -c conda-forge pcmdi_metrics

To learn more about conda environments see: http://conda.pydata.org/docs/using/envs.html


Advanced & Legacy Installation
==============================

.. admonition:: Support for Apple Silicon (M1/M2/M3)
   :class: note

   Modern versions of PMP (v3.10+) generally support ARM64 architecture natively. However, if you are installing **PMP v3.8 or lower**, you may encounter issues due to legacy dependencies (like older CDAT components). 

   If native installation fails, you can force an Intel-based (x86) environment:

   .. code-block:: bash

      # Create the environment as an x86 architecture
      CONDA_SUBDIR=osx-64 conda create -n pmp_legacy -c conda-forge python=3.8
      
      # Lock the architecture for this environment
      conda activate pmp_legacy
      conda config --env --set subdir osx-64
      
      # Install the legacy PMP version
      mamba install -c conda-forge pcmdi_metrics=3.8.0


Troubleshooting
===============

Environment Cleanup
-------------------
.. warning::
   Ensure no environment variables from old **UV-CDAT** installations (e.g., ``PATH``, ``PYTHONPATH``, ``LD_LIBRARY_PATH``) are set, as these can cause runtime conflicts.

Firewalls and SSL
-----------------
If your institution has strict SSL certificate inspection, you can bypass verification (at your own risk):

.. code-block:: bash

   conda config --set ssl_verify False

.. seealso::
   For more on managing conda environments, see the `Official Conda Documentation <http://conda.pydata.org/docs/using/envs.html>`_.




.. _mamba: https://mamba.readthedocs.io/en/latest/installation.html
.. _Miniforge/Mambaforge: https://github.com/conda-forge/miniforge
.. _Miniconda: https://conda.io/miniconda.html
.. _Anaconda: https://www.anaconda.com/products/individual#Downloads
.. _conda: https://docs.conda.io/en/latest/