# find common models in CMIP5 and CMIP6 group
import re


def get_prefix(item):
    return re.match(r"^[A-Za-z]+", item).group(0)


def get_common_model(list1, list2):
    # Get prefixes for both lists
    prefixes_list1 = {get_prefix(item) for item in list1}
    prefixes_list2 = {get_prefix(item) for item in list2}

    # Filter both lists based on common prefixes
    filtered_list1 = [item for item in list1 if get_prefix(item) in prefixes_list2]
    filtered_list2 = [item for item in list2 if get_prefix(item) in prefixes_list1]

    # print("Filtered List 1:", filtered_list1)
    # print("Filtered List 2:", filtered_list2)

    return filtered_list1, filtered_list2
