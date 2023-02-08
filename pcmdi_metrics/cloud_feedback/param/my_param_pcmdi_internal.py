# User Input:
# ================================================================================================
model = "GFDL-CM4"
institution = "NOAA-GFDL"
variant = "r1i1p1f1"
grid_label = "gr1"
version = "v20180701"
path = "/p/css03/esgf_publish/CMIP6"

# Flag to compute ECS
# True: compute ECS using abrupt-4xCO2 run
# False: do not compute, instead rely on ECS value present in the json file (if it exists)
get_ecs = True
data_pathh = "/home/lee1043/git/pcmdi_metrics_20221013/pcmdi_metrics/pcmdi_metrics/cloud_feedback/data"

# Output directory path (directory will be generated if it does not exist yet.)
xml_path = "/work/lee1043/cdat/pmp/cloud_feedback/xmls/"
figure_path = "/work/lee1043/cdat/pmp/cloud_feedback/figures/"
output_path = "/work/lee1043/cdat/pmp/cloud_feedback/output"
output_json_filename = "_".join(["cloud_feedback", model, variant]) + ".json"
# ================================================================================================
