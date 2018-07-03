

vars = ['pr','rlut', 'rsut','rsutcs','rlutcs','tas','prw','tauu','tauv','uas','vas','psl','hus','ta','ua','va', 'zg']
vars = ['rlut']

realm = 'atm'
MIP = 'cmip5'
exp = 'historical'

modpath = '/work/cmip5-test/' + exp + '/' + realm + '/mo_new/'
modpath = '/work/cmip5/' + exp  + '/' + realm + '/mo/'


filename_template = MIP + '.$MODEL' + '.' + exp + '.r1i1p1.mo.' + realm + '.Amon.' + '$VARIABLE' + '.ver-*.latestX.xml'

climout = 'cmip5clims_newsystem_' + exp + '_nocmor/'  

results_dir = climout

start_month = 0
start_year = 1981
end_month = 11
end_year = 2005
