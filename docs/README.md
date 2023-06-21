readthedocs
-----------
This branch hosts the online documentation for the PCMDI Metrics packages. Provided here are instructions for updating the documentation.

Checking out and making changes to the docs branch:
---------------------------------------------------

You must be in a conda environment with "sphinx", "sphinx_rtd_theme", and other sphinx-related libraries listed in `conda-env/readthedocs.yml` installed. Otherwise, create your env following below
```
cd pcmdi_metrics
conda env create -n <new environment name> -f conda-env/readthedocs.yml
conda activate <new environment name>
```
Once your environment is ready
```
git pull origin main (optional, grab latest updates)
git checkout -b <new branch name>
cd docs
```
The source files are found in pcmdi_metrics/docs/. There is an index.rst file that is the landing page. If you create a new page, make sure to list it under the toctree in index.rst.

Building for local preview
--------------------------
```
cd pcmdi_metrics/docs
make clean
make html
```
The `make clean` command is optional and deletes the existing docs/build folder, which is populated by `make html`.
To view your changes locally, open pcmdi_metrics/docs/build/html/index.html with a browser. If it does not build as expected, first try running `make clean` before building again.

Build for readthedocs
---------------------
After building, you then have to "git add" all the files you updated.

For example:
```
git add *rst _static/*
git commit -m "your message"
```
Then you can push your changes.

Pushing your changes to your fork to preview:
---------------------------------------------
In pcmdi_metrics, set up your fork as a remote:
```
git remote add <remote name> <https://github.com/your_fork_path>
git remote -v
```
Checkout and push your changes:
```
git checkout <branch with changes>
git push <remote name> <branch with changes>
```
Then go to your forked repo on github.com and create a Pull Request to the `main` branch. Once merged, readthedocs webhook will automatically generate the web pages.
