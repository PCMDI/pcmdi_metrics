#!/bin/tcsh

# A script to run file generation
make_obs_clim.py /work/durack1/csiro/climatologies/WOA09_nc/monthly/s0112.nc salinity_oa_mean sos NODC-WOA09 1772 2008
make_obs_clim.py /work/durack1/Shared/obs_data/AQUARIUS/130605_AQUARIUS_V2_monthly_SSS_20110817-20130416.nc sos sos JPL-Aquarius-v2 2011 2013
make_obs_clim.py /work/durack1/Shared/obs_data/Argo/UCSD_monthly/130606_RG_ArgoClim_33pfit_2013_annual.nc ARGO_SALINITY_ANNUAL_ANOMALY sos UCSD-ARGO 2004 2012
make_obs_clim.py /work/durack1/csiro/climatologies/WOA09_nc/monthly/t0112.nc temperature_oa_mean tos NODC-WOA09 1772 2008
make_obs_clim.py /work/durack1/Shared/obs_data/Argo/UCSD_monthly/130606_RG_ArgoClim_33pfit_2013_annual.nc ARGO_TEMPERATURE_ANNUAL_ANOMALY tos UCSD-ARGO 2004 2012
make_obs_clim.py /work/durack1/Shared/obs_data/temperature/HadCRUT3/130122_HadISST_sst.nc sst tos UKMETOFFICE-HadISST-v1.1
make_obs_clim.py /work/durack1/Shared/obs_data/temperature/NOAA_OISSTv2/130528_sst.mnmean.nc sst tos NOAA-OISST-v2 1982 2012
make_obs_clim.py /work/durack1/Shared/obs_data/temperature/REMSS_AMSRE/tos_AMSRE_L3_v7_200206-201012.nc tos tos REMSS-AMSRE-L3-v7 2003 2010
make_obs_clim.py /work/durack1/Shared/obs_data/CNES_AVISO/zos_AVISO_L4_199210-201012.nc zos zos CNES-AVISO-L4 1993 2010