from distutils.core import setup

data_files = [
                ('share/pmp', ('docs/obs_info_dictionary.json',
                               'pcmdi_metrics/share/disclaimer.txt'))
            ]
packages = {'pcmdi_metrics': 'pcmdi_metrics',
            'pcmdi_metrics.metrics': 'pcmdi_metrics/metrics'
            }
setup(
    name="pcmdi_metrics",
    version="1.2",
    author="PCMDI",
    author_email="pcmdi@llnl.gov",
    url='http://github.com/PCMDI/pcmdi_metrics',
    description="Framework for creating climate diagnostics.",
    packages=packages,
    include_package_data=True,
    data_files=data_files
)

