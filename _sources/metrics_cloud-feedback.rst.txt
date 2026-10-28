.. title:: PMP Cloud Feedback


*****************
Cloud Feedbacks
*****************

Overview
========

The cloud feedback metrics implemented in PMP are originally from `assessed-cloud-fbks <https://github.com/mzelinka/assessed-cloud-fbks>`_ |DOI|,
developed by `@mzelinka <https://mzelinka.github.io/>`_ at LLNL. This code performs the analysis of Zelinka et al. (2022).
It computes GCM cloud feedback components and compares them to the expert-assessed values from Sherwood et al. (2020).

.. |DOI| image:: https://zenodo.org/badge/353136800.svg
   :target: https://zenodo.org/badge/latestdoi/353136800


Instructions
============

To use the cloud feedback metrics, follow these steps:


1. Install PMP
##############

Install PMP via conda following the `installation instructions <http://pcmdi.github.io/pcmdi_metrics/install.html>`_. For example: ::

    conda create -n [YOUR_CONDA_ENVIRONMENT] -c conda-forge pcmdi_metrics


2. Activate PMP installed conda environment
###########################################

Activate your environment (if PMP installed env is different from your current one): ::

    conda activate [YOUR_CONDA_ENVIRONMENT]


3. Clone PMP repo to your local
################################

Clone PMP repo to your local for pre-calculated data: ::

    git clone https://github.com/PCMDI/pcmdi_metrics

Once completed, go to ``pcmdi_metrics/pcmdi_metrics/cloud_feedback`` directory: ::

    cd [YOUR LOCAL CLONED PMP REPOSITORY]
    cd pcmdi_metrics/pcmdi_metrics/cloud_feedback


4. Edit parameter files
#######################

In `param/my_param.py <https://github.com/PCMDI/pcmdi_metrics/blob/main/pcmdi_metrics/cloud_feedback/param/my_param.py>`_,
update the "User Input" section so it points to your model's amip and amip-p4K files: ::

    # User Input:
    # ================================================================================================
    model = "GFDL-CM4"
    variant = "r1i1p1f1"

    input_files_json = "./param/input_files.json"

    # Flag to compute ECS
    # True: compute ECS using abrupt-4xCO2 run
    # False: do not compute, instead rely on ECS value present in the json file (if it exists)
    # get_ecs = True
    get_ecs = False

    # Output directory path (directory will be generated if it does not exist yet.)
    xml_path = "./xmls/"
    figure_path = "./figures/"
    output_path = "./output"
    output_json_filename = "_".join(["cloud_feedback", model, variant]) + ".json"
    # ================================================================================================

You will need to update `param/input_files.json <https://github.com/PCMDI/pcmdi_metrics/blob/main/pcmdi_metrics/cloud_feedback/param/input_files.json>`_
file as well to provide data path for your input files.


5. Run the code and inspect the generated output files
#######################################################

Run calculation: ::

    python cloud_feedback_driver.py -p param/my_param.py

Once code is completed, check ``output`` directory (``output_path`` from the above parameter file) for JSON
and ``figures`` directory (``figure_path`` from the above parameter file) for figures and text tables.


References
==========

* Zelinka et al. (2022): `Evaluating climate models' cloud feedbacks against expert judgement <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021JD035198>`_, *J. Geophys. Res.*, 127, e2021JD035198, doi:10.1029/2021JD035198.

* Sherwood et al. (2020): `A combined assessment of Earth's climate sensitivity <https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2019RG000678>`_, *Rev. Geophys.*, 58, e2019RG000678, doi:10.1029/2019RG000678.
