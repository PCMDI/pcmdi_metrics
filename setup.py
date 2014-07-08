from distutils.core import setup, Extension
import os,sys
import numpy
Version="0.1.0"
import subprocess
p = subprocess.Popen(("git","log","-n1","--pretty=short"),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
  commit = p.stdout.readlines()[0].split()[1]
except:
  commit = ""
f=open("src/python/version.py","w")
print >>f, "__version__ = '%s'" % Version
print >>f, "__git_sha1__ = '%s'" % commit
f.close()

setup (name = "metrics",
       version=Version,
       author='PCMDI',
       description = "model metrics tools",
       url = "http://github.com/PCMDI/wgne-wgcm_metrics",
       packages = ['metrics','metrics.io','metrics.wgne'],
       package_dir = {'metrics': 'src/python',
                      'metrics.io': 'src/python/io',
                      'metrics.wgne': 'src/python/wgne'},
       scripts = ["src/python/wgne/scripts/wgne_metrics_driver.py",
                  "src/python/wgne/scripts/build_obs_meta_dictionary.py"],
       data_files = [('share/wgne',('doc/obs_info_dictionary.json',)),
                     ('doc',('doc/wgne_input_parameters_sample.py',)),
                     ('test/wgne',('test/wgne/basic_test_parameters_file.py','test/wgne/tos_GFDL-ESM2G_Omon_historical_r1i1p1_198501-200512-clim.nc','test/wgne/sftlf_GFDL-ESM2G_fx_historical_r0i0p0_198501-200512-clim.nc','test/wgne/tos_2.5x2.5_esmf_linear_metrics.json.good')),
                     ('test/wgne/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/ac',('test/wgne/tos_pcmdi-metrics_Omon_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc',)),
                     ('test/wgne/obs/fx/mo/sftlf/UKMETOFFICE-HadISST-v1-1/ac',('test/wgne/sftlf_pcmdi-metrics_fx_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc',)),
                     ]
       #include_dirs = [numpy.lib.utils.get_include()],
       #       ext_modules = [
       #    Extension('metrics.exts',
       #              ['src/C/add.c',],
       #              library_dirs = [],
       #              libraries = [],
       #              define_macros = [],
       #              extra_compile_args = [],
       #              extra_link_args = [],
       #              ),
       #    ]
      )

