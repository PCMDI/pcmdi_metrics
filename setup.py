from distutils.core import setup, Extension
import os,sys
import numpy
try:
    sys.path.append(os.environ['BUILD_DIR'])
    import cdat_info
    Version=cdat_info.Version
except:
    Version="???"
setup (name = "metrics",
       version=Version,
       author='PCMDI',
       description = "General utilities for model metrics computing",
       url = "http://uvcdat.llnl.gov",
       packages = ['metrics','metrics.io',],
       package_dir = {'metrics': 'src/python',
                      'metrics.io': 'src/python/io'},
       scripts = [],
       include_dirs = [numpy.lib.utils.get_include()],
              ext_modules = [
           Extension('metrics.exts',
                     ['src/C/add.c',],
                     library_dirs = [],
                     libraries = [],
                     define_macros = [],
                     extra_compile_args = [],
                     extra_link_args = [],
                     ),
           ]
      )

