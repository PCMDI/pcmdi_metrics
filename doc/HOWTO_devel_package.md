# Adding a Python Devel Package

* in order to build the devel packages you need to pass: `--enable-devel` to the `setup.py` command e.g. `python setup.py install --enable-devel`

* create a directory in `src/python/devel` named `YOUR_PACKAGE` (replace with appropriate package name)

* In the above directory create 3 subdirectories:
 * `lib` where your python packge file will sit
 * `scripts` where your scripts will be
 * `data` where files you want to package will be

* you can access your package by import pcmdi_metrics.YOUR_PACKAGE

# `lib` directory

create a `__init__.py` file from which you expose functions you want to access directly from `pcmdi_metrics.YOUR_PACKAGE`
example:
`file1.py` in the directory contains a function `foo` rather than access it via `pcmdi_metrics.YOUR_PACKAGE.file1.foo` you can add the follwoing line in your `__init__.py`
`from file1 import foo`
now you can access `foo` via:
`pcmdi_metrics.YOUR_PACKAGE.foo`

# `scripts` directory
any scripts to be called by user should go in here

# `data` directory

create as many subdirectories in here as you need to files in the subdirectories will be mapped to your package distribution as follow (example `share` directory

files in data/share will be mapped to distrib/share/YOUR_PACKAGE

