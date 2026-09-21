import json
import os
from collections import defaultdict


# Create a multi-level defaultdict
def multi_level_dict():
    return defaultdict(multi_level_dict)


# Function to convert nested defaultdict to regular dict
def convert_to_regular_dict(d):
    if isinstance(d, defaultdict):
        # Recursively convert each value to a regular dict
        d = {k: convert_to_regular_dict(v) for k, v in d.items()}
    return d


def print_dict(dictionary):
    print(json.dumps(convert_to_regular_dict(dictionary), indent=4, sort_keys=True))


def load_json_as_dict(file_path):
    """
    Load JSON data from a file and return it as a dictionary.

    :param file_path: Path to the JSON file.
    :type file_path: str
    :return: Dictionary representation of the JSON data.
    :rtype: dict
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file {file_path}.")
        return None


def write_to_json(data_dict, filename="output/output.json"):
    # Extract the directory path from the filename
    directory = os.path.dirname(filename)

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Dump the dictionary as a JSON file
    with open(filename, "w") as json_file:
        json.dump(data_dict, json_file, indent=4)

    print(f"Dictionary has been successfully written to {filename}")
