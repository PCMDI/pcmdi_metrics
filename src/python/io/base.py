import json
import cdms2
import MV2
import genutil
import os
import pcmdi_metrics
import cdat_info
import hashlib

value = 0
cdms2.setNetcdfShuffleFlag(value) ## where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value) ## where value is either 0 or 1
cdms2.setNetcdfDeflateLevelFlag(value) ## where value is a integer between 0 and 9 included

class Base(genutil.StringConstructor):
    def __init__(self,root,file_template):
        genutil.StringConstructor.__init__(self,root+"/"+file_template)
        self.targetGrid = None
        self.mask = None
        self.targetMask = None

    def __call__(self):
      return os.path.abspath(genutil.StringConstructor.__call__(self))

    def get(self,var,varInFile=None,*args,**kargs):
        self.variable = var
        if varInFile is None:
            varInFile = var
        ## First extract data
        f = cdms2.open(os.path.abspath(self()))
        out = f(varInFile,*args,**kargs)
        f.close()

        ## Now are we looking at a region in particular?
        if self.mask is not None:
          if self.mask.shape != out.shape:
            dum, msk = genutil.grower(out,self.mask)
          else:
            msk = self.mask
          out = MV2.masked_where(msk,out)
        if self.targetGrid is not None:
            out=out.regrid(self.targetGrid,regridTool=self.regridTool,regridMethod=self.regridMethod, coordSys='deg', diag = {},periodicity=1)
            if self.targetMask is not None:
              if self.targetMask.shape != out.shape:
                dum, msk = genutil.grower(out,self.targetMask)
              else:
                msk = self.targetMask
              out = MV2.masked_where(msk,out)
        return out

    def setTargetGrid(self,target,regridTool="esmf",regridMethod="linear"):
        self.regridTool = regridTool
        self.regridMethod = regridMethod
        if target=="2.5x2.5":
            self.targetGrid = cdms2.createUniformGrid(-88.875,72,2.5,0,144,2.5)
            self.targetGridName = target
        elif cdms2.isGrid(target):
            self.targetGrid = target
            self.targetGridName = target
        else:
            raise RunTimeError,"Unknown grid: %s" % target

    def write(self,data, type="json", mode="w", *args, **kargs):
        fnm = os.path.abspath(self())+".%s" % type
        try:
            os.makedirs(os.path.split(fnm)[0])
        except:
            pass
        if not os.path.exists(os.path.split(fnm)[0]):
            raise RuntimeError, "Could not create output directory: %s" % (os.path.split(fnm)[0])
        if type.lower() == "json":
            f=open(fnm,mode)
            data["metrics_git_sha1"] = pcmdi_metrics.__git_sha1__
            data["uvcdat_version"] = cdat_info.get_version()
            json.dump(data,f,*args,**kargs)            
            f.close()
        elif type.lower() in ["asc","ascii","txt"]:
            f=open(fnm,mode)
            for k in data.keys():
                f.write("%s  %s \n" % (k,data[k]))
            f.close()
        elif type.lower() == "nc":
            f=cdms2.open(fnm,mode)
            f.write(data,*args,**kargs)
            f.metrics_git_sha1 = pcmdi_metrics.__git_sha1__
            f.uvcdat_version = cdat_info.get_version()
            f.close()
        else:
            raise RuntimeError,"Unknown type: %s" % type

    def hash(self, blocksize=65536):
      afile=open(self())
      buf = afile.read(blocksize)
      hasher = hashlib.md5()
      while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
      afile.close()
      return hasher.hexdigest()

