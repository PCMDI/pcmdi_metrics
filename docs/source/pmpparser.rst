*********
PMPParser 
*********

PMPParser is basically a wrapper around ArgumentParser. It has the ability for users to use the default arguments which are listed below or define their own, which can overwrite the default arguments if needed. PMPParser also supports reading in a parameter file from the command line and then allowing for the user to modify select parameter values as needed.

Default Arguments
^^^^^^^^^^^^^^^^^

==============================  =====================================
Value        					Argument      
==============================  =====================================
parameter       				-p or --parameter
case_id 						--case_id
vars							-v or --vars
regions 						--regions
regions_values 					--regions_values
reference_data_set 				-r or --reference_data_set
reference_data_path 			--reference_data_path
test_data_set 					-t or --test_data_set
test_data_path 					--test_data_path
target_grid 					--target_grid
regrid_tool 					--regrid_tool
regrid_method 					--regrid_method
regrid_tool_ocn 				-regrid_tool_ocn
regrid_method_ocn 				-regrid_method_ocn
period 							--period
realization 					--realization
simulation_description_mapping 	--simulation_description_mapping
model_tweaks 					--model_tweaks
ext 							--ext
dry_run 						--dry_run
filename_template 				--filename_template
sftlf_filename_template 		--sftlf_filename_template
custom_observations 			--custom_observations
metrics_output_path 			--metrics_output_path
filename_output_template 		--filename_output_template
save_test_clims 				--save_test_clims
test_clims_interpolated_output 	--test_clims_interpolated_output
compute_custom_metrics 			--compute_custom_metrics
==============================  =====================================

Examples
^^^^^^^^

How to use PMPParser in your driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   #!/usr/bin/env python
   from pcmdi_metrics.pcmdi.pmp_parser import *
   # soon the import statement will be:
   # from pcmdi_metrics.driver.pmp_parser import *
   parser = PMPParser() # Includes all default options

   parser.add_argument(
       '-n', '--newarg',
       type=ast.literal_eval, #loading in a dictionary
       dest='newarg',
       help='description',
       required=False)

   parameter = parser.get_parameter()
   # All parameters can be referenced like so:
   # parameter.vars
   # parameter.regions
   # ...


Reading in a list from the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   driver -v var1 var2 var3

results in ``parameter.var`` being ``['var1', 'var2', 'var3']``

Reading in a dictionary from the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   driver --regions '{"tas": [None, "terre", "ocean"], "tos": [None, ]}'

results in ``parameter.regions`` being ``{'tos': [None], 'tas': [None, 'terre', 'ocean']}``



More PMPParser Info
^^^^^^^^^^^^^^^^^^^

This guide is intended to bring developers (and maybe users) up to speed with the changes done when refactoring pmp to use cdp. If you don't know what cdp is, look `here <https://github.com/UV-CDAT/CDP>`_.

What changed
------------
Vocabulary for the parameter has changed to account for the new paradigm of reference data set vs test data set, instead of just observation vs model. `See here <https://github.com/PCMDI/pcmdi_metrics/wiki/PMPParser#default-arguments>`_

All other cdp related stuff is in the ``src/python/pcmdi/scripts/driver/`` folder. This include the ``pmp_parser``, which is no longer in ``src/python/pcmdi/``.

The majority of the work was done to the ``pcmdi_metrics_driver.py``, which is now named ``pcmdi_metrics_driver_legacy.py``. The new driver is now named ``pcmdi_metrics_driver.py``. Both are executable via the command line. The next section details the changes done to the driver.

Changes to the driver
---------------------

Though not a requirement of cdp, the driver is now programmed in an object-oriented fashion. There are many good reasons to this, which you can see by googling it. Below is an explanation of the classes, which are located in ``src/python/pcmdi/scripts/driver/``.

* **PMPParameter**: Inherits from ``CDPParameter``. Contains the stuff that's usually in a Python parameter script. Eventually, we want to add error checking to the ``heck_values()`` function.

* **PMPParser**: Inherits from ``CDPParser``, which it based on ``ArgumentParser``. You can add/remove/change the arguments in the ``load_default_args()`` function if needed.

* **DataSet**: One of the largest forthcoming changes to pmp is that observations and models can be used interchangeably. To do so, both must be of the same class, which is ``DataSet``. ``DataSet`` is an abstract class that acts as an `interface <https://en.wikipedia.org/wiki/Interface_(computing)#Programming_to_the_interface>`_, with some functionality through static methods. Each ``DataSet`` object also has an attribute of type ``pmp_io``.

* **Model**: A concrete version of ``DataSet``. Looking at this from the legacy code, this is all of the stuff in the ``model_versions`` loop. It just does stuff related to ``_model_file``, which was called ``MODEL`` in the legacy version.

* **Observation**: Another concrete version of ``DataSet``. Looking at this from the legacy code, this is all of the stuff in the ``refs`` loop. It just does stuff related to ``_obs_file``, which was called ``OBS`` in the legacy version.

* **PMPDriver**: Inherits from ``CDPDriver``. Has a ``PMPParser`` to get command line arguments. Composed of three functions, ``check_parameter()``, ``run_diags()``, ``export()``. ``check_parameter()`` checks that the ``self.parameter`` has all of the stuff needed for this driver. ``run_diags()`` runs the diags. ``export()`` should export the results, but doesn't do that yet because that's already done in ``run_diags`` (but eventually will do it).

* **RunDiags**: The actual work for ``PMPDriver.run_diags()`` is done by this class. **This is where the main functionality is**. This loops through all of the ``vars``, ``regions``, ``reference_data_set`` and ``test_data_set`` in that order. This also determines if the comparison is obs vs obs, obs vs model, or model vs model.

* **OutputMetrics** When ``RunDiags`` gets the data from ``Model`` or ``Observation`` (via ``DataSet.get()``), these get sent to ``OutputMetrics`` which creates the ``metrics_dictionary``, computes the metrics needed, and outputs the results. Also has an ``out_file`` and ``clim_file``, which were respectively ``OUT`` and ``CLIM`` previously.





