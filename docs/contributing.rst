.. highlight:: shell

==================
Contributing Guide
==================

Contributions are welcome and greatly appreciated! Every little bit helps, and credit will always be given.

Types of Contributions
----------------------

PCMDI Metrics Package (PMP) includes issue templates based on the contribution type: https://github.com/PCMDI/pcmdi_metrics/issues/new/choose.
Note, new contributions must be made under the BSD-3-Clause license.

Bug Report
~~~~~~~~~~

Look through the `GitHub Issues`_ for bugs to fix. Any unassigned issues tagged with "Type: Bug" is open for implementation.

Feature Request
~~~~~~~~~~~~~~~

Look through the `GitHub Issues`_ for feature suggestions. Any unassigned issues tagged with "Type: Enhancement" is open for implementation.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a open-source project, and that contributions are welcome :)

Documentation Update
~~~~~~~~~~~~~~~~~~~~

Help improve PMP's documentation, whether that be the Sphinx documentation or the API docstrings.

Community Discussion
~~~~~~~~~~~~~~~~~~~~

Take a look at the `GitHub Discussions`_ page to get involved, share ideas, or ask questions.

.. _cf_xarray: https://cf-xarray.readthedocs.io/en/latest/index.html
.. _CF convention: http://cfconventions.org/
.. _GitHub Issues: https://github.com/PCMDI/pcmdi_metrics/issues
.. _GitHub Discussions: https://github.com/PCMDI/pcmdi_metrics/discussions

New metrics subpackage
----------------------

Developers working on new metrics packages to contribute to the PMP are highly encouraged to explore the `PMP source code`_ and examine how existing metrics workflows are structured. In general each subpackage contains a driver script, additional library code needed to run the driver script, and example parameter files.

Steps to contributing a new subpackage:

1. Open a Feature Request describing the new subpackage.
2. Follow the instructions in **Get Started** and **Pull Request Guidelines** while working on code.
3. Add the new subpackage to the `GitHub.io documentation`_.

.. _GitHub.io documentation: https://github.com/PCMDI/pcmdi_metrics/tree/main/docs

Please keep in mind that:

* All metrics code must be in Python, and it is the responsibility of the developer to deliver Python code. The PMP team has limited bandwidth to assist with code conversion to Python.
* Current PMP dependencies can be found in `dev.yml file`_. Dependencies cannot be added without the approval of the PMP team.
* Input data sets are expected to follow the `CF Metadata Conventions`_.
* Providing `unit tests`_ is highly encouraged.

Quick links to useful code sections:

* See `pcmdi_metrics/io`_ and `pcmdi_metrics/utils`_ to find functions for tasks like land masking, grid subsetting, and more.
* Graphics code for post-processing metrics is found in `pcmdi_metrics/graphics`_

.. _PMP source code: https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics
.. _dev.yml file: https://github.com/PCMDI/pcmdi_metrics/blob/main/conda-env/dev.yml#L6
.. _CF Metadata Conventions: https://cfconventions.org/
.. _unit tests: https://github.com/PCMDI/pcmdi_metrics/tree/main/tests
.. _pcmdi_metrics/io: https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/io
.. _pcmdi_metrics/utils: https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/utils
.. _pcmdi_metrics/graphics: https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/graphics

Version Control
---------------

The repository uses branch-based (core team) and fork-based (external collaborators)
Git workflows with tagged software releases.

.. figure:: _static/git-flow.svg
   :alt: Git Flow Diagram

Guidelines
~~~~~~~~~~

1. ``main`` must always be deployable
2. All changes are made through support branches
3. Branch names should follow the pattern "issuenumber_initials_description"
4. Rebase with the latest ``main`` to avoid/resolve conflicts
5. Make sure pre-commit quality assurance checks pass when committing (enforced in CI/CD build)
6. Open a pull request early for discussion
7. Once the CI/CD build passes and pull request is approved, squash and rebase your commits
8. Merge pull request into ``main`` and delete the branch

Things to Avoid
~~~~~~~~~~~~~~~

1. Don't merge in broken or commented out code
2. Don't commit directly to ``main``

   *  There are branch-protection rules for ``main``

3. Don't merge with conflicts. Instead, handle conflicts upon rebasing

