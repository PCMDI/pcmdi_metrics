.. title:: PMP Overview

.. _overview:

***********
Overview
***********

The PMP provides a diverse suite of analysis utilities, each producing summary statistics that gauge the consistency between climate model simulations and available observations.

The primary application of the PMP is to evaluate simulations from the `Coupled Model Intercomparison Project (CMIP) <https://www.wcrp-climate.org/wgcm-cmip>`_. It can also be used to provide objective performance summaries during the model development process as well as for selected research purposes.

The sections below provide a brief summary of key aspects of the PMP design.

Introduction Video
------------------

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 80%; height: auto; margin-left: auto; margin-right: auto">
        <iframe src="https://www.youtube.com/embed/STfCq5Biqf0" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

|

References
----------
Lee, J., P. J. Gleckler, M.-S. Ahn, A. Ordonez, P. Ullrich, K. R. Sperber, K. E. Taylor, Y. Y. Planton, E. Guilyardi, P. Durack, C. Bonfils, M. D. Zelinka, L.-W. Chao, B. Dong, C. Doutriaux, C. Zhang, T. Vo, J. Boutte, M. F. Wehner, A. G. Pendergrass, D. Kim, Z. Xue, A. T. Wittenberg, and J. Krasting, 2024: Systematic and Objective Evaluation of Earth System Models: PCMDI Metrics Package (PMP) version 3. Geoscientific Model Development, 17, 3919–3948, https://doi.org/10.5194/gmd-17-3919-2024.

Gleckler et al. (2016), A more powerful reality test for climate models, Eos, 97, `doi:10.1029/2016EO051663 <https://eos.org/science-updates/a-more-powerful-reality-test-for-climate-models>`_.


Software Framework and Dependencies
------------------------------------

The PMP is based on `Python 3 <https://www.python.org/>`_ and built upon `Xarray <https://docs.xarray.dev/en/stable/>`_ and the Xarray Climate Data Analysis Tools (`xCDAT`_). 

Input/Output Format
--------------------

The PMP is designed to handle model output that adheres to the `Climate-Forecast (CF) data conventions <https://cfconventions.org/>`_. More specifically, because the PMP is used to routinely analyze simulations contributed to CMIP, it leverages `the data conventions developed in support of CMIP <https://pcmdi.llnl.gov/CMIP6/Guide/dataUsers.html>`_. Many modeling groups have workflows that conform to CMIP or are very similar to it, making it possible to adapt the PMP to assist in the model development process.

The PMP statistics are output in `JSON format <https://www.json.org/json-en.html>`_, and the underlying diagnostics from which they were derived are typically saved in `netCDF format <https://www.unidata.ucar.edu/software/netcdf>`_.


.. _xCDAT: https://xcdat.readthedocs.io/en/stable/
