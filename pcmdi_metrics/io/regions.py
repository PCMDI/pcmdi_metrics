from typing import Union

import xarray as xr
import xcdat as xc

from pcmdi_metrics.io import da_to_ds, get_longitude, select_subset


def load_regions_specs() -> dict:
    regions_specs = {
        # Mean Climate
        "global": {},
        "NHEX": {"domain": {"latitude": (30.0, 90)}},
        "SHEX": {"domain": {"latitude": (-90.0, -30)}},
        "TROPICS": {"domain": {"latitude": (-30.0, 30)}},
        "90S50S": {"domain": {"latitude": (-90.0, -50)}},
        "50S20S": {"domain": {"latitude": (-50.0, -20)}},
        "20S20N": {"domain": {"latitude": (-20.0, 20)}},
        "20N50N": {"domain": {"latitude": (20.0, 50)}},
        "50N90N": {"domain": {"latitude": (50.0, 90)}},
        "CONUS": {"domain": {"latitude": (24.7, 49.4), "longitude": (-124.78, -66.92)}},
        "land": {"value": 100},
        "land_NHEX": {"value": 100, "domain": {"latitude": (30.0, 90)}},
        "land_SHEX": {"value": 100, "domain": {"latitude": (-90.0, -30)}},
        "land_TROPICS": {"value": 100, "domain": {"latitude": (-30.0, 30)}},
        "land_CONUS": {
            "value": 100,
            "domain": {"latitude": (24.7, 49.4), "longitude": (-124.78, -66.92)},
        },
        "ocean": {"value": 0},
        "ocean_NHEX": {"value": 0, "domain": {"latitude": (30.0, 90)}},
        "ocean_SHEX": {"value": 0, "domain": {"latitude": (-90.0, -30)}},
        "ocean_TROPICS": {"value": 0, "domain": {"latitude": (30.0, 30)}},
        "ocean_50S50N": {"value": 0.0, "domain": {"latitude": (-50.0, 50)}},
        "ocean_50S20S": {"value": 0.0, "domain": {"latitude": (-50.0, -20)}},
        "ocean_20S20N": {"value": 0.0, "domain": {"latitude": (-20.0, 20)}},
        "ocean_20N50N": {"value": 0.0, "domain": {"latitude": (20.0, 50)}},
        # Modes of variability
        "NAM": {"domain": {"latitude": (20.0, 90), "longitude": (-180, 180)}},
        "NAO": {"domain": {"latitude": (20.0, 80), "longitude": (-90, 40)}},
        "SAM": {"domain": {"latitude": (-20.0, -90), "longitude": (0, 360)}},
        "PSA1": {"domain": {"latitude": (-20.0, -90), "longitude": (0, 360)}},
        "PSA2": {"domain": {"latitude": (-20.0, -90), "longitude": (0, 360)}},
        "PNA": {"domain": {"latitude": (20.0, 85), "longitude": (120, 240)}},
        "NPO": {"domain": {"latitude": (20.0, 85), "longitude": (120, 240)}},
        "PDO": {"domain": {"latitude": (20.0, 70), "longitude": (110, 260)}},
        "NPGO": {"domain": {"latitude": (20.0, 70), "longitude": (110, 260)}},
        "AMO": {"domain": {"latitude": (0.0, 70), "longitude": (-80, 0)}},
        # Monsoon domains for Wang metrics
        # All monsoon domains
        "AllMW": {"domain": {"latitude": (-40.0, 45.0), "longitude": (0.0, 360.0)}},
        "AllM": {"domain": {"latitude": (-45.0, 45.0), "longitude": (0.0, 360.0)}},
        # North American Monsoon
        "NAMM": {"domain": {"latitude": (0.0, 45.0), "longitude": (210.0, 310.0)}},
        # South American Monsoon
        "SAMM": {"domain": {"latitude": (-45.0, 0.0), "longitude": (240.0, 330.0)}},
        # North African Monsoon
        # "NAFM": {"domain": {"latitude": (0.0, 45.0), "longitude": (310.0, 60.0)}},
        "NAFM": {"domain": {"latitude": (0.0, 45.0), "longitude": (-50.0, 60.0)}},
        # South African Monsoon
        "SAFM": {"domain": {"latitude": (-45.0, 0.0), "longitude": (0.0, 90.0)}},
        # Asian Summer Monsoon
        "ASM": {"domain": {"latitude": (0.0, 45.0), "longitude": (60.0, 180.0)}},
        # Australian Monsoon
        "AUSM": {"domain": {"latitude": (-45.0, 0.0), "longitude": (90.0, 160.0)}},
        # Monsoon domains for Sperber metrics
        # All India rainfall
        "AIR": {"domain": {"latitude": (7.0, 25.0), "longitude": (65.0, 85.0)}},
        # North Australian
        "AUS": {"domain": {"latitude": (-20.0, -10.0), "longitude": (120.0, 150.0)}},
        # Sahel
        "Sahel": {"domain": {"latitude": (13.0, 18.0), "longitude": (-10.0, 10.0)}},
        # Gulf of Guinea
        "GoG": {"domain": {"latitude": (0.0, 5.0), "longitude": (-10.0, 10.0)}},
        # North American monsoon
        "NAmo": {"domain": {"latitude": (20.0, 37.0), "longitude": (-112.0, -103.0)}},
        # South American monsoon
        "SAmo": {"domain": {"latitude": (-20.0, 2.5), "longitude": (-65.0, -40.0)}},
    }

    return regions_specs


