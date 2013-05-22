#!/usr/local/uvcdat/bin/python

# The user provides some minimal specification of the data he wants analyzed.
# Our goal here is to find all the data files which comprise that data.

import operator, os, functools, sys

# Datafile Filters: Make one class for each atomic operation, e.g. check that it
# is a file (as opposed to directory, etc.), check the file extension,
# various other filename checks; check the file type (from its contents).
# The __call__() method applies the filter to a single candidate file.
# You will be able to combine filters by constructing an 'and','or',
# or 'not' object.

class basic_filter:
    def __call__( self, filen ):
        return True

class basic_binary_filter:
    def __init__( f1, f2 ):
        _f1 = f1
        _f2 = f2

# If we were to decide to require that all datafiles functions put nothing but files
# into the files variable, then the following filter would be pointless:
class f_isfile(basic_filter):
    def __call__( self, filen ):
        return os.path.isfile(filen)

class f_nc(basic_filter):
    """filter for *.nc files"""
    def __call__( self, filen ):
        return os.path.splitext(filen).lower()=='nc'

class f_and(basic_binary_filter):
    def __call__( self, filen ):
        return _f1(filen) and _f2(filen)

# Thus a filter for "is a real file, with a .nc extension" is:
#       f = f_and( f_nc(), f_isfile() )
# Or we could do that in a class by:
class f_ncfile(f_and):
    def __init__():
        f_and.__init__( f_nc(), f_isfile() )


# Datafiles, the core of this module.
# Other datafiles classes may have different __init__ methods, and maybe
# even a __call__ or other methods.  For example, we may look
# into multiple directories.  We may be able to automatically
# identify these directories on a machine-dependent basis (implemented
# with a mixin maybe) given portable specifications like a CMIP5
# dataset id.  And we may want to filter the directory as well
# as the file.
# But a simple treeof_datafiles() will be enough for testing and demos.



class basic_datafiles:
    def __init__(self):
        self.files = []  # Not _files; this may be referenced from outside the class.
    def __repr__(self):
        return self.files.__repr__()

class treeof_datafiles (basic_datafiles):
    def __init__( self, root, filt=basic_filter() ):
        """Finds all the data files in the directory tree below root.
        root can be a string representing a directory, or a list
        of such strings.
        The second argument is an optional filter, of type basic_filter."""
        basic_datafiles.__init__(self)
        if type(root)==list:
            pass
        elif type(root)==str:
            root = [root]
        else:
            raise Error("don't understand root directory %s"%root)
        for r in root:
            self.getdatafiles(r,filt)


    def getdatafiles( self, root, filt ):
        """returns all data files under a single root directory"""
        for dirpath,dirname,filenames in os.walk(root):
            dirpath = os.path.abspath(dirpath)
            self.files += [ os.path.join(dirpath,f) for f in filenames if filt(f) ]
        return self.files


if __name__ == '__main__':
    if len( sys.argv ) > 1:
        datafiles = treeof_datafiles( sys.argv[1] )
        print datafiles
    else:
        print "usage: findfiles.py root"

