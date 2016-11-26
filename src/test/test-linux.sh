rm -rf ~/github/pcmdi_metrics/pcmdi_install_test_results

cd ~/github/pcmdi_metrics
source activate temp13
python setup.py install
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/basic_test_parameters_file.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/gensftlf_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/keep_going_on_error_varname_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/level_data_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/nosftlf_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/obs_by_name_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/region_specs_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/salinity_test.py
python ~/github/pcmdi_metrics/src/python/pcmdi/scripts/driver/run_pmp.py -p ~/github/pcmdi_metrics/src/test/misc/units_test.py
source deactivate temp13

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'basic_test_parameter_file.py'
diff ~/github/pcmdi_metrics/test/pcmdi/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
diff ~/github/pcmdi_metrics/test/pcmdi/installationTest/tos_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'gensftlf_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/gensftlfTest/tas_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/gensftlfTest/tas_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'keep_going_on_error_varname_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/keep_going_on_error_varnameTest/tos_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/keep_going_on_error_varnameTest/tos_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'level_data_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/level_data/ta-200_2.5x2.5_regrid2_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/level_data/ta-200_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'nosftlf_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/nosftlfTest/tas_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/nosftlfTest/tas_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'obs_by_name_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/obsByNameTest/tas_2.5x2.5_regrid2_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/obsByNameTest/tas_2.5x2.5_regrid2_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'region_specs_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/customRegions/tas_2.5x2.5_regrid2_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/customRegions/tas_2.5x2.5_regrid2_linear_metrics.json
echo '==================================================================================='
diff ~/github/pcmdi_metrics/test/pcmdi/customRegions/tos_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/customRegions/tos_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'salinity_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/salinityTest/sos_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/salinityTest/sos_2.5x2.5_esmf_linear_metrics.json

echo '==================================================================================='
echo '==================================================================================='
echo '==================================================================================='
echo 'units_test.py'
diff ~/github/pcmdi_metrics/test/pcmdi/unitsTest/tas_2.5x2.5_esmf_linear_metrics.json ~/github/pcmdi_metrics/pcmdi_install_test_results/metrics_results/unitsTest/tas_2.5x2.5_esmf_linear_metrics.json
