import subprocess
import os
import argparse

# Convert string input to boolean
def str_to_bool(value):
    if value.lower() in ('true', 'yes', '1'):
        return True
    elif value.lower() in ('false', 'no', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected. Use True/False, Yes/No, or 1/0.")

parser = argparse.ArgumentParser(description = 'Create the mean climate results page from a directory path')
parser.add_argument('--dir_path', type=str, required=True, help='Path to directory where images are saved.')
parser.add_argument('--compare_cmip6', type=str_to_bool, required=True, help='Boolean flag, accepts True/False, Yes/No, or 1/0.')
args = parser.parse_args()

command = ["python", "./mean_clim_results.py", "--dir_path", args.dir_path]
if args.compare_cmip6:
    command.append("--compare_cmip6=True")

subprocess.run(command)

home_content = """
<!DOCTYPE html>
<html>
<head>
    <title>PMP Output Viewer PROTOTYPE</title>
</head>
<body>
    <h1>Welcome to the POV PROTOTYPE page</h1>
    <p>Goal: Generate a PMP output viewer that offers a HTML page showing PMP output image files in an organized way.<p>
    <br><br><br>
    <h3>Mean Climate:</h3>
    <a href="./mean_clim_results.html" target="_blank">Dive Down Plots</a><br>
    <a href="./mean_clim_results.html" target="_blank">Portrait Plots</a><br>
    <a href="./mean_clim_results.html" target="_blank">Parallel Coordinate Plots</a><br>
    <h3>Modes of Variability:</h3>
    <p>Dive Down Plots</p>
</body>
</html>
"""

with open("pmp_output_viewer.html", "w") as pov_file:
    pov_file.write(home_content)

cwd = os.getcwd()
print(f"POV created in: {cwd}")