Source: https://gist.github.com/jbenet/ee6c9ac48068889b0912

Pre-commit
~~~~~~~~~~
The repository uses the pre-commit package to manage pre-commit hooks.
These hooks help with quality assurance standards by identifying simple issues
at the commit level before submitting code reviews.

.. figure:: _static/pre-commit-flow.svg
   :alt: Pre-commit Flow Diagram

   pre-commit Flow


Get Started
------------

Ready to contribute? Here's how to set up PMP for local development.

VS Code, the editor of choice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We recommend using VS Code as your IDE because it is open-source and has great Python development support.

Get VS Code here: https://code.visualstudio.com

VS Code Setup
^^^^^^^^^^^^^
PMP includes a VS Code workspace file (``.vscode/pcmdi_metrics.code-setting``). This file automatically configures your IDE with the quality assurance tools, code line-length rulers, and more.

Make sure to follow the :ref:`Local Development` section below.

Recommended VS Code Extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    * `Python <https://marketplace.visualstudio.com/items?itemName=ms-python.python>`_
    * `Pylance <https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance>`_
    * `Python Docstring Generator <https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring>`_
    * `Python Type Hint <https://marketplace.visualstudio.com/items?itemName=njqdev.vscode-python-typehint>`_
    * `Better Comments <https://marketplace.visualstudio.com/items?itemName=aaron-bond.better-comments>`_
    * `Jupyter <https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter>`_
    * `Visual Studio Intellicode <https://marketplace.visualstudio.com/items?itemName=VisualStudioExptTeam.vscodeintellicode>`_


.. _Local Development:

Local Development
~~~~~~~~~~~~~~~~~

1. Download and install Conda

    Linux
        ::

            $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
            $ bash ./Miniconda3-latest-Linux-x86_64.sh
            Do you wish the installer to initialize Miniconda3 by running conda init? [yes|no] yes


    MacOS
        ::

            $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
            $ bash ./Miniconda3-latest-MacOSX-x86_64.sh
            Do you wish the installer to initialize Miniconda3 by running conda init? [yes|no] yes

2. Fork the ``pcmdi_metrics`` repo on GitHub.

     - If you are a maintainer, you can clone and branch directly from the root repository here: https://github.com/PCMDI/pcmdi_metrics

3. Clone your fork locally::

    $ git clone git@github.com:your_name_here/pcmdi_metrics.git

4. <OPTIONAL> Open ``.vscode/pcmdi_metrics.code-settings`` in VS Code


5. Create and activate Conda development environment::

    $ cd pcmdi_metrics
    $ conda env create -f conda-env/dev.yml
    $ conda activate pcmdi_metrics_dev

6. <OPTIONAL> Set VS Code Python interpretor to ``pcmdi_metrics_dev``

7. Install pre-commit::

    $ pre-commit install
    pre-commit installed at .git/hooks/pre-commit

8. Create a branch for local development and make changes::

    $ git checkout -b <BRANCH-NAME>

9. `<OPTIONAL>` During or after making changes, check for formatting or linting issues using pre-commit::

    # Step 9 performs this automatically on staged files in a commit
    $ pre-commit run --all-files

    Trim Trailing Whitespace.................................................Passed
    Fix End of Files.........................................................Passed
    Check Yaml...............................................................Passed
    black....................................................................Passed
    isort....................................................................Passed
    flake8...................................................................Passed

10. Commit your changes::

     $ git add .
     $ git commit -m <Your detailed description of your changes>

     Trim Trailing Whitespace.................................................Passed
     Fix End of Files.........................................................Passed
     Check Yaml...............................................................Passed
     black....................................................................Passed
     isort....................................................................Passed
     flake8...................................................................Passed

11. Make sure pre-commit QA checks pass. Otherwise, fix any caught issues.

    - Most of the tools fix issues automatically so you just need to re-stage the files.
    - flake8 and mypy issues must be fixed automatically.

12. Push changes::

    $ git push origin <BRANCH-NAME>

13. Submit a pull request through the GitHub website.


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests for new or modified code.
2. Link issues to pull requests.
3. If the pull request adds functionality, the docs should be updated.
4. Squash and rebase commits for a clean and navigable Git history.

