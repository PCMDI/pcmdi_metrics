import glob
import os
from string import Template

# Before running for the first time, create the following subdirectories:
# pr/, tasmax/, and tasmin/
# Edit model name in L11 and run script to generate job submission scripts for that model.
# Uncomment the os.system() calls to submit jobs.
# To change the job script contents, edit the template files in this directory
# (pr_template.txt, tasmax_template.txt, and tasmin_template.txt)
model = "TaiESM1"
dpath = "/global/cfs/projectdirs/m3522/cmip6/LOCA2/{0}/0p0625deg/".format(model)
reals = glob.glob(os.path.join(dpath, "*"))

for rpath in reals:
    realization = os.path.basename(rpath)
    params = {
        "mymodel": '"{0}"'.format(model),
        "myreal": '"{0}"'.format(realization),
        "NR": "{0}".format(realization.split("i")[0].replace("r", "")),
        "modabbr": model[0:3],
        "msyear": 1985,
    }

    # PR
    with open(
        "/global/homes/a/aordonez/pmp_param/drcdm/LOCA2/pr_template.txt", "r"
    ) as f:
        tmpl = Template(f.read())
    pf = tmpl.substitute(params)
    outpath = "/global/homes/a/aordonez/pmp_param/drcdm/LOCA2/pr/run_LOCA2_pr_{0}_{1}.sh".format(
        model, realization
    )
    with open(outpath, "w") as fout:
        fout.write(pf)
    # os.system("sbatch {0}".format(outpath)) #uncomment to submit job

    # TASMIN
    with open(
        "/global/homes/a/aordonez/pmp_param/drcdm/LOCA2/tasmin_template.txt", "r"
    ) as f:
        tmpl = Template(f.read())
    pf = tmpl.substitute(params)
    outpath = "/global/homes/a/aordonez/pmp_param/drcdm/LOCA2/tasmin/run_LOCA2_tasmin_{0}_{1}.sh".format(
        model, realization
    )
    with open(outpath, "w") as fout:
        fout.write(pf)
    # os.system("sbatch {0}".format(outpath))

    # TASMAX
    with open(
        "/global/homes/a/aordonez/pmp_param/drcdm/LOCA2/tasmax_template.txt", "r"
    ) as f:
        tmpl = Template(f.read())
    pf = tmpl.substitute(params)
    outpath = "/global/homes/a/aordonez/pmp_param/drcdm/LOCA2/tasmax/run_LOCA2_tasmax_{0}_{1}.sh".format(
        model, realization
    )
    with open(outpath, "w") as fout:
        fout.write(pf)
    # os.system("sbatch {0}".format(outpath))
