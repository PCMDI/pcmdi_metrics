def plot_map(mode, model, syear, eyear, season, eof1, frac1, output_file_name):

  import vcs
  import string

  canvas = vcs.init(geometry=(900,800),bg=1) # Plotting in background mode

  canvas.drawlogooff()
  template = canvas.createtemplate()

  # Turn off no-needed information -- prevent overlap
  template.blank(['title','mean','min','max','dataname','crdate','crtime',
        'units','zvalue','tvalue','xunits','yunits','xname','yname'])

  canvas.setcolormap('bl_to_darkred')
  iso = canvas.createisofill()
  if string.split(mode,'_')[0] == 'PDO':
    iso.levels = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
  else:
    iso.levels = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
  iso.ext_1 = 'y' # control colorbar edge (arrow extention on/off)
  iso.ext_2 = 'y' # control colorbar edge (arrow extention on/off)
  cols = vcs.getcolors(iso.levels, range(16,240))
  cols[6] = 139 # Adjsut to light red
  iso.fillareacolors = cols
  iso.missing = 0
  p = vcs.createprojection()
  if mode == 'NAM' or mode == 'SAM':
    p.type = int('-3')
  elif mode == 'NAO' or mode == 'PNA' or mode == 'PDO' or mode == 'AMO':
    p.type = 'lambert'
  elif mode == 'PDO_teleconnection' or mode == 'PDO_pseudo_teleconnection':
    p.type = 'robinson' 
  else:
    p.type = int('-3')
  iso.projection = p
  xtra = {}
  if mode == 'PDO_teleconnection' or mode == 'PDO_pseudo_teleconnection':
    xtra = {}
  elif mode == 'SAM' or mode == 'SAM_teleconnection' or mode == 'SAM_pseudo_teleconnection':
    xtra['latitude'] = (-90.0,0.0) # For Southern Hemisphere
  else: 
    xtra['latitude'] = (90.0,0.0) # For Northern Hemisphere
  eof1 = eof1(**xtra)
  canvas.plot(eof1,iso,template)

  #-------------------------------------------------
  # Title
  #- - - - - - - - - - - - - - - - - - - - - - - - 
  plot_title = vcs.createtext()
  plot_title.x = .5
  plot_title.y = .97
  plot_title.height = 30
  plot_title.halign = 'center'
  plot_title.valign = 'top'
  plot_title.color='black'
  if frac1 != -999: percentage = str(round(float(frac1*100.),1)) + '%' # % with one floating number
  else: percentage = ''
  plot_title.string = mode+': '+model+'\n'+str(syear)+'-'+str(eyear)+' '+season+' '+percentage
  canvas.plot(plot_title)

  #-------------------------------------------------
  # Drop output as image file (--- vector image?)
  #- - - - - - - - - - - - - - - - - - - - - - - - - 
  canvas.png(output_file_name+'.png')

  canvas.clear()
  canvas.close()
