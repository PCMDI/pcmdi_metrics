import metrics
obs_dic = {'rlut':{'default':'CERES','alternate':'ERBE'},
           'rsut':{'default':'CERES','alternate':'ERBE'},
           'rlutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcre':{'default':'CERES','alternate':'ERBE'},
           'rlutcre':{'default':'CERES','alternate':'ERBE'},
           'pr':{'default':'GPCP','alternate':'CMAP'},
           'prw':{'default':'RSS'},
           'tas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ua':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'va':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'uas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'vas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ta':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'zg':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'tos':{'default':'HadISST'},
           'zos':{'default':'CNES_AVISO_L4'},
           'sos':{'default':'WOA09'},
            }

### ADDED BY PJG
obs_period = {'ERAINT':{'period':'000001-000012'},
              'CERES':{'period': '000001-000012'},
              'GPCP':{'period': '000001-000012'},
              'HadISST':{'period':'198001-200512'},
              'WOA09':  {'period':'177201-200812'},
              'CNES_AVISO_L4':{'period':'199201-200512'}
          }

class OBS(metrics.io.base.Base):
    def __init__(self,root,var,reference="default",period="198001-200512"):
        period = obs_period[obs_dic[var][reference]]['period']  ### ADDED BY PJG
        template = "%s/%s/ac/%s_%s_%%(period)_ac.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])
        metrics.io.base.Base.__init__(self,root,template)
        if var in ['tos','sos','zos']:
            self.realm = 'ocn'
        else:
            self.realm = 'atm'
        self.period = period
        self.ext = "nc"

