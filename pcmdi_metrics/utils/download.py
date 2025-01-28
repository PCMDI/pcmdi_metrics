import os
import re

import requests


def download_files_from_github_directory(url, output_dir):
    """
    Download all files from a GitHub directory.

    Parameters
    ----------
    url : str
        The URL of the GitHub directory.
    output_dir : str
        The local directory to save the downloaded files.

    Raises
    ------
    Exception
        If unable to fetch or parse the directory.

    Notes
    -----
    This function downloads all files from the specified GitHub directory
    without using BeautifulSoup. It constructs the raw file URLs based on
    the provided directory URL and saves the files to the specified output
    directory.

    Example
    -------
    >>> from pcmdi_metrics.utils import download_files_from_github_directory
    >>> github_directory_url = "https://github.com/PCMDI/pcmdi_metrics_results_archive/tree/main/metrics_results/enso_metric/cmip5/historical/v20210104/ENSO_perf"
    >>> output_directory = "downloaded_files"
    >>> download_files_from_github_directory(github_directory_url, output_directory)
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # GitHub raw content base URL
    base_raw_url = "https://raw.githubusercontent.com"
    repo_path = "/".join(url.split("github.com/")[1].split("/tree/"))

    print("repo_path:", repo_path)

    # Get the HTML content of the directory page
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch URL: {url} (Status Code: {response.status_code})"
        )

    # Extract file links using a more flexible regex pattern
    html_content = response.text
    file_pattern = re.compile(r'href="(/[^/]+/[^/]+/blob/[^"]+)"')
    print("file_pattern:", file_pattern)
    matches = file_pattern.findall(html_content)

    if not matches:
        print("No files found in the directory.")
        return

    # Remove duplicates
    matches = list(set(matches))

    # Download each file
    for match in matches:
        # Extract the file name and create the raw file URL
        file_name = match.split("/")[-1]
        raw_file_url = base_raw_url + match.replace("/blob/", "/")

        save_path = os.path.join(output_dir, file_name)

        # Download the file
        print(f"Downloading {file_name}...")
        file_response = requests.get(raw_file_url)
        if file_response.status_code == 200:
            with open(save_path, "wb") as file:
                file.write(file_response.content)
            print(f"Saved {file_name} to {save_path}")
        else:
            print(
                f"Failed to download {file_name} (Status Code: {file_response.status_code})"
            )
