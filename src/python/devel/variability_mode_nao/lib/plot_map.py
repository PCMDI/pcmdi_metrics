def plot_map(mode, model, syear, eyear, season, eof1, frac1, output_file_name):

  import vcs
  import string

  # Create canvas
  canvas = vcs.init(geometry=(900,800))
  canvas.open()
  canvas.drawlogooff()
  template = canvas.createtemplate()

  # Turn off no-needed information -- prevent overlap
  template.blank(['title','mean','min','max','dataname','crdate','crtime',
        'units','zvalue','tvalue','xunits','yunits','xname','yname'])

  canvas.setcolormap('bl_to_darkred')
  iso = canvas.createisofill()
  iso.levels = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
  iso.ext_1 = 'y' # control colorbar edge (arrow extention on/off)
  iso.ext_2 = 'y' # control colorbar edge (arrow extention on/off)
  cols = vcs.getcolors(iso.levels)
  cols[6] = 139 # Adjsut to light red
  iso.fillareacolors = cols
  p = vcs.createprojection()
  if mode == 'nam':
    ptype = int('-3')
  elif mode == 'nao':
    ptype = 'lambert azimuthal'
  p.type = ptype
  iso.projection = p
  xtra = {}
  xtra['latitude'] = (90.0,0.0)
  eof1 = eof1(**xtra) # For NH projection 
  canvas.plot(eof1,iso,template)

  #-------------------------------------------------
  # Title
  #- - - - - - - - - - - - - - - - - - - - - - - - 
  plot_title = vcs.createtext()
  plot_title.x = .5
  plot_title.y = .97
  plot_title.height = 23
  plot_title.halign = 'center'
  plot_title.valign = 'top'
  plot_title.color='black'
  frac1 = round(float(frac1*100.),1) # % with one floating number
  plot_title.string = str.upper(mode)+': '+str.upper(model)+'\n'+str(syear)+'-'+str(eyear)+' '+str.upper(season)+', '+str(frac1)+'%'
  canvas.plot(plot_title)

  #-------------------------------------------------
  # Drop output as image file (--- vector image?)
  #- - - - - - - - - - - - - - - - - - - - - - - - - 
  canvas.png(output_file_name+'.png')

  if not test:
    canvas.close()
