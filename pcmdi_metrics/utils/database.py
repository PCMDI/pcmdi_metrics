import os
import re
import requests
import json

def database_metrics(mip:str, model:str, exp:str, metrics:list=None, debug:bool=False):
    """
    Retrieves JSON files from the PMP Archive based on specified mip, model, exp, and metrics.

    Parameters
    ----------
    mip : str
        The model intercomparison project (e.g., 'cmip5', 'cmip6').
    model : str
        The model name (e.g., 'ACCESS-CM2', 'EC-EARTH').
    exp : str
        The experiment (e.g., 'historical', 'amip').
    metrics : list, optional
        List of metrics (e.g., 'enso_metric', 'mean_climate', 'mjo', 'variability_modes', 'qbo-mjo'). Default None retrieves files for all metrics.
    debug : bool, optional
        If true, print more interim outputs for debugging.
    Returns
    -------
    dict
        A dictionary of JSON files from the PMP Archive database.
    """
    
    if metrics is None:
        metrics = ['enso_metric', 'mean_climate', 'mjo', 'variability_modes', 'qbo-mjo']

    subdir_dict = load_subdir_dict()        
    results_dict = dict()
        
    for metric in metrics:
        
        json_url_list = find_pmp_archive_json_urls(metric, mip, exp)
        subdirs = subdir_dict.get(metric, {}).get(mip, {}).get(exp, ".")
        
        if debug:
            print(metric, json_url_list, subdirs)
            print(len(json_url_list), len(subdirs))
            print("metric, json_url_list, subdirs:", metric, json_url_list, subdirs)
            
        results_dict[metric] = dict()
        
        keys = list()
        
        for i, url in enumerate(json_url_list):
            tmp_dict = load_json_from_url(url)
                        
            # Initialize a dict
            results_dict_i = dict()
            results_dict_i["RESULTS"] = dict()
            results_dict_i["RESULTS"][model] = None
            
            # Find available models
            if "RESULTS" in tmp_dict.keys():
                if metric == "enso_metric":
                    models = tmp_dict["RESULTS"]["model"].keys()
                else:
                    models = tmp_dict["RESULTS"].keys()
                models = sorted(list(models))
            
            if debug:        
                print(metric, tmp_dict["RESULTS"].keys())
                print("models:", models)

            # Find info for the model
            if model is not None:
                if model in models:
                    if metric == "enso_metric":
                        results_dict_i["RESULTS"][model] = tmp_dict["RESULTS"]["model"][model]
                    else:
                        results_dict_i["RESULTS"][model] = tmp_dict["RESULTS"][model]
            else:
                results_dict_i["RESULTS"] = tmp_dict["RESULTS"]

            # Find provenance info                
            if "provenance" in tmp_dict.keys():
                results_dict_i["provenance"] = tmp_dict["provenance"]
                
            potential_keys_for_reference = ["REFERENCE", "reference", "Reference", "References", "REF"]
            
            # Find reference info
            for potential_key in potential_keys_for_reference:
                if potential_key in tmp_dict.keys():
                    results_dict_i["REFERENCE"] = tmp_dict[potential_key]
                    break
                else:
                    results_dict_i["REFERENCE"] = None
                
            # Name the key
            key = os.path.basename(url).replace(".json", "")
            
            # Update the key name if following condition is met
            if len(json_url_list) == len(subdirs):
                key = subdirs[i]
            elif "Variable" in tmp_dict.keys():
                key = tmp_dict["Variable"]["id"]
            else:
                if metric == "mean_climate":
                    if "variable_id" in list(tmp_dict.keys()):
                        key = tmp_dict["variable_id"]
            keys.append(key)

            # Add the content to results dict
            if key == ".":
                results_dict[metric] = results_dict_i           
            else:
                results_dict[metric][key] = results_dict_i

            # Find sub keys, just to check
            if debug:
                sub_keys = list(tmp_dict.keys())
                print("metric, key, sub_keys:", metric, key, sub_keys)
            
        if debug:
            print("metric, keys:", metric, keys, '\n')
            
        print(f"Found {len(json_url_list)} JSON files for metric '{metric}' and collected info for model '{model}'.")
            
    return results_dict

