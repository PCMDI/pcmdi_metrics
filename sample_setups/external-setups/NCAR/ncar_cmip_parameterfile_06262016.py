################################################################################
#  SAMPLE INPUT PARAMETER FILE FOR THE PCMDI METRICS PACKAGE (PMP V1.1)
#

import os

### USER SETTING #########################################
#  CHANGE SETTING OF domain BY COMMENTING OUT UNWANTED OPTIONS

domain = None
# domain = "land"
# domain = "ocean"

##########################################################

## FIRST USE OF A PYTHON LIST, IN THIS CASE IT HAS ONLY ONE ENTRY
test_data_set = [
    "30L_cam5301_FAMIP.002",
    "30L_cam5301_FAMIP.003",
]  # THIS IS A MANDETORY ENTRY FOR DOCUMENTING RESULTS

test_data_set = [
    "eul128x256_d67iamip.ES01",
    "f40.1979_amip.track1.1deg.001",
    "30L_cam5301_FAMIP.002",
    "30L_cam5301_FAMIP.003",
    "f40.1979_amip.track1.T31.001",
    "30L_cam5301_B03F2_taper2_D05_FAMIP",
    "60Lcam5301_B11F2_FAMIP",
    "f.e10.FAMIPC3.f09_f09.001",
    "46L_cam5301_B03F2_taper2_D05_FAMIP",
]

test_data_set = os.listdir("~/processed_data/ncar_clims-picontrol_processed/")

model_versios = [
    "b.e15.B1850.f09_g16.pi_control.36",
    "b.e15.B1850.f09_g16.pi_control.41",
    "b.e15.B1850.f09_g16.pi_control.all.58",
    "b.e15.B1850.f09_g16.pi_control.all.66",
    "b.e15.B1850.f09_g16.pi_control.all.79",
    "b.e15.B1850G.f09_g16.pi_control.01",
    "b.e15.B1850G.f09_g16.pi_control.15",
    "b.e15.B1850G.f09_g16.pi_control.15b",
    "b.e15.B1850G.f09_g16.pi_control.28",
]

###############################################################################
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
## ROOT PATH FOR MODELS CLIMATOLOGIES
# test_data_path = '/work/metricspackage/mod_clims/cmip5-amip'
test_data_path = (
    "/work/gleckler1/processed_data/ncar_clims-picontrol_processed/%(model_version)/"
)

filename_template = "30L_cam5301_FAMIP.002.xml"
filename_template = "%(variable).nc"
##filename_template = "%(variable)_%(model_version)_Amon_picontrol_%(exp)r1i1p1_01-12-clim.nc"

## ROOT PATH FOR OBSERVATIONS
reference_data_path = "/work/gleckler1/processed_data/obs/"

## DIRECTORY WHERE TO SAVE RESULTS
case_id = "simple-test1"
metrics_output_path = "./pmp-test-control/"  # USER CHOOSES, RESULTS STORED IN  metrics_output_path + case_id
###############################################################################

ncar_cmip_direct_name_map = {
    "psl": "PSL",
    "tas": "TREFHT",
    "huss": "QREFHT",
    "ua": "U",
    "va": "V",
    "ta": "T",
    "pr": "PRECC",
    "rlut": "FLUT",
    "rsut": "SOLIN",
    "rlutcs": "FLUTC",
    "rsdtcs": "SOLIN",
    "rsds": "FSDS",
    "rlds": "FLDS",
    "prw": "TMQ",
    "zg": "Z3",
    "tauu": "TAUX",
    "tauv": "TAUY",
}

## REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
regions = {
    "tas": [None, "land", "ocean"],
    "uas": [None, "land", "ocean"],
    "vas": [None, "land", "ocean"],
    "pr": [None, "land", "ocean"],
    "psl": [
        None,
        "land",
        "ocean",
    ],
    "huss": [None, "land", "ocean"],
    "prw": [None, "land", "ocean"],
}  # terre

# OBSERVATIONS TO USE: CHOICES INCLUDE 'default','alternate1','alternate2',... AND ARE VARIABLE DEPENDENT
reference_data_set = ["default"]  # ,'alternate1','alternate2']

## A PYTHON LIST OF VARIABLES TO COMPUTE STATISTICS
vars = [
    "pr",
    "tas",
    "rlut",
    "prw",
    "ua_850",
    "ua_200",
    "va_850",
    "va_200",
    "ta_200",
    "ta_850",
    "zg_500",
]  # THIS EXAMPLE ONLY INCLUDES ONE FIELD, PRECIPICATION
# vars = ['psl']


# INTERPOLATION OPTIONS
target_grid = "2.5x2.5"  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = "esmf"  #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method = "linear"  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS (required in PMP v1.1)
period = "1979-1989"  # PERIOD OF CLIMATOLOGY
realization = "r1i1p1"  # REALIZATION

### SAME AS DEMO1 ABOVE
########################################
### BELOW IS DEMO2

## REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
regions = {
    "tas": [None, "land", "ocean"],
    "psl": [None, "land", "ocean"],
    "pr": [domain],
}

generate_sftlf = True  # IF MODEL LAND SEA MASK NOT AVAILABLE AUTOMATICALLY (APPROXIMATE!) GENERATE IN AT TARGET RESoLUTION
save_test_clims = (
    True  # True - output interpolated model climatology  False - don't output
)

test_clims_interpolated_output = "./interpolated-output/"
ext = ".nc"

if domain == "land":
    filename_output_template = (
        "%(variable)_%(model_version)_%_historical_"
        + "%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim-land%(ext)"
    )

if domain == "ocean":
    filename_output_template = (
        "%(variable)_%(model_version)_%_historical_"
        + "%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim-ocean%(ext)"
    )
    filename_output_template = variable + "_crap.nc"

if domain == None:
    filename_output_template = (
        "%(variable)_%(model_version)_%_historical_"
        + "%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim%(ext)"
    )
