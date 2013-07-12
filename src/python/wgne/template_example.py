import genutil

template = "%(root)/%(var)_%(table).%(ext)"

T=genutil.StringConstructor(template)

T.ext='xml'
T.var='pr'
T.root='/work/cmip5'
T.table = 'Amon'

nm = T()
print nm
print T.keys()

print T.reverse(nm)

