.. title:: PMP API

API Reference
=============

APIs
----

.. currentmodule:: pcmdi_metrics

Unless specified, the following Application Programming Interfaces (APIs) are available in `pcmdi_metrics (> v3.6.1)` or higher.

Analysis & Diagnostics
~~~~~~~~~~~~~~~~~~~~~~

PMP is currently expanding its public APIs for diagnostics and metrics. This effort is intended to make more of PMP’s
capabilities available through a cleaner, more flexible and accessible for users and developers. As the API surface grows,
additional diagnostics and metric calculations will be exposed in a way that supports both programmatic use and
integration into workflows, while maintaining consistency with the package’s existing design and documentation conventions.

.. note::
   - ``variability_mode.eof_classification`` and ``sea_ice.calc_iiee_annual_cycle`` APIs are available in ``pcmdi_metrics`` version ``v4.1`` and later.
   - ``mjo.compute_mjo_ewr_from_dataset`` API is available in ``pcmdi_metrics`` version ``v4.1.1`` and later.
   - ``variability_mode``, ``qbo``, and ``hadley_cell`` APIs are available in version ``v4.2`` or later.
   - ``effective_resolution`` APIs are available in version ``v4.2.2`` or later.


Atmospheric Circulation & Dynamics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    effective_resolution.compute_effective_resolution
    effective_resolution.compute_effective_resolution_scalar
    effective_resolution.process_effective_resolution
    hadley_cell.hadley_cell_metrics
    qbo.compute_qbo_mjo_metrics

Tropical Variability
^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    mjo.compute_mjo_ewr_from_dataset

Extratropical Variability Modes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    variability_mode.NAO
    variability_mode.NAM
    variability_mode.SAM
    variability_mode.PNA
    variability_mode.NPO
    variability_mode.PSA1
    variability_mode.PSA2
    variability_mode.PDO
    variability_mode.NPGO
    variability_mode.AMO
    variability_mode.eof_classification

Cryosphere
^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    sea_ice.calc_iiee_annual_cycle


Custom calendars
~~~~~~~~~~~~~~~~

Functions for computing seasonal averages and departures with custom calendar definitions.

.. autosummary::
    :toctree: generated/

    utils.custom_season_average
    utils.custom_season_departure
    utils.replace_date_pattern


Data load
~~~~~~~~~

Load climate model and observational datasets using xCDAT.

.. autosummary::
    :toctree: generated/

    io.xcdat_open


Date
~~~~

Utilities for date string formatting, parsing, and finding overlapping time periods.

.. autosummary::
    :toctree: generated/

    utils.date_to_str
    utils.extract_date_components
    utils.find_overlapping_dates


Land-sea mask
~~~~~~~~~~~~~

Create and apply land-sea masks to datasets for ocean-only or land-only analysis.

.. autosummary::
    :toctree: generated/

    utils.create_land_sea_mask
    utils.apply_landmask
    utils.apply_oceanmask


Graphics
~~~~~~~~

Plotting functions for model evaluation and intercomparison. Example usages are available in the `demo notebooks <demo-notebooks.html#plots>`_.

.. autosummary::
    :toctree: generated/

    graphics.parallel_coordinate_plot
    graphics.portrait_plot
    graphics.TaylorDiagram


Grid and regrid
~~~~~~~~~~~~~~~

Functions for creating target grids and regridding datasets to different spatial resolutions.

.. autosummary::
    :toctree: generated/

    utils.create_target_grid
    utils.regrid


Region handling
~~~~~~~~~~~~~~~

Tools for defining, loading, and subsetting spatial regions from global datasets.

.. autosummary::
    :toctree: generated/

    io.load_regions_specs
    io.region_subset
    io.region_from_file


Retrieve data from xarray Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Helper functions for extracting coordinates, axes, and metadata from xarray Datasets.

.. autosummary::
    :toctree: generated/

    io.get_grid
    io.get_axis_list
    io.get_data_list
    io.get_latitude
    io.get_latitude_bounds
    io.get_latitude_key
    io.get_longitude
    io.get_longitude_bounds
    io.get_longitude_key
    io.get_time
    io.get_time_bounds
    io.get_time_bounds_key
    io.get_time_key
    io.select_subset


Quality control (QC) and repair
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Functions for checking and repairing time axes in climate datasets.

.. autosummary::
    :toctree: generated/

    utils.check_daily_time_axis
    utils.check_monthly_time_axis
    utils.regenerate_time_axis


Miscellaneous tools
~~~~~~~~~~~~~~~~~~~

General utility functions for file system operations and template string formatting.

.. autosummary::
    :toctree: generated/

    utils.sort_human
    utils.fill_template
    utils.tree


Viewer
~~~~~~

Generate interactive HTML output viewer for multi-model metric results. Available in `pcmdi_metrics (> v3.9.1)` or higher.

.. autosummary::
    :toctree: generated/

    viewer.generate_pmp_output_viewer_multimodel