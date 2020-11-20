gh-pages
--------
This branch hosts the online documentation for the PCMDI Metrics packages. Provided here are instructions for updating the documentation.

Checking out and making changes to the docs branch:
---------------------------------------------------

You must be in a conda environment with "sphinx" and "sphinx_rtd_theme" installed
```
git checkout -b gh-pages
git pull origin gh-pages (optional, grab latest updates)
git checkout -b <new branch name>
cd docs
```
The source files are found in pcmdi_metrics/docs/source. There is an index.rst file that is the landing page. If you create a new page, make sure to list it under the toctree in index.rst.

Building for local preview
--------------------------
```
cd pcmdi_metrics/docs
make clean
make html
```
The `make clean` command is optional and deletes the existing docs/build folder, which is populated by `make html`.
To view your changes locally, open pcmdi_metrics/docs/build/html/index.html with a browser. If it does not build as expected, first try running `make clean` before building again.

Build for github
----------------
The main difference here is that the web files have to be copied to /docs. There is a command that does builds and copies in one step:
```
cd pcmdi_metrics/docs
make github
```
Alternatively, these are the manual steps to build for github:
```
cd pcmdi_metrics/docs
make clean
make html
cp -r build/html/* . 
```
After building, you then have to "git add" all the files you copied from build/html and commit before pushing. This includes \*html, \*inv, and \*js files, along with the \_sources and \_static folders (which are currently listed in .gitignore, so you have to make sure to add them)
For example:
```
git add source/*rst *html *inv *js _static _sources
git commit -m "your message"
```
Then you can push your changes

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
Then go to your forked repo on github.com. Go to Settings -> GitHub Pages -> Source. Under source, select the name of the branch you just pushed. Choose /docs as the folder. This will generate a link to your github pages site.

You can also open a pull request from your fork repo, if desired.
