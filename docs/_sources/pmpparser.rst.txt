*********
PMPParser
*********

Installing PMPParser
####################
**Via Anaconda: get the nightly from or after October 18, 2016** 

::

   conda install pcmdi_metrics=2016.10.18 -c pcmdi/label/nightly -c uvcdat

**Manually: clone the repo and just run:**

::

   python setup.py install

Information 
############
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
########

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

