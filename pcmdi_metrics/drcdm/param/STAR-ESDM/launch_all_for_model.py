import glob
import os
from string import Template

# Before running for the first time, create the following subdirectories:
# pr/, tasmax/, and tasmin/
# Edit model name in L11 and run script to generate job submission scripts for that model.
# Uncomment the os.system() calls to submit jobs.
# To change the job script contents, edit the template files in this directory
# (pr_template.txt, tasmax_template.txt, and tasmin_template.txt)
model = "ACCESS-CM2"
dpath = "/global/cfs/projectdirs/m3522/project_downscale/CMIP6/NAM/TTU/STAR-ESDM-V1/{0}/CMIP/historical/".format(
    model
)
reals = glob.glob(os.path.join(dpath, "*"))

for rpath in reals:
    realization = os.path.basename(rpath)
    params = {
        "mymodel": '"{0}"'.format(model),
        "myreal": '"{0}"'.format(realization),
        "NR": "{0}".format(realization.split("i")[0].replace("r", "")),
        "modabbr": model[0:3],
    }

    # PR
    with open(
        "/global/homes/a/aordonez/pmp_param/drcdm/STAR-ESDM/pr_template.txt", "r"
    ) as f:
        tmpl = Template(f.read())
    pf = tmpl.substitute(params)
    outpath = "/global/homes/a/aordonez/pmp_param/drcdm/STAR-ESDM/pr/run_STAR-ESDM_pr_{0}_{1}.sh".format(
        model, realization
    )
    with open(outpath, "w") as fout:
        fout.write(pf)
    os.system("sbatch {0}".format(outpath))

    # TASMIN
    with open(
        "/global/homes/a/aordonez/pmp_param/drcdm/STAR-ESDM/tasmin_template.txt", "r"
    ) as f:
        tmpl = Template(f.read())
    pf = tmpl.substitute(params)
    outpath = "/global/homes/a/aordonez/pmp_param/drcdm/STAR-ESDM/tasmin/run_STAR-ESDM_tasmin_{0}_{1}.sh".format(
        model, realization
    )
    with open(outpath, "w") as fout:
        fout.write(pf)
    os.system("sbatch {0}".format(outpath))

    # TASMAX
    with open(
        "/global/homes/a/aordonez/pmp_param/drcdm/STAR-ESDM/tasmax_template.txt", "r"
    ) as f:
        tmpl = Template(f.read())
    pf = tmpl.substitute(params)
    outpath = "/global/homes/a/aordonez/pmp_param/drcdm/STAR-ESDM/tasmax/run_STAR-ESDM_tasmax_{0}_{1}.sh".format(
        model, realization
    )
    with open(outpath, "w") as fout:
        fout.write(pf)
    os.system("sbatch {0}".format(outpath))
