import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

global climate_labels, climate_colors

climate_labels = {
    "0.0": "Undefined",
    "1.1": "Af",
    "1.2": "Am",
    "1.3": "Aw",
    "2.1": "BWh",
    "2.2": "BWk",
    "2.3": "BSh",
    "2.4": "BSk",
    "3.1": "Cfa",
    "3.2": "Cfb",
    "3.3": "Cfc",
    "3.4": "Cwa",
    "3.5": "Cwb",
    "3.6": "Cwc",
    "3.7": "Csa",
    "3.8": "Csb",
    "3.9": "Csc",
    "4.11": "Dfa",
    "4.12": "Dfb",
    "4.13": "Dfc",
    "4.14": "Dfd",
    "4.15": "Dwa",
    "4.16": "Dwb",
    "4.17": "Dwc",
    "4.18": "Dwd",
    "4.19": "Dsa",
    "4.2": "Dsb",
    "4.21": "Dsc",
    "4.22": "Dsd",
    "5.1": "ET",
    "5.2": "EF",
}

climate_colors = {  # Colors from wiki
    "Undefined": "#fafafa",
    "Af": "#0000ff",
    "Am": "#0079ff",
    "Aw": "#45adfc",
    "BWh": "#ff0000",
    "BWk": "#ff9797",
    "BSh": "#f5a701",
    "BSk": "#ffdd64",
    "Cfa": "#c9ff4f",
    "Cfb": "#64ff4f",
    "Cfc": "#30cc01",
    "Cwa": "#97ff97",
    "Cwb": "#64c964",
    "Cwc": "#2e972e",
    "Csa": "#ffff00",
    "Csb": "#cbcb02",
    "Csc": "#979700",
    "Dfa": "#01ffff",
    "Dfb": "#34c9ff",
    "Dfc": "#027f7f",
    "Dfd": "#00445f",
    "Dwa": "#adb3ff",
    "Dwb": "#5a79dd",
    "Dwc": "#4a4fb5",
    "Dwd": "#2e0088",
    "Dsa": "#ff00ff",
    "Dsb": "#c900c9",
    "Dsc": "#972e97",
    "Dsd": "#976497",
    "ET": "#b3b3b3",
    "EF": "#686868",
}


def convert_temperature_to_C(ds, varname):
    data_units = ds[varname].attrs["units"]  # K, F, or C
    unit_str = f"deg{data_units}"

    # Attach units with Pint
    t_units = Q_(ds[varname].data, unit_str)
    tC_arr = t_units.to("degC").magnitude
    ds_tC = xr.DataArray(
        tC_arr,
        coords=ds[varname].coords,
        dims=ds[varname].dims,
    ).to_dataset(name=varname)

    return ds_tC


def convert_precipitation_to_mm(ds, varname):
    data_units = ds[varname].attrs["units"]  # K, F, or C
    unit_str = f"{data_units}"

    # Attach units with Pint
    pr_units = Q_(ds[varname].data, unit_str)
    pr_arr = pr_units.to("mm").magnitude
    ds_pr = xr.DataArray(
        pr_arr,
        coords=ds[varname].coords,
        dims=ds[varname].dims,
    ).to_dataset(name=varname)

    return ds_pr


def standard_month_names(month_num_list):
    month_dict = {
        1: "JAN",
        2: "FEB",
        3: "MAR",
        4: "APR",
        5: "MAY",
        6: "JUNE",
        7: "JULY",
        8: "AUG",
        9: "SEP",
        10: "OCT",
        11: "NOV",
        12: "DEC",
    }

    month_names = [month_dict[month] for month in month_num_list]

    return month_num_list + month_names


def tropical(tas, pr, tas_var="tas", pr_var="pr"):
    tas = convert_temperature_to_C(tas, tas_var)
    pr = convert_precipitation_to_mm(pr, pr_var)

    trop_tf = xr.zeros_like(tas[tas_var].isel(month=0)).drop_vars("month")

    # Finding tropical locations
    t_thresh = 18  # Celcius

    t_cond = (tas[tas_var] > t_thresh).all(dim="month")
    # trop_tf = trop_tf.where(t_cond, 0)

    rf = (pr[pr_var] > 60).all(dim="month")
    mons = (~(pr[pr_var] > 60).all(dim="month")) & (
        pr[pr_var].min(dim="month") > (100 - pr[pr_var].sum(dim="month") / 25)
    )
    sav = (~(pr[pr_var] > 60).all(dim="month")) & (
        pr[pr_var].min(dim="month") < (100 - pr[pr_var].sum(dim="month") / 25)
    )

    trop_tf = trop_tf.where(~(t_cond & rf), 1.1)
    trop_tf = trop_tf.where(~(t_cond & mons), 1.2)
    trop_tf = trop_tf.where(~(t_cond & sav), 1.3)

    return trop_tf


