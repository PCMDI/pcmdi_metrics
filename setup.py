from distutils.core import setup
import glob
import subprocess
import os
import sys

if "--enable-devel" in sys.argv:
    install_dev = True
    sys.argv.remove("--enable-devel")
else:
    install_dev = False

Version = "0.6.0"
p = subprocess.Popen(
    ("git",
     "describe",
     "--tags"),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
try:
    descr = p.stdout.readlines()[0].strip()
    Version = "-".join(descr.split("-")[:-2])
    if Version == "":
        Version = descr
except:
    Version = "0.9.pre-release"
    descr = Version

p = subprocess.Popen(
    ("git",
     "log",
     "-n1",
     "--pretty=short"),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
try:
    commit = p.stdout.readlines()[0].split()[1]
except:
    commit = ""
f = open("src/python/version.py", "w")
print >>f, "__version__ = '%s'" % Version
print >>f, "__git_tag_describe__ = '%s'" % descr
print >>f, "__git_sha1__ = '%s'" % commit
f.close()

portrait_files = ["src/python/graphics/share/portraits.scr", ]
cmip5_amip_json = glob.glob("data/CMIP_metrics_results/CMIP5/amip/*.json")
cmip5_historical_json = glob.glob(
    "data/CMIP_metrics_results/CMIP5/historical/*.json")
cmip5_piControl_json = glob.glob(
    "data/CMIP_metrics_results/CMIP5/piControl/*.json")
demo_ACME_files = glob.glob("demo/ACME/*.py")
demo_CSIRO_files = glob.glob("demo/CSIRO/*.py")
demo_CSIRO_files += glob.glob("demo/CSIRO/*.png")
demo_CSIRO_files += glob.glob("demo/CSIRO/*.sh")
demo_GFDL_files = glob.glob("demo/GFDL/*.py")
demo_GFDL_files += glob.glob("demo/GFDL/*.png")
demo_NCAR_files = glob.glob("demo/NCAR/*.py")
param_files = glob.glob("doc/parameter_files/*.py")


packages={'pcmdi_metrics': 'src/python',
           'pcmdi_metrics.io': 'src/python/io',
           'pcmdi_metrics.pcmdi': 'src/python/pcmdi',
           'pcmdi_metrics.graphics': 'src/python/graphics',
           }
scripts=['src/python/pcmdi/scripts/pcmdi_metrics_driver.py',
       'src/python/pcmdi/scripts/pcmdi_compute_climatologies.py']

data_files=[('demo/ACME', demo_ACME_files),
          ('demo/CSIRO', demo_CSIRO_files),
          ('demo/GFDL', demo_GFDL_files),
          ('demo/NCAR', demo_NCAR_files),
          ('doc/parameter_files', param_files),
          ('doc',
           ('doc/parameter_files/pcmdi_input_parameters_sample.py',
            'doc/simple_json_test.py',
            )),
          ('share/CMIP_metrics_results/CMIP5/amip',
           cmip5_amip_json),
          ('share/CMIP_metrics_results/CMIP5/historical',
           cmip5_historical_json),
          ('share/CMIP_metrics_results/CMIP5/piControl',
           cmip5_piControl_json),
          ('share/graphics/vcs', portrait_files),
          ('share/pcmdi', ('doc/obs_info_dictionary.json','share/pcmdi_metrics_table')),
          ]

if install_dev:
    print "Adding experimental packages"
    dev_packages = glob.glob("src/python/devel/*")
    dev_packages.remove("src/python/devel/example_dev")
    for p in dev_packages:
        if not os.path.isdir(p):
            dev_packages.pop(p)
    dev_scripts = []
    for p in dev_packages:
        scripts = glob.glob(os.path.join(p,"scripts","*"))
        dev_scripts+=scripts
    dev_pkg = {}
    dev_data = []
    for p in dev_packages:
        nm = p.replace("/",".")
        nm = nm.replace("src.python.devel","pcmdi_metrics")
        pnm = nm.split(".")[-1]
        pkg_dir = os.path.join(p,"lib")
        dev_pkg[nm]=pkg_dir
        data = glob.glob(os.path.join(p,"data","*"))
        for d in data:
            dir_nm = os.path.split(d)[-1]
            dev_data.append([os.path.join(dir_nm,pnm),glob.glob(os.path.join(d,"*"))])
    packages.update(dev_pkg)
    data_files+=dev_data
    scripts+=dev_scripts

setup(name='pcmdi_metrics',
      version=descr,
      author='PCMDI',
      description='model metrics tools',
      url='http://github.com/PCMDI/pcmdi_metrics',
      packages=packages.keys(),
      package_dir=packages,
      scripts=scripts,
      data_files=data_files
      # include_dirs = [numpy.lib.utils.get_include()],
      #  ext_modules = [
      #               Extension('pcmdi_metrics.exts',
      #               ['src/C/add.c',],
      #               library_dirs = [],
      #               libraries = [],
      #               define_macros = [],
      #               extra_compile_args = [],
      #               extra_link_args = [],
      #               ]
      )
