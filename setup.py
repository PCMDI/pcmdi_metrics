from setuptools import find_packages, setup

setup(
    name="pcmdi_metrics",
    version="2.0",
    author="PCMDI",
    author_email="shaheen2@llnl.gov",
    url='http://github.com/PCMDI/pcmdi_metrics',
    description="Framework for creating climate diagnostics.",
    packages=find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    package_data = {'pcmdi_metrics':['PMP/share/*']},
    include_package_data=True
)
