"""if "test_data_set" not in settings:
    # See what model folders exist in model directory
    model_list = os.listdir(model_dir)
    test_data_set = []
    for model in model_list:
        fpath = os.path.join(model_dir,model)
        if os.path.isdir(fpath):
            test_data_set.append(model)
    # Derive filename template
    if "filename_template" not in settings:
        var_name = os.path.join(fpath,os.path.listdir(fpath)[0])
        test_name = os.listdir(var_name)[0]
    if "%(model)" not in filename_template:
        test_name.replace(model,"%(model)")
        filename_template = "%(model)/"+test_name

# TODO: also check aliases
if "vars" not in settings:
    # build variable list from directories in model directory
    varlist = os.listdir(model_dir)
    var = []
    for item in varlist:
        if item != "fx" and os.path.isdir(os.path.join(model_dir,item)):
            var.append(item)
    settings["vars"] = var
    if "filename_template" not in settings:
        for varname in var:
            if varname in filename_template:
                filename_template.replace(varname,"%(variable)")
"""