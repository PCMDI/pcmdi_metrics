import xmltodict
import glob
import os
import sys
import xcdat as xc


def xcdat_open(infile):
    """
    Parameter
    ---------
    infile: 
        list of string, or string
        File(s) to open using xcdat
    Output
    ------
    ds:
        xcdat dataset
    """     
    if isinstance(infile, list):
        ds = xcdat.open_mfdataset(infile)
    else:
        if infile.split('.')[-1].lower() == 'xml':
            ds = xcdat_openxml(infile)
        else:
            ds = xcdat.open_dataset(infile)

    return ds


def xcdat_openxml(xmlfile):
    """
    Parameter
    ---------
    infile: 
        xml file to open using xcdat
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
        ds = xc.open_mfdataset(ncfile_list)
    else:
        ds = xc.open_dataset(ncfile_list[0])
    
    return ds