def desert(tas, pr, tas_var="tas", pr_var="pr"):
    tas = convert_temperature_to_C(tas, tas_var)
    pr = convert_precipitation_to_mm(pr, pr_var)

    desert_tf = xr.zeros_like(tas[tas_var].isel(month=0)).drop_vars("month")
    polar_cond = (tas[tas_var] < 10).all(dim="month")
    # min_temp = tas[tas_var].min(dim="month")
    mean_temp = tas[tas_var].mean(dim="month")

    pr_thresh = tas[tas_var].mean(dim="month") * 20 + 280

    spring_summer_precip = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([4, 5, 6, 7, 8, 9])))
        .sum(dim="month")
    )
    total_precip = pr[pr_var].sum(dim="month")
    frac_spring_summer = spring_summer_precip / total_precip

    pr_thresh = pr_thresh.where(frac_spring_summer > 0.70, pr_thresh - 140)
    pr_thresh = pr_thresh.where(frac_spring_summer > 0.30, pr_thresh - 140)

    arid = total_precip < 0.5 * pr_thresh
    semi_arid = (total_precip > 0.5 * pr_thresh) & (total_precip < pr_thresh)

    hot_arid = arid & (mean_temp > 18)
    cool_arid = arid & (mean_temp < 18)
    hot_semi_arid = semi_arid & (mean_temp > 18)
    cool_semi_arid = semi_arid & (mean_temp < 18)

    desert_tf = desert_tf.where(~((~polar_cond) & hot_arid), 2.1)
    desert_tf = desert_tf.where(~((~polar_cond) & cool_arid), 2.2)
    desert_tf = desert_tf.where(~((~polar_cond) & hot_semi_arid), 2.3)
    desert_tf = desert_tf.where(~((~polar_cond) & cool_semi_arid), 2.4)

    return desert_tf


def temperate(tas, pr, desert_tf, tas_var="tas", pr_var="pr"):
    tas = convert_temperature_to_C(tas, tas_var)
    pr = convert_precipitation_to_mm(pr, pr_var)

    temp_tf = xr.zeros_like(tas[tas_var].isel(month=0)).drop_vars("month")
    min_temp = tas[tas_var].min(dim="month")
    max_temp = tas[tas_var].max(dim="month")
    temp_cond = (min_temp > 0) & (min_temp < 18) & (max_temp > 10)  # All in Celsius
    thresh_10_sum = (tas[tas_var] > 10).sum(dim="month")

    wettest_month_summer = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([6, 7, 8])))
        .max(dim="month")
    )
    driest_month_winter = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([1, 2, 12])))
        .min(dim="month")
    )
    wettest_month_winter = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([1, 2, 12])))
        .max(dim="month")
    )
    driest_month_summer = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([6, 7, 8])))
        .min(dim="month")
    )

    # Humid Subtropical
    humid_sub = (min_temp > 0) & (max_temp > 22) & (thresh_10_sum >= 4)

    # Temperate Oceanic
    temp_ocean = (min_temp > 0) & (max_temp < 22) & (thresh_10_sum >= 4)

    # Sub-Polar Oceanic
    sub_ocean = (
        (min_temp > 0) & (max_temp < 22) & (thresh_10_sum >= 1) & (thresh_10_sum < 4)
    )

    # Monsoon-Influenced Humid Subtropical
    mon_humid_sub = (
        (min_temp > 0)
        & (max_temp > 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Monsoon-Influenced Temperature Subtropical
    mon_temp_ocean = (
        (min_temp > 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Monsoon-influenced Subpolar Oceanic
    mon_sub_ocean = (
        (min_temp > 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 1)
        & (thresh_10_sum < 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Hot-summer Mediterranean
    hot_medit = (
        (min_temp > 0)
        & (max_temp > 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_winter > (3 * driest_month_summer))
        & (driest_month_summer < 40)
    )

    # Warm-summer Mediterranean
    warm_medit = (
        (min_temp > 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_winter > (3 * driest_month_summer))
        & (driest_month_summer < 40)
    )

    # Cold-summer Mediterranean
    cold_medit = (
        (min_temp > 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 1)
        & (thresh_10_sum < 4)
        & (wettest_month_winter > 3 * driest_month_summer)
        & (driest_month_summer < 40)
    )

    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & humid_sub), 3.1)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & temp_ocean), 3.2)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & sub_ocean), 3.3)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & mon_humid_sub), 3.4)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & mon_temp_ocean), 3.5)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & mon_sub_ocean), 3.6)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & hot_medit), 3.7)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & warm_medit), 3.8)
    temp_tf = temp_tf.where(~((~desert_tf) & temp_cond & cold_medit), 3.9)

    return temp_tf.where(temp_tf > 0)


