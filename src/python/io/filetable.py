#!/usr/bin/python

# Set up and index a table whose entries will be something like
#   file_id,  variable_id,  time_range,  lat_range,  lon_range,  level_range
# subject to change!

class range:
   def __init__( low, high, units ):
       self.lo = low
       self.hi = high
       self.units = units
       
class row:
    """This class identifies a file and contains the information essential to tell
    whether the file has data we want to graph: a variable and its domain information.
    There will be no more than that - if you want more information you can open the file.
    If the file has several variables, there will be several rows for the file."""
    def __init__( fileid, variableid, timerange, latrange, lonrange, levelrange=None ):
        self.fileid = fileid
        self.variableid = variableid
        self.timerange = timerange
        self.latrange = latrange
        self.lonrange = lonrange
        self.levelrange = levelrange


def get_datafile_support( dfile ):
    """dfile is an open datafile.  If the file type is recognized,
    then this will return an object with methods needed to support that file type."""
    if hasattr(dfile,'Conventions') and dfile.Conventions[0:1]=='CF':
        return CF_support( dfile )
    else:
        return No_support()

class basic_filetable:
    """Conceptually a file table is just a list of rows; but we need to attach some methods,
    which makes it a class.  Moreover, indices for the table are in this class.
    Different file types will require different methods,
    and auxiliary data."""

    def __init__( filelist ):
        """filelist is a list of strings, each of which is the path to a file"""
        self._table = []     # will be built from the filelist, see below
        # We have two indices, one by file and one by variable.
        # the value is always a list of rows of the table.
        self._fileindex = {} # will be built as the table is built
        self._varindex = {} # will be built as the table is built
        for filep in filelist:
            self.addfile( filep )
    def addfile( filep ):
        """Extract essential header information from a file filep,
        and put the results in the table.
        filep should be a string consisting of the path to the file."""
        fileid = filep
        dfile = cdms2.open( fileid )
        filesupp = get_datafile_support( dfile )
        timerange = filesupp.get_timerange()
        latrange = filesupp.get_latrange()
        lonrange = filesupp.get_lonrange()
        levelrange = filesupp.get_levelrange()
        vars = filesupp.interesting_variables()
        for var in vars:
            variableid = var
            newrow = row( fileid, variableid, timerange, latrange, lonrange,
                          levelrange )
            self._table.append( newrow )
            if self.fileindex.haskey(fileid):
                self._fileindex[fileid].append(newrow)
            else:
                self._fileindex[fileid] = [newrow]
            if self._varindex.haskey(variableid):
                self._varindex[variableid].append(newrow)
            else:
                self._varindex[variableid] = [newrow]
            
class basic_support:
    """Children of this class contain methods which support specific file types,
    and are used to build the file table.  Maybe later we'll put here methods
    to support other functionality."""
    def get_timerange(): return None
    def get_latrange(): return None
    def get_lonrange(): return None
    def get_levelrange(): return None
    def interesting_variables(): return []

class No_support(basic_support):
    """Any unsupported file type gets this one."""

class CF_support(basic_support):
    """NetCDF file conforming to the CF Conventions."""

