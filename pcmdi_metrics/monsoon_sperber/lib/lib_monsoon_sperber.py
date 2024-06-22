from collections import defaultdict

import xcdat as xc


def tree():
    return defaultdict(tree)


def pick_year_last_day(ds):
    eday = 31
    try:
        time_key = xc.axis.get_dim_keys(ds, axis="T")
        if "calendar" in ds[time_key].attrs.keys():
            if "360" in ds[time_key]["calendar"]:
                eday = 30
        else:
            if "360" in ds[time_key][0].values.item().calendar:
                eday = 30
    except Exception:
        pass
    return eday
