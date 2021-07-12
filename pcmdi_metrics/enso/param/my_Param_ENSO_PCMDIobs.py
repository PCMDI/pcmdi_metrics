import datetime
import glob
import os


def find_latest(path):
    dir_list = [p for p in glob.glob(path+"/v????????")]
    return sorted(dir_list)[-1]


# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip6'  # cmip5, cmip6
exp = 'historical'  # historical, piControl

# =================================================
# Miscellaneous
# -------------------------------------------------
debug = False
# debug = True
nc_out = True

# =================================================
# Observation
# -------------------------------------------------
reference_data_lf_path = {
    'GPCPv2.3': '/work/lee1043/DATA/GPCP/gpcp_25_lsmask.nc',
    'GPCP-2-3': '/work/lee1043/DATA/GPCP/gpcp_25_lsmask.nc'
}

obs_cmor = True
obs_cmor_path = "/p/user_pub/PCMDIobs/PCMDIobs2"
obs_catalogue = "/p/user_pub/PCMDIobs/catalogue/pcmdiobs_monthly_bySource_catalogue_v20210422.json"

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    find_latest('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'),
    '%(mip)/%(exp)/%(realm)/mon/%(variable)',
    '%(mip).%(exp).%(model).%(realization).mon.%(variable).xml')

modpath_lf = os.path.join(
    find_latest('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'),
    '%(mip)/historical/%(realm)/fx/%(variable)',
    '%(mip).historical.%(model).r0i0p0.fx.%(variable).xml')

modnames = ['IPSL-CM6A-LR']
realization = 'r1i1p1f1'

# modnames = ['all']
# realization = '*'

if debug:
    modnames = ['IPSL-CM6A-LR']
    realization = 'r1i1p1f1'  # r1i1p1 (cmip5), r1i1p1f1 (cmip6), * (all)

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
