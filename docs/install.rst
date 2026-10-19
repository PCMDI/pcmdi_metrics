.. title:: PMP Installation

.. _install:

************
Installation
************

The PCMDI Metrics Package (PMP) is available for **Linux-64** and **macOS-64**. Modern PMP releases generally support both Intel and Apple Silicon systems natively. Windows support has not been thoroughly tested.

You can find the package details on `conda-forge <https://anaconda.org/conda-forge/pcmdi_metrics>`_.

PMP can be installed either with a conda-based package manager such as ``mamba`` or ``conda``, or by using Docker.

System Requirements
===================

For conda-based installation, you must have a conda distribution installed. We recommend one of the following:

* Install the `Anaconda`_ package (we recommend installing this for each user)
* Alternatives include `Miniconda`_ or `Miniforge/Mambaforge`_
* If using Anaconda or Miniconda, we recommend also installing `mamba`_ for better performance

Ensure your conda distribution is in your ``PATH``. For example, if Anaconda is installed in ``${HOME}/anaconda``:

.. code-block:: bash

   # For bash/zsh
   export PATH="${HOME}/anaconda/bin:${PATH}"

   # For tcsh
   setenv PATH "${HOME}/anaconda/bin:${PATH}"

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

   conda create -n pmp_env -c conda-forge python=3.10 pcmdi_metrics=4.2.1
   conda activate pmp_env

Installation in Existing Environments
-------------------------------------
.. code-block:: bash

   mamba install -c conda-forge pcmdi_metrics
   # OR
   conda install -c conda-forge pcmdi_metrics

To learn more about conda environments see: http://conda.pydata.org/docs/using/envs.html


Docker Installation
===================

Docker packages PMP together with its runtime environment in a container image. This is useful when you want a reproducible installation without managing the Python and system dependencies directly on your host machine.

Why use Docker?
---------------

* Reproducible PMP environment across different systems
* Reduced dependency conflicts on the host machine
* Easier deployment on Linux servers, cloud systems, and shared platforms

Build the PMP Docker image locally from the repository root:

In the examples below, ``pmp:latest`` is just a local image tag name.

.. code-block:: bash

   docker build -t pmp:latest .

Run the default container command to confirm PMP is installed:

.. code-block:: bash

   docker run --rm pmp:latest

Start an interactive shell in the container:

.. code-block:: bash

   docker run --rm -it pmp:latest bash

Mount a host directory so the container can access your input data or write output files:

.. code-block:: bash

   docker run --rm -it -v /path/to/local/data:/data pmp:latest bash

Inside the container, PMP is installed in the preconfigured conda environment and the command-line tools are available on ``PATH``.

Prebuilt Docker Image
---------------------

If PMP is published on Docker Hub, users will be able to pull a prebuilt image instead of building locally.

Current Docker Hub image location:

.. code-block:: text

   docker.io/lee1043/pcmdi_metrics

Example pull command:

.. code-block:: bash

   docker pull lee1043/pcmdi_metrics:latest

.. note::

   The preferred long-term image location would be ``docker.io/pcmdi/pcmdi_metrics``. For now, the published image is available from ``docker.io/lee1043/pcmdi_metrics``.


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