def continental(tas, pr, desert_tf, tas_var="tas", pr_var="pr"):
    tas = convert_temperature_to_C(tas, tas_var)
    pr = convert_precipitation_to_mm(pr, pr_var)

    cont_tf = xr.zeros_like(tas[tas_var].isel(month=0)).drop_vars("month")
    min_temp = tas[tas_var].min(dim="month")
    max_temp = tas[tas_var].max(dim="month")
    cont_cond = (min_temp < 0) & (max_temp > 10)  # All in Celsius
    thresh_10_sum = (tas[tas_var] > 10).sum(dim="month")

    wettest_month_summer = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([6, 7, 8])))
        .max(dim="month")
    )
    driest_month_winter = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([1, 2, 12])))
        .min(dim="month")
    )
    wettest_month_winter = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([1, 2, 12])))
        .max(dim="month")
    )
    driest_month_summer = (
        pr[pr_var]
        .isel(month=pr.month.isin(standard_month_names([6, 7, 8])))
        .min(dim="month")
    )

    # Hot Humid Subtropical
    hot_humid_cont = (min_temp < 0) & (max_temp > 22) & (thresh_10_sum >= 4)

    # Warm Humid Subtropical
    warm_humid_cont = (min_temp < 0) & (max_temp < 22) & (thresh_10_sum >= 4)

    # Sub-Artic
    sub_arctic = (min_temp < 0) & (thresh_10_sum >= 1) & (thresh_10_sum < 4)

    # Extreme sub-arctic
    ext_sub_arctic = (min_temp < -38) & (thresh_10_sum >= 1) & (thresh_10_sum < 4)

    # Monsoon-Influenced Hot Humid Subtropical
    mon_hot_humid_cont = (
        (min_temp < 0)
        & (max_temp > 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Monsoon-influenced warm-summer humid continental
    mon_warm_humid_cont = (
        (min_temp < 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Monsoon-influenced subarctic
    mon_sub_arctic = (
        (min_temp < 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 1)
        & (thresh_10_sum < 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Monsoon-influenced Extreme sub-arctic
    mon_ext_sub_arctic = (
        (min_temp < -38)
        & (thresh_10_sum >= 1)
        & (thresh_10_sum < 4)
        & (wettest_month_summer > 10 * driest_month_winter)
    )

    # Hot-summer Mediterranean Continental (Dsa)
    hot_medit_cont = (
        (min_temp < 0)
        & (max_temp > 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_winter > (3 * driest_month_summer))
        & (driest_month_summer < 30)
    )

    # Warm-summer Mediterranean (Dsb)
    warm_medit_cont = (
        (min_temp < 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 4)
        & (wettest_month_winter > (3 * driest_month_summer))
        & (driest_month_summer < 30)
    )

    # Mediterranean Subarctic (Dsc)
    sub_arctic_medit = (
        (min_temp < 0)
        & (max_temp < 22)
        & (thresh_10_sum >= 1)
        & (thresh_10_sum < 4)
        & (wettest_month_winter > 3 * driest_month_summer)
        & (driest_month_summer < 30)
    )

    # Mediterranean Extremem Subarctic (Dsd)
    ext_sub_arctic_medit = (
        (min_temp < -38)
        & (thresh_10_sum >= 1)
        & (thresh_10_sum < 4)
        & (wettest_month_winter > 3 * driest_month_summer)
        & (driest_month_summer < 30)
    )

    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & hot_humid_cont), 4.11)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & warm_humid_cont), 4.12)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & sub_arctic), 4.13)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & ext_sub_arctic), 4.14)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & mon_hot_humid_cont), 4.15)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & mon_warm_humid_cont), 4.16)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & mon_sub_arctic), 4.17)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & mon_ext_sub_arctic), 4.18)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & hot_medit_cont), 4.19)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & warm_medit_cont), 4.2)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & sub_arctic_medit), 4.21)
    cont_tf = cont_tf.where(~((~desert_tf) & cont_cond & ext_sub_arctic_medit), 4.22)

    return cont_tf.where(cont_tf > 0)


