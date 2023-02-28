# User Input:
# ================================================================================================
model = "GFDL-CM4"
variant = "r1i1p1f1"

input_files_json = "./param/input_files.json"

# Flag to compute ECS
# True: compute ECS using abrupt-4xCO2 run
# False: do not compute, instead rely on ECS value present in the json file (if it exists)
# get_ecs = True
get_ecs = False

# Output directory path (directory will be generated if it does not exist yet.)
xml_path = "./xmls/"
figure_path = "./figures/"
output_path = "./output"
output_json_filename = "_".join(["cloud_feedback", model, variant]) + ".json"
# ================================================================================================
