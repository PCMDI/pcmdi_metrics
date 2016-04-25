### ENSO REGIONS
region = {'Nino34':{'llat':-5., 'ulat':5.,  'llon':190., 'ulon':240.},
          'Nino3' :{'llat':-5., 'ulat':5.,  'llon':210., 'ulon':270.},
          'Nino4' :{'llat':-5., 'ulat':5.,  'llon':160., 'ulon':210.},
          'Nino12':{'llat':-10.,'ulat':0.,  'llon':270., 'ulon':280.},
          'TSA'   :{'llat':-20.,'ulat':0.,  'llon':-30., 'ulon':10. }, # Tropical Southern Atlantic
          'TNA'   :{'llat':5.5, 'ulat':23.5,'llon':302.5,'ulon':345.}, # Tropical Northern Atlantic
          'IO'    :{'llat':-15.,'ulat':15., 'llon':40.,  'ulon':110.}, # Indian Ocean
          }

def get_reg_selector(reg):
    lat1 = region[reg]['llat']
    lat2 = region[reg]['ulat']
    lon1 = region[reg]['llon']
    lon2 = region[reg]['ulon']
    reg_selector = cdutil.region.domain(latitude=(lat1,lat2,'ccb'),longitude=(lon1,lon2,'ccb'))
    return(reg_selector)
