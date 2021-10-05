import glob

def generate_parameter_files(demo_data_directory, demo_output_directory, filenames=[]):
    # This prepares the various parameter files used in the demo notebooks 
    # to reflect where you downloaded the data
    sub_dict = {
        "INPUT_DIR": demo_data_directory,
        "OUTPUT_DIR": demo_output_directory
    }
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
    download the sample data, and generate the parameter files."""
    import requests
    import cdat_info

    r = requests.get("https://pcmdiweb.llnl.gov/pss/pmpdata/pmp_tutorial_files.txt")
    with open("data_files.txt","wb") as f:
        f.write(r.content)
    
    demo_data_directory = "demo_data"
    demo_output_directory = "demo_output"
    cdat_info.download_sample_data_files("data_files.txt", demo_data_directory)
    generate_parameter_files(demo_data_directory, demo_output_directory)