def polar(tas, pr, tas_var="tas", pr_var="pr"):
    tas = convert_temperature_to_C(tas, tas_var)  # Normalizing units
    pr = convert_precipitation_to_mm(pr, pr_var)

    """ Polar and alpine climates has every month of the year with an average temperature below 10 °C (50 °F).[9][11]
    ET = Tundra climate; average temperature of warmest month between 0 °C (32 °F) and 10 °C (50 °F).[9][11]
    EF = Ice cap climate; eternal winter, with all 12 months of the year with average temperatures below 0 °C (32 °F).[9][11]
    """
    polar_tf = xr.zeros_like(tas[tas_var].isel(month=0)).drop_vars("month")
    max_temp = tas[tas_var].max(dim="month")
    polar_cond = max_temp < 10

    tundra_cond = (max_temp > 0) & (max_temp < 10)
    ice_cap_cond = max_temp < 0

    polar_tf = polar_tf.where(~(polar_cond & tundra_cond), 5.1)
    polar_tf = polar_tf.where(~(polar_cond & ice_cap_cond), 5.2)

    return polar_tf.where(polar_tf != 0)


def koppen(tas, pr, tas_var="tas", pr_var="pr"):
    """
    Returns climate classification indices and corresponding colormap
    """

    climate_cat = xr.zeros_like(tas[tas_var].isel(month=0)).drop_vars("month")

    tropical_tf = tropical(tas, pr, tas_var=tas_var, pr_var=pr_var)
    desert_tf = desert(tas, pr, tas_var=tas_var, pr_var=pr_var)
    temp_tf = temperate(
        tas, pr, tas_var=tas_var, pr_var=pr_var, desert_tf=desert_tf != 0
    )
    cont_tf = continental(
        tas, pr, tas_var=tas_var, pr_var=pr_var, desert_tf=desert_tf != 0
    )
    polar_tf = polar(tas, pr, tas_var=tas_var, pr_var=pr_var)

    # Assign values in order of priority (tropical > desert > temperate > continental > polar)

    # Assign tropical
    climate_cat = xr.where(
        (climate_cat == 0) & (tropical_tf.notnull()), tropical_tf, climate_cat
    )
    # Assign desert
    climate_cat = xr.where(
        (climate_cat == 0) & (desert_tf.notnull()), desert_tf, climate_cat
    )
    # Assign temperate
    climate_cat = xr.where(
        (climate_cat == 0) & (temp_tf.notnull()), temp_tf, climate_cat
    )
    # Assign continental
    climate_cat = xr.where(
        (climate_cat == 0) & (cont_tf.notnull()), cont_tf, climate_cat
    )
    # Assign polar
    climate_cat = xr.where(
        (climate_cat == 0) & (polar_tf.notnull()), polar_tf, climate_cat
    )

    climate_cat = climate_cat.astype(str)
    # climate_codes = list(climate_labels.keys())
    used_codes = np.unique(climate_cat.data)

    filtered_codes = [code for code in climate_labels if code in used_codes]
    filtered_labels = [climate_labels[code] for code in filtered_codes]
    filtered_colors = [climate_colors[label] for label in filtered_labels]

    code_to_index = {code: idx for idx, code in enumerate(filtered_codes)}
    climate_cat_indices = np.vectorize(code_to_index.get)(climate_cat.astype(str))
    cmap = plt.matplotlib.colors.ListedColormap(filtered_colors)

    climate_index = xr.DataArray(
        data=climate_cat_indices,
        dims=["lat", "lon"],
        coords={"lat": climate_cat["lat"], "lon": climate_cat["lon"]},
    )

    return climate_index, cmap, filtered_labels, filtered_colors
