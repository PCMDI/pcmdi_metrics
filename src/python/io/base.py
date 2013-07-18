import json
import cdms2

class Base(genutil.StribgConstructor):
    def __init__(self,root,file_template):
        genutil.StringConstructor.__init__(self,root+"/"+file_template)
        self.targetGrid = None
    def get(self,var,*args,**kargs):
        self.var = var
        if self.targetGrid is None:
            return cdms2.open(self())(var,*args,**kargs)
        else:
            return cdms2.open(self())(var,*args,**kargs).regrid(self.targetGrid,regridTool=self.regridTool,regridMethod=self.regridMethod, coordSys='deg', diag = {},periodicity=1)
    def setTargetGrid(self,target,regridTool="esmf",regridMethod="linear"):
        self.regridTool = regridTool
        self.regridMethod = regridMethod
        if target=="2.5x2.5":
            self.targetGrid = cdms2.createUniformGrid(-88.875,72,2.5,0,144,2.5)
        elif cdms2.isGrid(target):
            self.targetGrid = target
        else:
            raise RunTimeError,"Unknown grid: %s" % target
    def write(self,data,type="json",*args,**kargs):
        fnm = self()+".%s" % type
        try:
            os.mkdir(os.path.split(fnm)[0])
        except:
            pass
        if not os.path.exists(os.path.split(fnm)[0]):
            raise RuntimeError, "Could not create output directory: %s" % (os.path.split(fnm)[0])
        if type.lower() == "json":
            f=open(fnm,"w")
            json.dump(data,f,*args,**kargs)            
        elif type.lower() in ["asc","ascii","txt"]:
            f=open(fnm,"w")
            for k in data.keys():
                f.write("%s  %s \n" % (k,data[k]))
        elif type.lower == "nc":
            f=cdms2.open(fnm,"w")
            f.write(data,*args,**kargs)
        else:
            raise RuntimeError,"Unknown type: %s" % type
        f.close()

    
