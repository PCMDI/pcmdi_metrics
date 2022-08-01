import glob


def generate_parameter_files(demo_data_directory, demo_output_directory, filenames=[]):
    # This prepares the various parameter files used in the demo notebooks
    # to reflect where you downloaded the data
    sub_dict = {"INPUT_DIR": demo_data_directory, "OUTPUT_DIR": demo_output_directory}
    if len(filenames) < 1:
        filenames = glob.glob("*.in")
    for name in filenames:
        with open(name) as template_file:
            print("Preparing parameter file: {}".format(name[:-3]))
            template = template_file.read()
            for key in sub_dict:
                template = template.replace("${}$".format(key), sub_dict[key])
            with open(name[:-3], "w") as param_file:
                param_file.write(template)

    print("Saving User Choices")
    with open("user_choices.py", "w") as f:
        print("demo_data_directory = '{}'".format(demo_data_directory), file=f)
        print("demo_output_directory = '{}'".format(demo_output_directory), file=f)


if __name__ == "__main__":
    """Perform the same actions as Demo 0 notebook: Get the tutorial file list,
    download the sample data, and generate the parameter files.

    Arguments:
        demo_data_directory (str): save sample data to this local directory.
        demo_output_directory (str): used in generating parameter files.
            If demo_output_directory is not provided, parameter files are skipped.
    """
    import os
    import sys

    import cdat_info
    import requests

    # Get directories from user input
    demo_data_directory = sys.argv[1]
    if len(sys.argv) > 2:
        demo_output_directory = sys.argv[2]
    else:
        demo_output_directory = None

    if not os.path.exists(demo_data_directory):
        os.mkdir(demo_data_directory)

    #  Get the list of files, with md5 sums, and write to local file.
    r = requests.get("https://pcmdiweb.llnl.gov/pss/pmpdata/pmp_tutorial_files.v20220420.txt")
    data_files_txt = os.path.join(demo_data_directory, "data_files.txt")
    with open(data_files_txt, "wb") as f:
        f.write(r.content)

    # Use the file list we just saved as input to cdat_info, which downloads any files
    # that are not already present in demo_data_directory.
    try:
        cdat_info.download_sample_data_files(data_files_txt, demo_data_directory)
    except RuntimeError:
        print("Download failed")
        sys.exit(1)

    # Only generate parameter files if demo_output_directory is provided.
    if demo_output_directory is not None:
        generate_parameter_files(demo_data_directory, demo_output_directory)
