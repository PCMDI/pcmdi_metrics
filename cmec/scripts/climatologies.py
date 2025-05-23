import os
import subprocess
import sys

from pcmdi_metrics.utils import StringConstructor


def make_climatologies(settings, model_dir, wk_dir):
    filename_template = settings["filename_template"]
    modellist = settings["test_data_set"]
    varlist = settings["vars"]
    realization = settings.get("realization", "")
    period = settings.get("period", "")
    tmp = os.path.join(model_dir, filename_template)
    model_file = StringConstructor(tmp)
    model_file.period = period
    model_file.realization = realization
    out_base = os.path.join(wk_dir, "AC")
    os.mkdir(out_base)

    for model in modellist:
        for var in varlist:
            model_file.model_version = model
            model_file.variable = var
            cmd = [
                "pcmdi_compute_climatologies.py",
                "--infile",
                model_file(),
                "--outpath",
                out_base,
                "--var",
                var,
            ]
            suffix = "pcmdi_compute_climatologies_{0}_{1}.log".format(model, var)
            outfilename = os.path.join(out_base, suffix)
            with open(outfilename, "w") as outfile:
                subprocess.run(cmd, env=os.environ.copy(), stdout=outfile, check=True)

    # Get the date strings from the climo files for the filename template
    settings["test_data_path"] = out_base
    filelist = os.listdir(out_base)
    ext = os.path.basename(filename_template)[-3:]
    trim = -30  # default for '.nc'
    if ext == "xml":
        trim = -29
    try:
        for file in filelist:
            if ".AC." in file:
                suffix = file[trim:]
                break
        settings["filename_template"] = (
            os.path.basename(filename_template)[:-3] + suffix
        )
        print("Success in generating climatologies\n")
    except TypeError:
        print("Error: Could not find climatologies.")
        sys.exit(1)

    # Link sftlf file in AC folder if exists,
    # since it is the new model folder.
    if settings.get("generate_sftlf", False) is False:
        sftlf = settings.get("sftlf_filename_template", "sftlf_%(model_version).nc")
        for model in modellist:
            s = sftlf.replace("%(model_version)", model)
            sftlf_src = os.path.join(model_dir, s)
            sftlf_dst = os.path.join(out_base, s)
            if os.path.exists(sftlf_src):
                # Make any subdirectories from sftlf template
                os.makedirs(os.path.dirname(sftlf_dst), exist_ok=True)
                os.symlink(sftlf_src, sftlf_dst)

    return settings
