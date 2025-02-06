def create_user_df(dir_path):
    # Create df from directory structure
    data = []
    model_pattern = r"^[^_]+_([^_]+)_.*\.png$" #regex pattern to extract model name between first and second underscores
    region_pattern = r"^(?:.*?_){5}(.*?)_.*\.png$" # regex pattern to extract region name, after the fifth underscore
    var_folders = [f.name for f in os.scandir(dir_path) if f.is_dir()]
    seasons = {
        "ANN": "_AC_",
        "DJF": "_DJF_",
        "JJA": "_JJA_",
        "MAM": "_MAM_",
        "SON": "_SON_"
    }
    regions = {
        "global": "_global_",
        "NHEX": "_NHEX_",
        "SHEX": "_SHEX_",
        "TROPICS": "_TROPICS_"
    }

    for var_folder in var_folders:
        var_folder_path = os.path.join(dir_path, var_folder)
        data_dict = {} #dictionary for images stored by model

        for file in os.scandir(var_folder_path):
            if file.is_file():
                model_match = re.match(model_pattern, file.name)
                region_match = re.match(region_pattern, file.name)
                if model_match:
                    model = model_match.group(1)
                if region_match:
                    region = region_match.group(1)

                    if model not in data_dict: #initialize model entry if it doesn't exist
                        data_dict[model] = {"Variable": var_folder, "Region": region, "ANN": None, "DJF": None, "JJA": None, "MAM": None, "SON": None,}
                    
                    for season_key, season in seasons.items():
                        for region_key, r in regions.items():
                            if season in file.name and r in file.name:
                                data_dict[model] = f"https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/amip/clim/v20241029/{var_folder}/{file.name}"
                                break #to stop checking other key strings for this file
        
        # Add model images to data
        for model, model_data in data_dict.items():
            data.append({
                "Model": model,
                "Variable": model_data["Variable"],
                "Region": model_data["Region"],
                "ANN": model_data["ANN"],
                "DJF": model_data["DJF"],
                "JJA": model_data["JJA"],
                "MAM": model_data["MAM"],
                "SON": model_data["SON"]
            })

    user_df = pd.DataFrame(data)
    return user_df