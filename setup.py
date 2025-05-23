from __future__ import print_function

import subprocess
import sys

from setuptools import find_packages, setup

if "--enable-devel" in sys.argv:
    install_dev = True
    sys.argv.remove("--enable-devel")
else:
    install_dev = False

# Read version from _version.py
version = {}
with open("pcmdi_metrics/_version.py") as f:
    exec(f.read(), version)
    release_version = version["__version__"]

p = subprocess.Popen(
    ("git", "describe", "--tags"),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Generate and install default arguments
p = subprocess.Popen(["python", "setup_default_args.py"], cwd="share")
p.communicate()

packages = find_packages(exclude=["cmec", "tests"], include=["pcmdi_metrics*"])

scripts = [
    "pcmdi_metrics/mean_climate/pcmdi_compute_climatologies.py",
    "pcmdi_metrics/mean_climate/mean_climate_driver.py",
    "pcmdi_metrics/monsoon_wang/scripts/mpindex_compute.py",
    "pcmdi_metrics/monsoon_wang/monsoon_wang_driver.py",
    "pcmdi_metrics/monsoon_sperber/driver_monsoon_sperber.py",
    "pcmdi_metrics/mjo/mjo_metrics_driver.py",
    "pcmdi_metrics/variability_mode/variability_modes_driver.py",
    "pcmdi_metrics/enso/enso_driver.py",
    "pcmdi_metrics/precip_variability/variability_across_timescales_PS_driver.py",
    "pcmdi_metrics/misc/scripts/parallelize_driver.py",
    "pcmdi_metrics/misc/scripts/get_pmp_data.py",
    "pcmdi_metrics/precip_distribution/precip_distribution_driver.py",
    "pcmdi_metrics/cloud_feedback/cloud_feedback_driver.py",
    "pcmdi_metrics/extremes/extremes_driver.py",
    "pcmdi_metrics/sea_ice/sea_ice_driver.py",
    "pcmdi_metrics/drcdm/drcdm_driver.py",
]

entry_points = {
    "console_scripts": [
        "compositeDiurnalStatistics.py = pcmdi_metrics.diurnal.scripts.compositeDiurnalStatistics:main",
        "computeStdOfDailyMeans.py = pcmdi_metrics.diurnal.scripts.computeStdOfDailyMeans:main",
        "fourierDiurnalAllGrid.py = pcmdi_metrics.diurnal.scripts.fourierDiurnalAllGrid:main",
        "fourierDiurnalGridpoints.py = pcmdi_metrics.diurnal.scripts.fourierDiurnalGridpoints:main",
        "savg_fourier.py = pcmdi_metrics.diurnal.scripts.savg_fourier:main",
        "std_of_dailymeans.py = pcmdi_metrics.diurnal.scripts.std_of_dailymeans:main",
        "std_of_hourlyvalues.py = pcmdi_metrics.diurnal.scripts.std_of_hourlyvalues:main",
        "std_of_meandiurnalcycle.py = pcmdi_metrics.diurnal.scripts.std_of_meandiurnalcycle:main",
    ],
}

data_files = (
    (
        "share/pmp/graphics/png",
        [
            "share/pcmdi/PCMDILogo_1588x520px_300dpi.png",
            "share/pcmdi/PCMDILogo_200x65px_72dpi.png",
            "share/pcmdi/PCMDILogo_300x98px_72dpi.png",
            "share/pcmdi/PCMDILogo_400x131px_72dpi.png",
            "share/pcmdi/PCMDILogo_500x164px_72dpi.png",
            "share/pcmdi/PCMDILogoText_1365x520px_300dpi.png",
            "share/pcmdi/PMPLogoText_1359x1146px_300dpi.png",
            "share/pcmdi/PMPLogo_1359x1146px_300dpi.png",
            "share/pcmdi/PMPLogo_500x421px_72dpi.png",
        ],
    ),
    (
        "share/pmp",
        (
            "doc/obs_info_dictionary.json",
            "share/pcmdi_metrics_table",
            "share/disclaimer.txt",
            "share/test_data_files.txt",
            "share/cmip_model_list.json",
            "share/default_regions.py",
            "share/DefArgsCIA.json",
            "pcmdi_metrics/precip_distribution/lib/cluster3_pdf.amt_regrid.360x180_IMERG_ALL_90S90N.nc",
            "share/data/navy_land.nc",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.cpg",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.dbf",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.prj",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.sbn",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.sbx",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.shp",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.shp.xml",
            "share/data/cb_2023_us_state_500k_ncaregions_wgs84/cb_2023_us_state_500k_ncaregions_wgs84.shx",
        ),
    ),
    (
        "share/pmp/viewer/assets",
        (
            "pcmdi_metrics/viewer/assets/CMIP6_Amon.json",
            "pcmdi_metrics/viewer/assets/ENSO_ACCESS-CM2_thumbnail.png",
            "pcmdi_metrics/viewer/assets/mean_climate_portrait_plot_20250213.png",
            "pcmdi_metrics/viewer/assets/PMPLogo_500x421px_72dpi.png",
            "pcmdi_metrics/viewer/assets/style.css",
        ),
    ),
)

setup(
    name="pcmdi_metrics",
    version=release_version,
    author="PCMDI",
    description="model metrics tools",
    url="http://github.com/PCMDI/pcmdi_metrics",
    packages=packages,
    scripts=scripts,
    data_files=data_files,
    entry_points=entry_points,
)