def find_pmp_archive_json_urls(metric:str, mip:str, exp:str, version:str=None, search_keys:list=None):
    """
    Find PMP archive JSON URLs based on the provided metric, mip, exp, and optional version and search keys.

    Parameters
    ----------
    metric : str
        The metric to search for (e.g., 'enso_metric', 'mean_climate', 'mjo', 'variability_modes', 'qbo-mjo').
    mip : str
        The model intercomparison project (e.g., 'cmip5', 'cmip6').
    exp : str
        The experiment (e.g., 'historical', 'amip').
    version : str, optional
        The version of the dataset, by default None.
    search_keys : list, optional
        A list of search keys to filter the URLs, by default None.

    Returns
    -------
    list
        A list of URLs matching the search criteria.
    """
    version_dict = load_version_dict()
    subdir_dict = load_subdir_dict()
    
    github_repo = "https://github.com/PCMDI/pcmdi_metrics_results_archive"
    branch = "tree/main"

    if version is None:
        try:
            version = version_dict[metric][mip][exp]
        except KeyError:
            raise KeyError(f"Version not found for metric '{metric}', mip '{mip}', and experiment '{exp}'.")

    # List of available metrics
    # Available options for metrics: enso_metric, mean_climate, variability_modes, mjo, qbo-mjo
    # will add precip and possibly others later ...
    available_metrics = list(version_dict.keys())
        
    subdirs = subdir_dict.get(metric, {}).get(mip, {}).get(exp, ".")
    
    urls_interim = list()
    urls_final = list()
    
    if metric not in available_metrics:
        raise ValueError(f"Metric '{metric}' is not supported.")

    for subdir in subdirs:
        dir_url = os.path.join(github_repo, branch, "metrics_results", metric, mip, exp, version, subdir)
        urls = find_json_files_in_the_directory(dir_url)
        urls_interim.extend(urls)
            
    if search_keys is not None:
        for url in urls_interim:
            for search_key in search_keys:
                if search_key in url:
                    urls_final.append(url)
    else:
        urls_final = urls_interim
                    
    return urls_final

def load_version_dict():
    """
    Create a dictionary of each metric and mip's corresponding data version.

    Returns
    -------
    dict
        A dictionary of relevant data versions for each metric and mip.
    """
    version_dict = {
        "enso_metric":{
            "cmip5":{
                "historical": "v20210104"
            },
            "cmip6":{
                "historical": "v20210620"
            }
        },
        "mean_climate":{
            "cmip5":{
                "amip": "v20200429",
                "historical": "v20220928"
            },
            "cmip6":{
                "amip": "v20210830",
                "historical": "v20230823"
            }            
        },
        "variability_modes":{
            "cmip3":{
                "20c3m": "v20210119",
                "amip": "v20210119"
            },
            "cmip5":{
                "amip": "v20210119",
                "historical": "v20210119"
            },
            "cmip6":{
                "amip": "v20210119",
                "historical": "v20220825"
            }            
        },
        "mjo":{
            "cmip5":{
                "historical": "v20230924"
            },
            "cmip6":{
                "historical": "v20230924"
            }
        },
        "qbo-mjo":{
            "cmip5":{
                "historical": "v20240422"
            },
            "cmip6":{
                "historical": "v20240422"
            }
        }
    }    
    return version_dict


