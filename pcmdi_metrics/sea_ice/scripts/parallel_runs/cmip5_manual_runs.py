# Run this script to get the cmip5 runs that were missed in sea_ice_parallel_cmip5_sft.py
from pcmdi_metrics.misc.scripts import parallel_submitter

model_dict = {
    "EC-Earth": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/ICHEC/EC-EARTH/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_EC-EARTH_historical_%(realization)_185001-200512.nc",
        "area_template": "/p/css03/cmip5_css01/data/cmip5/output1/ICHEC/EC-EARTH/historical/fx/ocean/fx/r0i0p0/v20130313/areacello/areacello_fx_EC-EARTH_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css01/data/cmip5/output1/ICHEC/EC-EARTH/historical/fx/ocean/fx/r0i0p0/v20130313/sftof/sftof_fx_EC-EARTH_historical_r0i0p0.nc",
    },
    "CanCM4": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanCM4/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_CanCM4_historical_%(realization)_*-*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanCM4/decadal1960/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_CanCM4_decadal1960_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanCM4/decadal1960/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_CanCM4_decadal1960_r0i0p0.nc",
        "area_var": "areacella",
    },
    "CanESM2": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanESM2/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_CanESM2_historical_%(realization)_*-*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanESM2/historical/fx/atmos/fx/r0i0p0/v20120410/areacella/areacella_fx_CanESM2_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanESM2/1pctCO2/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_CanESM2_1pctCO2_r0i0p0.nc",
        "area_var": "areacella",
    },
    "bcc-csm1-1-m": {
        "dir_template": "/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1-m/historical/mon/seaIce/OImon/%(realization)/v20120709/sic/",
        "file_template": "sic_OImon_bcc-csm1-1-m_historical_%(realization)_*.nc",
        "area_template": "/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1-m/piControl/fx/ocean/fx/r0i0p0/v20130307/areacello/areacello_fx_bcc-csm1-1-m_piControl_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1-m/piControl/fx/ocean/fx/r0i0p0/v20130307/sftof/sftof_fx_bcc-csm1-1-m_piControl_r0i0p0.nc",
    },
    "CCSM4": {
        "dir_template": "/p/css03/esgf_publish/cmip5/gdo2/cmip5/output1/NCAR/CCSM4/historical/mon/seaIce/OImon/%(realization)/v20120202/sic/",
        "file_template": "sic_OImon_CCSM4_historical_%(realization)_*-*.nc",
        "area_template": "/p/css03/esgf_publish/cmip5/gdo2/cmip5/output1/NCAR/CCSM4/historical/fx/ocean/fx/r0i0p0/v20120614/areacello/areacello_fx_CCSM4_historical_r0i0p0.nc",
        "mask_template": "",
    },
    "CESM1-CAM5-1-FV2": {
        "dir_template": "/p/css03/cmip5_css01/data/cmip5/output1/NSF-DOE-NCAR/CESM1-CAM5-1-FV2/historical/mon/seaIce//OImon/%(realization)/v20120605/sic/",
        "file_template": "sic_OImon_CESM1-CAM5-1-FV2_historical_%(realization)_*.nc",
        "area_template": "/p/css03/cmip5_css01/data/cmip5/output1/NSF-DOE-NCAR/CESM1-CAM5/historical/fx/ocean/fx/r0i0p0/v20130315/areacello/areacello_fx_CESM1-CAM5_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css01/data/cmip5/output1/NSF-DOE-NCAR/CESM1-CAM5/historical/fx/ocean/fx/r0i0p0/v20130315/sftof/sftof_fx_CESM1-CAM5_historical_r0i0p0.nc",
    },
    "HadGEM2-AO": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/NIMR-KMA/HadGEM2-AO/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_HadGEM2-AO_historical_%(realization)_*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/MOHC/HadGEM2-CC/historical/fx/ocean/fx/r0i0p0/areacello/1/areacello_fx_HadGEM2-CC_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/MOHC/HadGEM2-CC/historical/fx/ocean/fx/r0i0p0/sftof/1/sftof_fx_HadGEM2-CC_historical_r0i0p0.nc",
    },
    "GISS-E2-R-CC": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-R-CC/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_GISS-E2-R-CC_historical_%(realization)_*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-R/historical/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_GISS-E2-R_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-R/historical/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_GISS-E2-R_historical_r0i0p0.nc",
        "area_var": "areacella",
    },
    "GISS-E2-R": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-R/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_GISS-E2-R_historical_%(realization)_*-*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-R/historical/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_GISS-E2-R_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-R/historical/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_GISS-E2-R_historical_r0i0p0.nc",
        "area_var": "areacella",
    },
    "GISS-E2-H-CC": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-H-CC/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_GISS-E2-H-CC_historical_%(realization)_*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-H/historical/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_GISS-E2-H_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-H/historical/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_GISS-E2-H_historical_r0i0p0.nc",
        "area_var": "areacella",
    },
    "GISS-E2-H": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-H/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_GISS-E2-H_historical_%(realization)_*-*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-H/historical/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_GISS-E2-H_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/NASA-GISS/GISS-E2-H/historical/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_GISS-E2-H_historical_r0i0p0.nc",
        "area_var": "areacella",
    },
    "inmcm4": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/INM/inmcm4/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_inmcm4_historical_%(realization)_*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/INM/inmcm4/esmrcp85/fx/ocean/fx/r0i0p0/areacello/1/areacello_fx_inmcm4_esmrcp85_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/INM/inmcm4/esmrcp85/fx/ocean/fx/r0i0p0/sftof/1/sftof_fx_inmcm4_esmrcp85_r0i0p0.nc",
    },
    "NorESM1-M": {
        "dir_template": "/p/css03/esgf_publish/cmip5/output1/NCC/NorESM1-M/historical/mon/seaIce/OImon/%(realization)/v20120227/sic/",
        "file_template": "sic_OImon_NorESM1-M_historical_%(realization)_*.nc",
        "area_template": "/p/css03/esgf_publish/cmip5/output1/NCC/NorESM1-M/historicalGHG/fx/ocean/fx/r0i0p0/v20110918/areacello/areacello_fx_NorESM1-M_historicalGHG_r0i0p0.nc",
        "mask_template": "/p/css03/esgf_publish/cmip5/output1/NCC/NorESM1-M/historicalGHG/fx/ocean/fx/r0i0p0/v20110918/sftof/sftof_fx_NorESM1-M_historicalGHG_r0i0p0.nc",
    },
    "CSIRO-Mk3-6-0": {
        "dir_template": "/p/css03/cmip5_css02/data/cmip5/output1/CSIRO-QCCCE/CSIRO-Mk3-6-0/historical/mon/seaIce/OImon/%(realization)/sic/1/",
        "file_template": "sic_OImon_CSIRO-Mk3-6-0_historical_%(realization)_*-*.nc",
        "area_template": "/p/css03/cmip5_css02/data/cmip5/output1/CSIRO-QCCCE/CSIRO-Mk3-6-0/historical/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_CSIRO-Mk3-6-0_historical_r0i0p0.nc",
        "mask_template": "/p/css03/cmip5_css02/data/cmip5/output1/CSIRO-QCCCE/CSIRO-Mk3-6-0/historical/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_CSIRO-Mk3-6-0_historical_r0i0p0.nc",
        "area_var": "areacella",
    },
}

