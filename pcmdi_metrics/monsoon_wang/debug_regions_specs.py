import xcdat as xc
import xarray as xr
from pcmdi_metrics.io import load_regions_specs, region_subset
from typing import Union
import sys 
#from pcmdi_metrics.io import da_to_ds, get_longitude, select_subset
#from .xcdat_dataset_io import da_to_ds

def da_to_ds(d: Union[xr.Dataset, xr.DataArray], var: str = "variable") -> xr.Dataset:
    """Convert xarray DataArray to Dataset

    Parameters
    ----------
    d : Union[xr.Dataset, xr.DataArray]
        Input dataArray. If dataset is given, no process will be done
    var : str, optional
        Name of dataArray, by default "variable"

    Returns
    -------
    xr.Dataset
        xarray Dataset

    Raises
    ------
    TypeError
        Raised when given input is not xarray based variables
    """
    if isinstance(d, xr.Dataset):
        return d.copy()
    elif isinstance(d, xr.DataArray):
        return d.to_dataset(name=var).bounds.add_missing_bounds().copy()
    else:
        raise TypeError(
            "Input must be an instance of either xarrary.DataArray or xarrary.Dataset"
        )


#xr.show_versions()
#sys.exit()


regions_specs = load_regions_specs()
ds = xc.open_dataset("xd_mpi_obs.nc")

if isinstance(ds, xr.DataArray):
    is_dataArray = True
    print("True")
    ds = da_to_ds(ds, data_var)
    print("da_to_ds converted")


ds = ds.drop_vars(['time'])
ds = xc.swap_lon_axis(ds, to=(-180, 180))




mpi_obs_reg = region_subset(ds, "NAFM", data_var="pr", regions_specs=regions_specs)
