rm -rf ~/pcmdi_metrics/pcmdi_install_test_results

source activate pmp
cd ~/pcmdi_metrics/
python setup.py install
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/basic_test_parameters_file.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/gensftlf_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/keep_going_on_error_varname_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/level_data_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/nosftlf_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/obs_by_name_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/region_specs_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/salinity_test.py
python ~/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_metrics_driver.py -p ~/pcmdi_metrics/test/pcmdi/units_test.py
source deactivate pmp

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'basic_test_parameter_file.py'
diff ~/pcmdi_metrics/test/pcmdi/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
diff ~/pcmdi_metrics/test/pcmdi/installationTest/tos_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'gensftlf_test.py'
diff ~/pcmdi_metrics/test/pcmdi/gensftlfTest/tas_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/gensftlfTest/tas_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'keep_going_on_error_varname_test.py'
diff ~/pcmdi_metrics/test/pcmdi/keep_going_on_error_varnameTest/tos_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/keep_going_on_error_varnameTest/tos_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'level_data_test.py'
diff ~/pcmdi_metrics/test/pcmdi/level_data/ta-200_2.5x2.5_regrid2_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/level_data/ta-200_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'nosftlf_test.py'
diff ~/pcmdi_metrics/test/pcmdi/nosftlfTest/tas_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/nosftlfTest/tas_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'obs_by_name_test.py'
diff ~/pcmdi_metrics/test/pcmdi/obsByNameTest/tas_2.5x2.5_regrid2_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/obsByNameTest/tas_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'region_specs_test.py'
diff ~/pcmdi_metrics/test/pcmdi/customRegions/tas_2.5x2.5_regrid2_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/customRegions/tas_2.5x2.5_regrid2_linear_metrics.json
echo '==================================================================================='
diff ~/pcmdi_metrics/test/pcmdi/customRegions/tos_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/customRegions/tos_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'salinity_test.py'
diff ~/pcmdi_metrics/test/pcmdi/salinityTest/sos_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/salinityTest/sos_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'units_test.py'
diff ~/pcmdi_metrics/test/pcmdi/unitsTest/tas_2.5x2.5_esmf_linear_metrics.json ~/pcmdi_metrics/pcmdi_install_test_results/metrics_results/unitsTest/tas_2.5x2.5_esmf_linear_metrics.json