When you open a pull request on GitHub, there is a template available for use.


Style Guide
-----------

PMP integrates the Black code formatter for code styling. If you want to learn more, please read about it `here <https://black.readthedocs.io/en/stable/the_black_code_style.html>`__.

PMP also leverages `Python Type Annotations <https://docs.python.org/3.8/library/typing.html>`_ to help the project scale.
`mypy <https://mypy.readthedocs.io/en/stable/introduction.html>`_ performs optional static type checking through pre-commit.

Testing
-------

Testing your local changes are important to ensure long-term maintainability and extensibility of the project.
Since PMP is an open source library, we aim to avoid as many bugs as possible from reaching the end-user.

To get started, here are guides on how to write tests using pytest:

- https://docs.pytest.org/en/latest/
- https://docs.python-guide.org/writing/tests/#py-test

In most cases, if a function is hard to test, it is usually a symptom of being too complex (high cyclomatic-complexity).

DOs for Testing
~~~~~~~~~~~~~~~

*  *DO* write tests for new or refactored code
*  *DO* try to follow test-driven-development
*  *DO* use the Coverage reports to see lines of code that need to be tested
*  *DO* focus on simplistic, small, reusable modules for unit testing
*  *DO* cover as many edge cases as possible when testing

DON'Ts for Testing
~~~~~~~~~~~~~~~~~~

*  *DON'T* push or merge untested code
*  *DON'T* introduce tests that fail or produce warnings

Documenting Code
----------------

If you are using VS code, the `Python Docstring Generator <https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring>`_ extension can be used to auto-generate a docstring snippet once a function/class has been written.
If you want the extension to generate docstrings in Sphinx format, you must set the ``"autoDocstring.docstringFormat": "sphinx"`` setting, under File > Preferences > Settings.

Note that it is best to write the docstrings once you have fully defined the function/class, as then the extension will generate the full docstring.
If you make any changes to the code once a docstring is generated, you will have to manually go and update the affected docstrings.

More info on docstrings here: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html

DOs for Documenting Code
~~~~~~~~~~~~~~~~~~~~~~~~

*  *DO* explain **why** something is done, its purpose, and its goal. The code shows **how** it is done, so commenting on this can be redundant.
*  *DO* explain ambiguity or complexities to avoid confusion
*  *DO* embrace documentation as an integral part of the overall development process
*  *DO* treat documenting as code and follow principles such as *Don't Repeat Yourself* and *Easier to Change*

DON'Ts for Documenting Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*  *DON'T* write comments as a crutch for poor code
*  *DON'T* comment *every* function, data structure, type declaration

Developer Tips
--------------

* flake8 will warn you if the cyclomatic complexity of a function is too high.

    * https://github.com/PyCQA/mccabe


FAQs
----

.. _Why squash and rebase?:

Why squash and rebase commits?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you merge a support branch back into ``main``, the branch is typically squashed down to a single buildable commit, and then rebased on top of the main repo's ``main`` branch.

Why?

* Ensures build passes from the commit
* Cleans up Git history for easy navigation
* Makes collaboration and review process more efficient
* Makes handling conflicts from rebasing simple since you only have to deal with conflicted commits


How do I squash and rebase commits?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Use GitHub's Squash and Merge feature in the pull request

   * You still need to rebase on the latest ``main`` if ``main`` is ahead of your branch.

* Manually squash and rebase

   1. `<OPTIONAL if you are forking>` Sync your fork of ``main`` (aka ``origin``) with the root ``main`` (aka ``upstream``) ::

        git checkout main
        git rebase upstream/main
        git push -f origin main

   2. Get the SHA of the commit OR number of commits to rebase to ::

        git checkout <branch-name>
        git log --graph --decorate --pretty=oneline --abbrev-commit

   3. Squash commits::

        git rebase -i [SHA]

        # OR

        git rebase -i HEAD~[NUMBER OF COMMITS]

   4. Rebase branch onto ``main`` ::

        git rebase main
        git push -f origin <BRANCH-NAME>

   5. Make sure your squashed commit messages are refined

   6. Force push to remote branch ::

        git push -f origin <BRANCH-NAME>
