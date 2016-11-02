from setuptools import find_packages, setup

setup(
    name="pcmdi_metrics2",
    version="1.2",
    author="PCMDI",
    author_email="pcmdi@llnl.gov",
    url='http://github.com/PCMDI/pcmdi_metrics',
    description="Framework for creating climate diagnostics.",
    packages=find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    package_data = {'pcmdi_metrics2':['share/*']},
    include_package_data=True
)
