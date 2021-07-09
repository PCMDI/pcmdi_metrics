import datetime
import glob
import os


def find_latest(path):
    dir_list = [p for p in glob.glob(path+"/v????????")]
    return sorted(dir_list)[-1]


# =================================================
# Background Information
# -------------------------------------------------
mip = 'obs2obs'  # cmip5, cmip6
exp = 'historical'  # historical, piControl

# =================================================
# Miscellaneous
# -------------------------------------------------
debug = False
nc_out = True

# =================================================
# Observation
# -------------------------------------------------
reference_data_path = {
    'ERA-Interim': '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/mon/VAR/ERA-INT/gn/v20200402/VAR_mon_ERA-INT_BE_gn_v20200402_197901-201903.nc',  # noqa
    'HadISST': '/work/lee1043/DATA/HadISSTv1.1/HadISSTv1.1.xml',
    'OISST': '/work/lee1043/DATA/OISST/xmls/OISST_tos_mo.xml',
    'Tropflux': '/work/lee1043/DATA/TropFlux/monthly/xmls/Tropflux_VAR_mo.xml',
    # 'Tropflux': '/p/user_pub/PCMDIobs/PCMDIobs2.0/atmos/mon/VAR/TropFlux-1-0/gn/v20190912/VAR_mon_TropFlux-1-0_BE_gn_197901-201707.nc', # noqa 
    # 'OAFlux': '/work/lee1043/DATA/OAFlux/xmls/OAFlux_VAR_mo.xml',
    'GPCPv2.3': '/p/user_pub/pmp/pmp_obs_preparation/orig/data/GPCP_v2.3_mon_jwl/precip.mon.mean.nc',
    # 'GPCPv2.3': '/p/user_pub/PCMDIobs/PCMDIobs2.0/atmos/mon/pr/GPCP-2-3/gn/v20200117/pr_mon_GPCP-2-3_BE_gn_197901-201907.nc',  # noqa
    # 'AVISO': '/p/user_pub/PCMDIobs/PCMDIobs2.1/ocean/mon/zos/AVISO-1-0/gn/v20190912/zos_mon_AVISO-1-0_BE_gn_199210-201012.nc',  # noqa
    'AVISO': '/work/lee1043/DATA/AVISO/sla_aviso_199301-201812.xml',
}

reference_data_lf_path = {
    'GPCPv2.3': '/work/lee1043/DATA/GPCP/gpcp_25_lsmask.nc'
}
# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    '/p/user_pub/PCMDIobs/PCMDIobs2/%(realm)/mon/%(variable)',
    '%(model)/gn/',
    'v????????',
    '%(variable)_mon_%(model)_BE_gn_v????????_??????-??????.nc')

modpath_lf = os.path.join(
    find_latest('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'),
    '%(mip)/historical/%(realm)/fx/%(variable)',
    '%(mip).historical.%(model).r0i0p0.fx.%(variable).xml')

modnames = ['20CR', 'ERA-20C', 'ERA-INT', 'TropFlux-1-0', 'CMAP-V1902', 'GPCP-2-3', 'TRMM-3B43v-7', 'ERA-5',
            'CERES-EBAF-4-0', 'CERES-EBAF-4-1', 'AVISO-1-0']

if debug:
    modnames = ['ERA-INT']

realization = 'r1i1p1f1'  # r1i1p1 (cmip5), r1i1p1f1 (cmip6), * (all)
# realization = '*'

# =================================================
# Metrics Collection
# -------------------------------------------------
metricsCollection = 'ENSO_perf'  # ENSO_perf, ENSO_tel, ENSO_proc

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmprdir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2'

if debug:
    pmprdir = '/work/lee1043/imsi/result_test'

results_dir = os.path.join(
    pmprdir,
    '%(output_type)', 'enso_metric',
    '%(mip)', '%(exp)', '%(case_id)', '%(metricsCollection)')

json_name = '%(mip)_%(exp)_%(metricsCollection)_%(case_id)_%(model)_%(realization)'
netcdf_name = json_name
