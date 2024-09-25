API Reference
=============

API Functions for Developpers
-----------------------------

.. currentmodule:: pcmdi_metrics

Below is a list of some API functions that are available in `pcmdi_metrics.` for developpers.


Land-sea mask
~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.create_land_sea_mask
    pcmdi_metrics.utils.apply_landmask
    pcmdi_metrics.utils.apply_oceanmask


Grid handling and re-gridding (horizontal interpolation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.create_target_grid
    pcmdi_metrics.utils.regrid
    

Quality control (QC)
~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.check_daily_time_axis
    pcmdi_metrics.utils.check_monthly_time_axis


Calendar-related functions
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.custom_season_average
    pcmdi_metrics.utils.custom_season_departure


Miscellaneous tools
~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.sort_human
    pcmdi_metrics.utils.fill_template
    pcmdi_metrics.utils.tree