def region_subset(
    ds: Union[xr.Dataset, xr.DataArray],
    region: str,
    data_var: str = None,
    regions_specs: dict = None,
    debug: bool = False,
) -> Union[xr.Dataset, xr.DataArray]:
    """
    Subset a dataset or data array based on a specified region.

    This function subsets an xarray Dataset or DataArray based on the latitude and longitude
    coordinates defined for a given region. It handles different longitude conventions
    and can optionally provide debug information.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array to be subsetted.
    region : str
        The name of the region to subset the data to. This should correspond to a key
        in the regions_specs dictionary.
    data_var : str, optional
        The name of the data variable if ds is a DataArray, by default None, which names DataArray as "variable" in the Dataset if DataArray has no name.
    regions_specs : dict, optional
        A dictionary containing the specifications for different regions. If None,
        it will be loaded from a default source, by default None.
    debug : bool, optional
        If True, print debug information during the subsetting process, by default False.

    Returns
    -------
    Union[xr.Dataset, xr.DataArray]
        The subsetted dataset or data array, matching the input type.

    Notes
    -----
    This function first converts DataArrays to Datasets for processing, then converts
    back if necessary. It handles both latitude and longitude subsetting based on the
    region specifications, and can deal with different longitude conventions (0 to 360
    vs -180 to 180).

    """
    if isinstance(ds, xr.DataArray):
        is_dataArray = True
        if data_var is None:
            if ds.name is None:
                data_var = "variable"
            else:
                data_var = ds.name
        ds = da_to_ds(ds, data_var)
    else:
        is_dataArray = False

    if regions_specs is None:
        regions_specs = load_regions_specs()

    if "domain" in regions_specs[region]:
        if "latitude" in regions_specs[region]["domain"]:
            lat0 = regions_specs[region]["domain"]["latitude"][0]
            lat1 = regions_specs[region]["domain"]["latitude"][1]
            # proceed subset
            ds = select_subset(ds, lat=(min(lat0, lat1), max(lat0, lat1)))
            if debug:
                print("region_subset, latitude subsetted, ds:", ds)

        if "longitude" in regions_specs[region]["domain"]:
            lon0 = regions_specs[region]["domain"]["longitude"][0]
            lon1 = regions_specs[region]["domain"]["longitude"][1]

            # check original dataset longitude range
            lon_min = get_longitude(ds).min().values.item()
            lon_max = get_longitude(ds).max().values.item()

            # Check if longitude range swap is needed
            if min(lon0, lon1) < 0:
                # when subset region lon is defined in (-180, 180) range
                if min(lon_min, lon_max) < 0:
                    # if original data lon range is (-180, 180), no treatment needed
                    pass
                else:
                    # if original data lon range is (0, 360), convert and swap lon
                    ds = xc.swap_lon_axis(ds, to=(-180, 180))

            # proceed subset
            # ds = select_subset(ds, lon=(min(lon0, lon1), max(lon0, lon1)))
            ds = select_subset(ds, lon=(lon0, lon1))
            if debug:
                print("region_subset, longitude subsetted, ds:", ds)

    # return the same type
    if is_dataArray:
        return ds[data_var]
    else:
        return ds
