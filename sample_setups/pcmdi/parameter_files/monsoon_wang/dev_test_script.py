import xcdat as xc
from regions_test import region_subset

from pcmdi_metrics.monsoon_wang.lib import regrid

regions_specs = {
    "NAFM": {"domain": {"latitude": (0.0, 45.0), "longitude": (-50, 60.0)}}
}
fm = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip5/historical/v20230323/pr/cmip5.historical.CanCM4.r1i1p1.mon.pr.198101-200512.AC.v20230323.nc"
fo = "/p/user_pub/climate_work/lee1043/DATA/GPCP_monthly/processed/GPCP.mon.pr.198101-200412.AC.v20250109.nc"
dsm = xc.open_dataset(fm)
dso = xc.open_dataset(fo)
dam = dsm.pr
dao = dso.pr
da = regrid(dao, dam)
da = regrid(dao, dam)


fim = "mpi_obs.nc"
dsim = xc.open_dataset(fim)
daim = dsim.pr

daim = daim.drop_vars("time")

da_reg = region_subset(daim, region="NAFM", regions_specs=regions_specs)
