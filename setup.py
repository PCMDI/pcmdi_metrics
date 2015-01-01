from distutils.core import setup
import glob,subprocess

Version = "0.6.0"
p = subprocess.Popen(("git","describe","--tags"),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
  descr = p.stdout.readlines()[0].strip()
  Version = "-".join(descr.split("-")[:-2])
  if Version == "":
    Version = descr
except:
  Version = "0.9.pre-release"
  descr = Version

p = subprocess.Popen(("git","log","-n1","--pretty=short"),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
  commit = p.stdout.readlines()[0].split()[1]
except:
  commit = ""
f = open("src/python/version.py","w")
print >>f, "__version__ = '%s'" % Version
print >>f, "__git_tag_describe__ = '%s'" % descr
print >>f, "__git_sha1__ = '%s'" % commit
f.close()

portrait_files          = ["src/python/graphics/share/portraits.scr",]
cmip5_amip_json         = glob.glob("data/CMIP_metrics_results/CMIP5/amip/*.json")
cmip5_historical_json   = glob.glob("data/CMIP_metrics_results/CMIP5/historical/*.json")
cmip5_piControl_json    = glob.glob("data/CMIP_metrics_results/CMIP5/piControl/*.json")
demo_ACME_files         = glob.glob("src/python/pcmdi/scripts/ACME/*.py")
demo_GFDL_files         = glob.glob("src/python/pcmdi/scripts/GFDL/*.py")
demo_NCAR_files         = glob.glob("src/python/pcmdi/scripts/NCAR/*.py")
param_files             = glob.glob("doc/parameter_files/*.py")
test_data_files         = glob.glob("test/pcmdi/data/*.nc")
test_py_files           = glob.glob("test/pcmdi/*.py")

setup (name         = 'pcmdi_metrics',
       version      = descr,
       author       = 'PCMDI',
       description  = 'model metrics tools',
       url          = 'http://github.com/PCMDI/pcmdi_metrics',
       packages     = ['pcmdi_metrics','pcmdi_metrics.io','pcmdi_metrics.pcmdi','pcmdi_metrics.graphics'],  
       package_dir  = {'pcmdi_metrics': 'src/python',
                       'pcmdi_metrics.io': 'src/python/io',
                       'pcmdi_metrics.pcmdi': 'src/python/pcmdi',
                       'pcmdi_metrics.graphics': 'src/python/graphics',
                      },
       scripts      = ['src/python/pcmdi/scripts/pcmdi_metrics_driver.py'],
       data_files   = [('demo/ACME',demo_ACME_files),
                       ('demo/GFDL',demo_GFDL_files),
                       ('demo/NCAR',demo_NCAR_files),
                       ('doc/parameter_files',param_files),
                       ('doc',('doc/parameter_files/pcmdi_input_parameters_sample.py',)),
                       ('share/CMIP_metrics_results/CMIP5/amip',cmip5_amip_json),
                       ('share/CMIP_metrics_results/CMIP5/historical',cmip5_historical_json),
                       ('share/CMIP_metrics_results/CMIP5/piControl',cmip5_piControl_json),
                       ('share/graphics/vcs',portrait_files),
                       ('share/pcmdi',('doc/obs_info_dictionary.json',)),
                       ('test',('test/test_from_param.py','test/test_suite.py',)),
                       ('test/data',test_data_files),
                       ('test/pcmdi',test_py_files),
                       ('test/pcmdi/gensftlfTest',('test/pcmdi/gensftlfTest/tas_2.5x2.5_esmf_linear_metrics.json',)),
                       ('test/pcmdi/installationTest',('test/pcmdi/installationTest/tas_2.5x2.5_regrid2_linear_metrics.json','test/pcmdi/installationTest/tos_2.5x2.5_esmf_linear_metrics.json',)),
                       ('test/pcmdi/nosftlfTest',('test/pcmdi/nosftlfTest/tas_2.5x2.5_esmf_linear_metrics.json',)),
                       ('test/obs/atm/mo/tas/ERAINT/ac',('test/pcmdi/obs/atm/mo/tas/ERAINT/ac/tas_pcmdi-metrics_Amon_ERAINT_198901-200911-clim.nc',)),
                       ('test/obs/fx/sftlf/ERAINT',('test/pcmdi/obs/fx/sftlf/ERAINT/sftlf_pcmdi-metrics_fx_ECMWF-ERAInterim_197901-201407.nc',)),
                       ('test/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/ac',('test/pcmdi/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/ac/tos_pcmdi-metrics_Omon_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc',)),
                       ('test/pcmdi/unitsTest',('test/pcmdi/unitsTest/tas_2.5x2.5_esmf_linear_metrics.json',)),
                      ]
       #include_dirs = [numpy.lib.utils.get_include()],
       #ext_modules = [
       #              Extension('pcmdi_metrics.exts',
       #              ['src/C/add.c',],
       #              library_dirs = [],
       #              libraries = [],
       #              define_macros = [],
       #              extra_compile_args = [],
       #              extra_link_args = [],
       #              ]
      )
