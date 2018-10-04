#!/usr/bin/env python
from __future__ import print_function
from pcmdi_metrics.driver.pmp_parser import PMPParser
import tempfile
import requests
import os
import cdat_info


def download_file(download_url_root, name, local_filename):
    r = requests.get("%s/%s" % (download_url_root, name), stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter local_filename keep-alive new chunks
                f.write(chunk)


parser = PMPParser(description='Get sample data')
parser.add_argument("--dataset", help="Download observation or sample data or both",
                    default="all", choices=["all", "obs", "sample"])
parser.add_argument("--version", help="which version to use", default="latest")
parser.add_argument("--server", help="which serverto use",
                    default="https://pcmdiweb.llnl.gov/pss/pmpdata")
parser.add_argument("--version_in_path", action="store_true", default=False,
                    help="Append version in rooot path, avoids clobbering versions")
parser.add_argument(
    "--output-path", help="directory where to download", default=None)
# parser.use("num_workers")
p = parser.get_parameter()

# Step1 prepare the paths to get the sample datafiles
pth = tempfile.mkdtemp()
files = []
if p.dataset in ["all", "obs"]:  # ok we need obs
    download_file(p.server, "obs_{}.txt".format(p.version), "obs.txt")
    files.append("obs.txt")
if p.dataset in ["all", "sample"]:
    download_file(p.server, "sample_{}.txt".format(p.version), "sample.txt")
    files.append("sample.txt")

# Ok now we can download
for file in files:
    # First do we clobber or not?
    pathout = p.output_path
    if p.version_in_path:
        with open(file) as f:
            header = f.readline().strip()
            version = header.split("_")[-1]
            pathout = os.path.join(p.output_path, version)
    cdat_info.download_sample_data_files(file, path=pathout)