def load_subdir_dict():
    """
    Create a dictionary of each metric and mip's corresponding subdirectories.

    Returns
    -------
    dict
        A dictionary of each metric and mip subdirectory structure.
    """
    subdir_dict = {
        "enso_metric":{
            "cmip5":{
                "historical": ["ENSO_perf", "ENSO_proc", "ENSO_tel"]
            },
            "cmip6":{
                "historical": ["ENSO_perf", "ENSO_proc", "ENSO_tel"]
            }
        },
        "mean_climate":{
            "cmip5":{
                "amip": ["."],
                "historical": ["."]
            },
            "cmip6":{
                "amip": ["."],
                "historical": ["."]
            }            
        },
        "variability_modes":{
            "cmip3":{
                "20c3m": [
                    "NAM/NOAA-CIRES_20CR",
                    "NAO/NOAA-CIRES_20CR",
                    "NPGO/HadISSTv1.1",
                    "NPO/NOAA-CIRES_20CR",
                    "PDO/HadISSTv1.1",
                    "PNA/NOAA-CIRES_20CR",
                    "SAM/NOAA-CIRES_20CR"
                ],
                "amip": [
                    "NAM/NOAA-CIRES_20CR",
                    "NAO/NOAA-CIRES_20CR",
                    "NPGO/HadISSTv1.1",
                    "NPO/NOAA-CIRES_20CR",
                    "PNA/NOAA-CIRES_20CR",
                    "SAM/NOAA-CIRES_20CR"
                ],
            },
            "cmip5":{
                "amip": [
                    "NAM/NOAA-CIRES_20CR",
                    "NAO/NOAA-CIRES_20CR",
                    "NPGO/HadISSTv1.1",
                    "NPO/NOAA-CIRES_20CR",
                    "PNA/NOAA-CIRES_20CR",
                    "SAM/NOAA-CIRES_20CR"
                ],
                "historical": [
                    "NAM/NOAA-CIRES_20CR",
                    "NAO/NOAA-CIRES_20CR",
                    "NPGO/HadISSTv1.1",
                    "NPO/NOAA-CIRES_20CR",
                    "PDO/HadISSTv1.1",
                    "PNA/NOAA-CIRES_20CR",
                    "SAM/NOAA-CIRES_20CR"
                ],
            },
            "cmip6":{
                "amip": [
                    "NAM/NOAA-CIRES_20CR",
                    "NAO/NOAA-CIRES_20CR",
                    "NPGO/HadISSTv1.1",
                    "NPO/NOAA-CIRES_20CR",
                    "PNA/NOAA-CIRES_20CR",
                    "SAM/NOAA-CIRES_20CR"
                ],
                "historical": [
                    "NAM/NOAA-CIRES_20CR",
                    "NAO/NOAA-CIRES_20CR",
                    "NPGO/HadISSTv1.1",
                    "NPO/NOAA-CIRES_20CR",
                    "PDO/HadISSTv1.1",
                    "PNA/NOAA-CIRES_20CR",
                    "SAM/NOAA-CIRES_20CR"
                ],
            }            
        },
    }
    return subdir_dict

def find_json_files_in_the_directory(url):
    """
    Find JSON file URLs based on directory URL.

    Parameters
    -------
    url : str
        The URL of the directory where JSON files are stored (e.g., pcmdi_metrics_results_archive).

    Returns
    -------
    list
        A list of all URLs for available JSON files in the given directory.
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch URL: {url} (Status Code: {response.status_code})"
        )

    # Extract file links using a regex pattern
    html_content = response.text
    file_pattern = re.compile(r'href="(/[^/]+/[^/]+/blob/[^"]+)"')
    matches = file_pattern.findall(html_content)
    urls = list()

    # GitHub raw content base URL
    base_raw_url = "https://raw.githubusercontent.com"

    if matches:
        # Remove duplicates and download each file
        matches = list(set(matches))
        for match in matches:
            raw_file_url = base_raw_url + match.replace("/blob/", "/")
            urls.append(raw_file_url)
        
    return urls

def load_json_from_url(url):
    """
    Load JSON data from a given URL.
    
    Parameters
    ----------
    url : str
        The URL of the JSON file to be loaded.

    Returns
    -------
    dict or None
        The JSON data as a dictionary if the request is successful and the content is valid JSON.
        Returns None if there is an error fetching the JSON file or decoding the JSON content.

    Example
    -------
    >>> url = 'https://example.com/path/to/your/file.json'  # Replace with your JSON file URL
    >>> json_data = load_json_from_url(url)
    """
    
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Load the response content as JSON
        data = response.json()
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the JSON file: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON")
        return None