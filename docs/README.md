Update Documentation website
----------------------------
This directory hosts the online documentation for the PCMDI Metrics packages. There are two options available, one via Github Pages (http://pcmdi.github.io/pcmdi_metrics/) and another via ReadtheDocs (https://pcmdi-metrics.readthedocs.io). Provided here are instructions for updating the documentation for either or both options.

Checking out and making changes
-------------------------------
You must be in a conda environment with "sphinx", "sphinx_rtd_theme", and other sphinx-related libraries listed in `conda-env/dev.yml` installed. Otherwise, create your env following below
```
cd pcmdi_metrics
conda env create -n <new environment name> -f conda-env/dev.yml
conda activate <new environment name>
```

Once your environment is ready
```
git pull origin main (optional, grab latest updates)
git checkout -b <new branch name>
cd docs
```

The source files are found in pcmdi_metrics/docs/. There is an index.rst file that is the landing page. If you create a new page, make sure to list it under the toctree in index.rst.

Building local preview
----------------------
Optional but strongly recommended step is building a local preview to examine the generated html files are looking okay. 
```
cd pcmdi_metrics/docs
make clean
make html
```
The `make clean` command is optional and deletes the existing docs/build folder, which is populated by `make html`.
To view your changes locally, open `pcmdi_metrics/docs/_build/html/index.html` with a browser. If it does not build as expected, first try running `make clean` before building again.

Prepare pushing your changes
----------------------------
After previewing and everything look okay, you are ready to push changes. You have to "git add" all the files you updated.

For example:
```
git add *rst _static/*
git commit -m "your message"
```
Then you can push your changes.

Push your changes to remote
---------------------------
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
Then go to your forked repo on github.com and create a Pull Request to the `main` branch. 

Build webpages
--------------
Once the changes are merged to the `main` branch of pcmdi_metrics, Github Action will automatically build and deploy web pages using Github Pages. This process will follow what is defined in `.github/workflows/documentation.yaml`. The page will be accessible at http://pcmdi.github.io/pcmdi_metrics/.

To deploy the web pages via readthedocs, you will need to go to readthedocs project page (https://readthedocs.org/projects/pcmdi-metrics/), go to "Builds" menu, and click "Build Version" button. The page will be accessible at https://pcmdi-metrics.readthedocs.io/en/latest/.

Resources
---------
* [Read the Docs tutorial](https://docs.readthedocs.io/en/stable/tutorial/index.html)
* [Deploying Sphinx documentation to GitHub Pages](https://coderefinery.github.io/documentation/gh_workflow/)

