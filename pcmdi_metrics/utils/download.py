import os
import re

import requests


def download_files_from_github(url, output_dir):
    """
    Download files from a GitHub directory or a single file.

    Parameters
    ----------
    url : str
        The URL of the GitHub directory or file.
    output_dir : str
        The local directory to save the downloaded files.

    Raises
    ------
    Exception
        If unable to fetch or parse the directory or file.

    Notes
    -----
    This function downloads all files from the specified GitHub directory
    or a single file if a file URL is provided. It constructs the raw file
    URLs based on the provided URL and saves the files to the specified
    output directory.

    Example
    -------
    >>> github_directory_url = "https://github.com/PCMDI/pcmdi_metrics_results_archive/tree/main/metrics_results/enso_metric/cmip5/historical/v20210104/ENSO_perf"
    >>> output_directory = "downloaded_files"
    >>> download_files_from_github(github_directory_url, output_directory)
    >>> github_file_url = "https://github.com/PCMDI/pcmdi_metrics_results_archive/blob/main/metrics_results/enso_metric/cmip5/historical/v20210104/ENSO_perf/cmip5_historical_ENSO_perf_v20210104_allModels_allRuns.json"
    >>> download_files_from_github(github_file_url, output_directory)
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # GitHub raw content base URL
    base_raw_url = "https://raw.githubusercontent.com"

    # Check if the URL is for a file or a directory
    if "blob" in url:
        # It's a file URL
        file_name = url.split("/")[-1]
        raw_file_url = url.replace("github.com/", "raw.githubusercontent.com/").replace(
            "/blob/", "/"
        )
        download_file(raw_file_url, file_name, output_dir)

    elif "tree" in url:
        # It's a directory URL
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch URL: {url} (Status Code: {response.status_code})"
            )

        # Extract file links using a regex pattern
        html_content = response.text
        file_pattern = re.compile(r'href="(/[^/]+/[^/]+/blob/[^"]+)"')
        matches = file_pattern.findall(html_content)

        if matches:
            # Remove duplicates and download each file
            matches = list(set(matches))
            for match in matches:
                file_name = match.split("/")[-1]
                raw_file_url = base_raw_url + match.replace("/blob/", "/")
                download_file(raw_file_url, file_name, output_dir)
        else:
            print("No files found in the directory.")

    else:
        raise Exception(
            "The provided URL is neither a valid GitHub directory nor a file."
        )


def download_file(raw_file_url, file_name, output_dir):
    """Helper function to download a single file."""
    print(f"Downloading {file_name} from {raw_file_url}...")
    file_response = requests.get(raw_file_url)
    if file_response.status_code == 200:
        save_path = os.path.join(output_dir, file_name)
        with open(save_path, "wb") as file:
            file.write(file_response.content)
        print(f"Saved {file_name} to {save_path}")
    else:
        print(
            f"Failed to download {file_name} (Status Code: {file_response.status_code})"
        )
