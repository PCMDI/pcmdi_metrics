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

