from pcmdi_metrics.misc.scripts import parallel_submitter

model_dict = {
    "E3SM-1-1": {
        "dir_template": "/p/user_pub/work/CMIP6/CMIP/E3SM-Project/E3SM-1-1/historical/%(realization)/SImon/siconc/gr/*/",
        "file_template": "siconc_SImon_E3SM-1-1_historical_%(realization)_gr_*-*.nc",
        "area_template": "/p/user_pub/work/CMIP6/C4MIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Ofx/areacello/gr/v20210126/areacello_Ofx_E3SM-1-1_hist-bgc_r1i1p1f1_gr.nc",
        "mask_template": "/p/user_pub/work/CMIP6/C4MIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/fx/sftlf/gr/v20201015/sftlf_fx_E3SM-1-1_hist-bgc_r1i1p1f1_gr.nc",
    },
    "E3SM-1-0": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/UCSB/E3SM-1-0/historical/%(realization)/SImon/siconc/gr/*/",
        "file_template": "siconc_SImon_E3SM-1-0_historical_%(realization)_gr_*-*.nc",
        "area_template": "/p/user_pub/work/CMIP6/C4MIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Ofx/areacello/gr/v20210126/areacello_Ofx_E3SM-1-1_hist-bgc_r1i1p1f1_gr.nc",
        "mask_template": "/p/user_pub/work/CMIP6/C4MIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/fx/sftlf/gr/v20201015/sftlf_fx_E3SM-1-1_hist-bgc_r1i1p1f1_gr.nc",
    },
    "E3SM-1-1-ECA": {
        "dir_template": "/p/user_pub/work/CMIP6/CMIP/E3SM-Project/E3SM-1-1-ECA/historical/%(realization)/SImon/siconc/gr/*/",
        "file_template": "siconc_SImon_E3SM-1-1-ECA_historical_%(realization)_gr_*-*.nc",
        "area_template": "/p/user_pub/work/CMIP6/C4MIP/E3SM-Project/E3SM-1-1-ECA/ssp585-bgc/r1i1p1f1/Ofx/areacello/gr/v20210126/areacello_Ofx_E3SM-1-1-ECA_ssp585-bgc_r1i1p1f1_gr.nc",
        "mask_template": "",
    },
    "BCC-ESM1": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/BCC/BCC-ESM1/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_BCC-ESM1_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/AerChemMIP/BCC/BCC-ESM1/ssp370/r1i1p1f1/Ofx/areacello/gn/v20201021/areacello_Ofx_BCC-ESM1_ssp370_r1i1p1f1_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/AerChemMIP/BCC/BCC-ESM1/ssp370/r1i1p1f1/Ofx/sftof/gn/v20201021/sftof_Ofx_BCC-ESM1_ssp370_r1i1p1f1_gn.nc",
    },
    "CAS-ESM2-0": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/CAS/CAS-ESM2-0/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_CAS-ESM2-0_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/CAS/CAS-ESM2-0/1pctCO2/r1i1p1f1/Ofx/areacello/gn/v20201229/areacello_Ofx_CAS-ESM2-0_1pctCO2_r1i1p1f1_gn.nc",
        "mask_template": "",
    },
    "UKESM1-0-LL": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/UKESM1-0-LL/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_UKESM1-0-LL_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/UKESM1-0-LL/piControl/r1i1p1f2/Ofx/areacello/gn/v20190705/areacello_Ofx_UKESM1-0-LL_piControl_r1i1p1f2_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/UKESM1-0-LL/piControl/r1i1p1f2/Ofx/sftof/gn/v20190705/sftof_Ofx_UKESM1-0-LL_piControl_r1i1p1f2_gn.nc",
    },
    "UKESM1-1-LL": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/UKESM1-1-LL/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_UKESM1-1-LL_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/UKESM1-0-LL/piControl/r1i1p1f2/Ofx/areacello/gn/v20190705/areacello_Ofx_UKESM1-0-LL_piControl_r1i1p1f2_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/UKESM1-0-LL/piControl/r1i1p1f2/Ofx/sftof/gn/v20190705/sftof_Ofx_UKESM1-0-LL_piControl_r1i1p1f2_gn.nc",
    },
    "HadGEM3-GC31-LL": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/HadGEM3-GC31-LL/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_HadGEM3-GC31-LL_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/HadGEM3-GC31-LL/piControl/r1i1p1f1/Ofx/areacello/gn/v20190709/areacello_Ofx_HadGEM3-GC31-LL_piControl_r1i1p1f1_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/HadGEM3-GC31-LL/piControl/r1i1p1f1/Ofx/sftof/gn/v20190709/sftof_Ofx_HadGEM3-GC31-LL_piControl_r1i1p1f1_gn.nc",
    },
    "HadGEM3-GC31-MM": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/HadGEM3-GC31-MM/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_HadGEM3-GC31-MM_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/HadGEM3-GC31-MM/piControl/r1i1p1f1/Ofx/areacello/gn/v20200108/areacello_Ofx_HadGEM3-GC31-MM_piControl_r1i1p1f1_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CMIP/MOHC/HadGEM3-GC31-MM/piControl/r1i1p1f1/Ofx/sftof/gn/v20200108/sftof_Ofx_HadGEM3-GC31-MM_piControl_r1i1p1f1_gn.nc",
    },
    "GISS-E2-2-H": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/NASA-GISS/GISS-E2-2-H/historical/%(realization)/SImon/siconc/gr/*/",
        "file_template": "siconc_SImon_GISS-E2-2-H_historical_%(realization)_gr_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/NASA-GISS/GISS-E2-1-H/piControl/r1i1p1f1/Ofx/areacello/gr/v20180824/areacello_Ofx_GISS-E2-1-H_piControl_r1i1p1f1_gr.nc",
        "mask_template": "",
    },
    "GISS-E2-1-H": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/NASA-GISS/GISS-E2-1-H/historical/%(realization)/SImon/siconc/gr/*/",
        "file_template": "siconc_SImon_GISS-E2-1-H_historical_%(realization)_gr_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/NASA-GISS/GISS-E2-1-H/piControl/r1i1p1f1/Ofx/areacello/gr/v20180824/areacello_Ofx_GISS-E2-1-H_piControl_r1i1p1f1_gr.nc",
        "mask_template": "",
    },
    "CAMS-CSM1-0": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/CAMS/CAMS-CSM1-0/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_CAMS-CSM1-0_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/CAMS/CAMS-CSM1-0/1pctCO2/r2i1p1f1/Ofx/areacello/gn/v20190830/areacello_Ofx_CAMS-CSM1-0_1pctCO2_r2i1p1f1_gn.nc",
        "mask_template": "",
    },
    "INM-CM5-0": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/INM/INM-CM5-0/historical/%(realization)/SImon/siconc/gr1/*/",
        "file_template": "siconc_SImon_INM-CM5-0_historical_%(realization)_gr1_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/INM/INM-CM5-0/piControl/r1i1p1f1/Ofx/areacello/gr1/v20201029/areacello_Ofx_INM-CM5-0_piControl_r1i1p1f1_gr1.nc",
        "mask_template": "",
    },
    "INM-CM4-8": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/INM/INM-CM4-8/historical/%(realization)/SImon/siconc/gr1/*/",
        "file_template": "siconc_SImon_INM-CM4-8_historical_%(realization)_gr1_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/INM/INM-CM4-8/piControl/r1i1p1f1/Ofx/areacello/gr1/v20201029/areacello_Ofx_INM-CM4-8_piControl_r1i1p1f1_gr1.nc",
        "mask_template": "",
    },
    "TaiESM1": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/AS-RCEC/TaiESM1/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_TaiESM1_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/AerChemMIP/AS-RCEC/TaiESM1/hist-piNTCF/r1i1p1f1/Ofx/areacello/gn/v20220103/areacello_Ofx_TaiESM1_hist-piNTCF_r1i1p1f1_gn.nc",
        "mask_template": "",
    },
    "MIROC-ES2L": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC-ES2L/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_MIROC-ES2L_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC-ES2L/historical/r1i1000p1f2/Ofx/areacello/gn/v20210107/areacello_Ofx_MIROC-ES2L_historical_r1i1000p1f2_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC-ES2L/historical/r1i1000p1f2/Ofx/sftof/gn/v20210107/sftof_Ofx_MIROC-ES2L_historical_r1i1000p1f2_gn.nc",
    },
    "NorESM2-MM": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/NCC/NorESM2-MM/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_NorESM2-MM_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/NCC/NorESM2-MM/historical/r3i1p1f1/Ofx/areacello/gn/v20200702/areacello_Ofx_NorESM2-MM_historical_r3i1p1f1_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CMIP/NCC/NorESM2-MM/historical/r3i1p1f1/Ofx/sftof/gn/v20200702/sftof_Ofx_NorESM2-MM_historical_r3i1p1f1_gn.nc",
    },
    "ICON-ESM-LR": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/MPI-M/ICON-ESM-LR/historical/%(realization)/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_ICON-ESM-LR_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/MPI-M/ICON-ESM-LR/historical/r1i1p1f1/Ofx/areacello/gn/v20210215/areacello_Ofx_ICON-ESM-LR_historical_r1i1p1f1_gn.nc",
        "mask_template": "",
    },
    "CMCC-CM2-HR4": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/CMCC/CMCC-CM2-HR4/historical/r1i1p1f1/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_CMCC-CM2-HR4_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/CMCC/CMCC-CM2-HR4/abrupt-4xCO2/r1i1p1f1/Ofx/areacello/gn/v20210624/areacello_Ofx_CMCC-CM2-HR4_abrupt-4xCO2_r1i1p1f1_gn.nc",
        "mask_template": "",
    },
    "CMCC-CM2-SR5": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/CMCC/CMCC-CM2-SR5/historical/r2i1p2f1/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_CMCC-CM2-SR5_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/CMCC/CMCC-CM2-SR5/historical/r2i1p2f1/Ofx/areacello/gn/v20211109/areacello_Ofx_CMCC-CM2-SR5_historical_r2i1p2f1_gn.nc",
        "mask_template": "",
    },
    "CMCC-ESM2": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/CMCC/CMCC-ESM2/historical/r1i1p1f1/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_CMCC-ESM2_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/ScenarioMIP/CMCC/CMCC-ESM2/ssp534-over/r1i1p1f1/Ofx/areacello/gn/v20210409/areacello_Ofx_CMCC-ESM2_ssp534-over_r1i1p1f1_gn.nc",
        "mask_template": "",
    },
    "NorESM2-LM": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/NCC/NorESM2-LM/historical/r1i1p1f1/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_NorESM2-LM_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/CMIP/NCC/NorESM2-LM/historical/r1i1p1f1/Ofx/areacello/gn/v20190815/areacello_Ofx_historical_NorESM2-LM_r1i1p1f1_gn.nc",
        "mask_template": "/p/css03/esgf_publish/CMIP6/CDRMIP/NCC/NorESM2-LM/esm-ssp534-over/r1i1p1f2/Ofx/sftof/gn/v20230616/sftof_Ofx_NorESM2-LM_esm-ssp534-over_r1i1p1f2_gn.nc",
    },
    "NESM3": {
        "dir_template": "/p/css03/esgf_publish/CMIP6/CMIP/NUIST/NESM3/historical/r1i1p1f1/SImon/siconc/gn/*/",
        "file_template": "siconc_SImon_NESM3_historical_%(realization)_gn_*-*.nc",
        "area_template": "/p/css03/esgf_publish/CMIP6/PMIP/NUIST/NESM3/lig127k/r1i1p1f1/Ofx/areacello/gn/v20190928/areacello_Ofx_NESM3_lig127k_r1i1p1f1_gn.nc",
        "mask_template": "",
    },
}


cmd_list = []
log_list = []
area_var = "areacello"
mip = "cmip6"
var = "siconc"
for model in model_dict:
    if model_dict[model]["mask_template"] == "":
        cmd_list.append(
            "./sea_ice_driver.py -p parameter_file_cmip6.py --case_id "
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
            "./sea_ice_driver.py -p parameter_file_cmip6.py --case_id "
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
num_cpus = 20
parallel_submitter(
    cmd_list,
    log_dir="./log_cmip6_extras",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
