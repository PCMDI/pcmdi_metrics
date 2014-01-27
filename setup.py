from distutils.core import setup, Extension
import os,sys
import numpy
Version="0.1.0"
setup (name = "metrics",
       version=Version,
       author='PCMDI',
       description = "model metrics tools",
       url = "http://uvcdat.llnl.gov",
       packages = ['metrics','metrics.io','metrics.wgne'],
       package_dir = {'metrics': 'src/python',
                      'metrics.io': 'src/python/io',
                      'metrics.wgne': 'src/python/wgne'},
       scripts = ["src/python/wgne/scripts/wgne_metrics_driver.py",
                  "src/python/wgne/scripts/build_obs_meta_dictionary.py"],
       data_files = [('shared/wgne',('doc/obs_info_dictionary.json',))],
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

