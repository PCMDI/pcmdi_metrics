import glob
import os
import sys

import xcdat
import xmltodict


def xcdat_open(infile, data_var=None):
    """
    Parameter
    ---------
    infile:
        list of string, or string
        File(s) to open using xcdat
    data_var:
        (Optional[str], optional) – The key of the non-bounds data variable to keep in the Dataset, alongside any existing bounds data variables, by default None.

    Output
    ------
    ds:
        xcdat dataset
    """
    if isinstance(infile, list):
        ds = xcdat.open_mfdataset(infile, data_var=data_var)
    else:
        if infile.split('.')[-1].lower() == 'xml':
            ds = xcdat_openxml(infile, data_var=data_var)
        else:
            ds = xcdat.open_dataset(infile, data_var=data_var)

    return ds


def xcdat_openxml(xmlfile, data_var=None):
    """
    Parameter
    ---------
    infile:
        xml file to open using xcdat
    data_var:
        (Optional[str], optional) – The key of the non-bounds data variable to keep in the Dataset, alongside any existing bounds data variables, by default None.

    Output
    ------
    ds:
        xcdat dataset
    """
    if not os.path.exists(xmlfile):
        sys.exit('ERROR: File not exist: {}'.format(xmlfile))

    with open(xmlfile) as fd:
        doc = xmltodict.parse(fd.read())

    ncfile_list = glob.glob(os.path.join(doc['dataset']['@directory'], '*.nc'))

    if len(ncfile_list) > 1:
        ds = xcdat.open_mfdataset(ncfile_list, data_var=data_var)
    else:
        ds = xcdat.open_dataset(ncfile_list[0], data_var=data_var)

    return ds
