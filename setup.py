from distutils.core import setup
Version="0.5.0"
import glob,subprocess

p = subprocess.Popen(("git","log","-n1","--pretty=short"),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
  commit = p.stdout.readlines()[0].split()[1]
except:
  commit = ""
f = open("src/python/version.py","w")
print >>f, "__version__ = '%s'" % Version
print >>f, "__git_sha1__ = '%s'" % commit
f.close()

portrait_files = ["src/python/graphics/share/portraits.scr",]

cmip5_amip_json         = glob.glob("data/CMIP_metrics_results/CMIP5/amip/*.json")
cmip5_historical_json   = glob.glob("data/CMIP_metrics_results/CMIP5/historical/*.json")

setup (name         = "pcmdi_metrics",
       version      = Version,
       author       = "PCMDI",
       description  = "model metrics tools",
       url          = "http://github.com/PCMDI/pcmdi_metrics",
       packages     = ['pcmdi_metrics','pcmdi_metrics.io','pcmdi_metrics.pcmdi','pcmdi_metrics.graphics'],  
       package_dir  = {'pcmdi_metrics': 'src/python',
                       'pcmdi_metrics.io': 'src/python/io',
                       'pcmdi_metrics.pcmdi': 'src/python/pcmdi',
                       'pcmdi_metrics.graphics': 'src/python/graphics',
                       },
       scripts      = ["src/python/pcmdi/scripts/pcmdi_metrics_driver.py"],
       data_files   = [('share/pcmdi',('doc/obs_info_dictionary.json',)),
                       ('share/CMIP_results/CMIP5/amip',cmip5_amip_json),
                         ('share/CMIP_results/CMIP5/historical',cmip5_historical_json),
                         ('share/graphics/vcs',portrait_files),
                         ('doc',('doc/parameter_files/pcmdi_input_parameters_sample.py',)),
                         ('test/graphics',("test/graphics/test_portrait.py",)),
                         ('test/pcmdi',('test/pcmdi/basic_test_parameters_file.py','test/pcmdi/tos_GFDL-ESM2G_Omon_historical_r1i1p1_198501-200512-clim.nc','test/pcmdi/sftlf_GFDL-ESM2G.nc','test/pcmdi/tos_2.5x2.5_esmf_linear_metrics.json')),
                         ('test/pcmdi/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/ac',('test/pcmdi/tos_pcmdi-metrics_Omon_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc',)),
                         ('test/pcmdi/obs/fx/mo/sftlf/UKMETOFFICE-HadISST-v1-1/ac',('test/pcmdi/sftlf_pcmdi-metrics_fx_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc',)),
                       ]
       #include_dirs = [numpy.lib.utils.get_include()],
       #       ext_modules = [
       #    Extension('pcmdi_metrics.exts',
       #              ['src/C/add.c',],
       #              library_dirs = [],
       #              libraries = [],
       #              define_macros = [],
       #              extra_compile_args = [],
       #              extra_link_args = [],
       #              ),
       #    ]
      )

