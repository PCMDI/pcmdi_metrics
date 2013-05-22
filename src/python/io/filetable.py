#!/usr/local/uvcdat/bin/python

# Set up and index a table whose entries will be something like
#   file_id,  variable_id,  time_range,  lat_range,  lon_range,  level_range
# subject to change!

import sys, cdms2

class drange:
   def __init__( low, high, units ):
       self.lo = low
       self.hi = high
       self.units = units
   def overlaps_with( range2 ):
      if self.units!=range2.units:
         # >>> TO DO >>>> units conversion
         return False
      elif range2==None:
         # None means everything
         return True
      else:
         return self.hi>range2.lo and self.lo<range2.hi
       
class row:
    """This class identifies a file and contains the information essential to tell
    whether the file has data we want to graph: a variable and its domain information.
    There will be no more than that - if you want more information you can open the file.
    If the file has several variables, there will be several rows for the file."""
    # One can think of lots of cases where this is too simple, but it's a start.
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

    def __init__( self, filelist ):
        """filelist is a list of strings, each of which is the path to a file"""
        self._table = []     # will be built from the filelist, see below
        # We have two indices, one by file and one by variable.
        # the value is always a list of rows of the table.
        self._fileindex = {} # will be built as the table is built
        # The variable index is based on the CF standard name.  Why that?  We have to standardize
        # the variable in some way in order to have an API to the index, and CF standard names
        # cover just about anything we'll want to plot.  If something is missing, we'll need our
        # own standard name list.
        self._varindex = {} # will be built as the table is built
        print "filelist=",filelist,type(filelist)
        for filep in filelist.files:
            self.addfile( filep )
    def addfile( self, filep ):
        """Extract essential header information from a file filep,
        and put the results in the table.
        filep should be a string consisting of the path to the file."""
        fileid = filep
        dfile = cdms2.open( fileid )
        filesupp = get_datafile_support( dfile )
        vars = filesupp.interesting_variables()
        if len(vars)>0:
            timerange = filesupp.get_timerange()
            latrange = filesupp.get_latrange()
            lonrange = filesupp.get_lonrange()
            levelrange = filesupp.get_levelrange()
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
        dfile.close()
    def find_files( variable, time_range=None, lat_range=None, lon_range=None, level_range=None ):
       """This method is intended for creating a plot.
       This finds and returns a list of files needed to cover the supplied variable and time and space ranges.
       The returned list may contain more or less than requested, but will be the best available.
       The variable is a string, containing as a CF standard name, or equivalent.
       For ranges, None means you want all values."""
       candidates = self.varindex( variable_id )
       found = []
       for row in candidates:
          if time_range.overlaps_with( row.timerange ) and\
                 lat_range.overlaps_with( row.latrange ) and\
                 lon_range.overlaps_with( row.lonrange ) and\
                 level_range.overlaps_with( row.levelrange ):
             found.append( row )
       return found
            
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
    def __init__(dfile):
        """dfile is an open file"""
        # There are many possible interesting variables!
        # As we add plots to the system, we'll need to expand this list:
        self._all_interesting_standard_names = [
            'surface_air_pressure', 'surface_temperature' ]
        _dfile = dfile
    def interesting_variables():
        iv = []
        for var in _dfile.variables.keys():
            if getattr( _dfile[var], 'standard_name', None ) in\
                    self.all_interesting_standard_names:
                iv.append(var)
        return iv
    def get_timerange():
        time_bnds_name = _dfile.axes['time'].bounds
        lo = f[time_bnds_name][0][0]
        hi = f[time_bnds_name][-1][1]
        units = dfile.axes['time'].units
        return drange( lo, hi, units )
    def get_latrange():
        lat_bnds_name = _dfile.axes['lat'].bounds
        lo = f[lat_bnds_name][0][0]
        hi = f[lat_bnds_name][-1][1]
        units = dfile.axes['lat'].units
        return drange( lo, hi, units )
    def get_lonrange():
        lon_bnds_name = _dfile.axes['lon'].bounds
        lo = f[lon_bnds_name][0][0]
        hi = f[lon_bnds_name][-1][1]
        units = dfile.axes['lon'].units
        return drange( lo, hi, units )
    def get_levelrange():
        levelaxis = None
        for axis_name in dfile.axes.keys():
            axis = dfile[axis_name]
            if hasattr( axis, 'positive' ):
                # The CF Conventions specifies this as a way to detect a vertical axis.
                levelaxis = axis
                break
        if levelaxis==None:
            return None
        lo = min( levelaxis[0], levelaxis[-1] )
        hi = max( levelaxis[0], levelaxis[-1] )
        units = levelaxis.units
        return drange( lo, hi, units )

if __name__ == '__main__':
    if len( sys.argv ) > 1:
        from findfiles import *
        datafiles = treeof_datafiles( sys.argv[1] )
        print "datafiles=", datafiles
        filetable = basic_filetable( datafiles )
        print "filetable=", filetable
    else:
        print "usage: findfiles.py root"