cmd_list = []
log_list = []
mip = "cmip5"
var = "sic"
for model in model_dict:
    area_var = "areacello"
    if "area_var" in model_dict[model]:
        area_var = model_dict[model]["area_var"]
    if model_dict[model]["mask_template"] == "":
        cmd_list.append(
            "./sea_ice_driver.py -p parameter_file_cmip5.py --case_id "
            + model
            + " --test_data_set "
            + model
            + " --test_data_path "
            + model_dict[model]["dir_template"]
            + " --filename_template "
            + model_dict[model]["file_template"]
            + " --area_template "
            + model_dict[model]["area_template"]
            + " --area_var "
            + area_var
            + " --generate_mask"
        )
    elif len(model_dict[model]["mask_template"]) > 0:
        cmd_list.append(
            "./sea_ice_driver.py -p parameter_file_cmip5.py --case_id "
            + model
            + " --test_data_set "
            + model
            + " --test_data_path "
            + model_dict[model]["dir_template"]
            + " --filename_template "
            + model_dict[model]["file_template"]
            + " --area_template "
            + model_dict[model]["area_template"]
            + " --area_var "
            + area_var
            + " --sft_filename_template "
            + model_dict[model]["mask_template"]
        )
    log_list.append("log_" + mip + "_" + var + "_" + model)

print(cmd_list)
num_cpus = 4
parallel_submitter(
    cmd_list,
    log_dir="./log_cmip5_extras",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
