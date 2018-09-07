from __future__ import print_function
import os
import glob

pathin = '/work/lee1043/ESGF/xmls/cmip5/historical/day/pr'
lst = glob.glob(os.path.join(pathin, '*.xml'))
print(lst)

models = set([])
model_runs = set([])

for l in sorted(lst):
    print(l)
    mip = l.split('/')[-1].split('.')[0]
    model = l.split('/')[-1].split('.')[1]
    exp = l.split('/')[-1].split('.')[2]
    run = l.split('/')[-1].split('.')[3]
    models.add(model)
    model_runs.add(model+'_'+run)

print('num models: ', len(list(models)))
print('models: ', sorted(list(models), key=lambda s: s.lower()))
print('num model_runs: ', len(list(model_runs)))
print('model_runs: ', sorted(list(model_runs), key=lambda s: s.lower()))
