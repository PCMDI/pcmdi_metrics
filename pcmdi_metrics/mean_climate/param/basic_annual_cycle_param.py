# VARIABLES TO USE
vars = ["pr"]
# vars = ['ua', 'ta']
vars = ["pr", "ua", "ta"]

# START AND END DATES FOR CLIMATOLOGY
start = "1981-01"
# end = '1983-12'
end = "2005-12"

# INPUT DATASET - CAN BE MODEL OR OBSERVATIONS
infile = "/work/lee1043/ESGF/E3SMv2/atmos/mon/cmip6.E3SMv2.historical.r1i1p1f1.mon.%(variable).xml"

# DIRECTORY WHERE TO PUT RESULTS
outfile = "clim/cmip6.historical.E3SMv2.r1i1p1.mon.%(variable).nc"
