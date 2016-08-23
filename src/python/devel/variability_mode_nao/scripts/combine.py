# Combine multiple images into one.
#
# To install the Pillow module on Mac OS X:
#
# $ xcode-select --install
# $ brew install libtiff libjpeg webp little-cms2
# $ pip install Pillow
#
# Basement of this code is coming from https://gist.github.com/glombard/7cd166e311992a828675

from __future__ import print_function
from PIL import Image
import os
import math

modes = ['NAO', 'NAM', 'SAM', 'PNA', 'PDO']

#debug = True
debug = False

lr = False
#lr = True

pseudo = False
pseudo = True

if lr: 
  ftail1 = '_lr'
else:
  ftail1 = ''

if pseudo: 
  ftail2 = '_pseudo'
else: 
  ftail2 = ''

for mode in modes:

  print(mode)
  if mode == 'PDO': seasons = ['monthly']
  else: seasons = ['DJF', 'MAM', 'JJA', 'SON']

  for season in seasons:

    # List up all image files ---
    files = os.popen('ls ../'+mode+'/'+mode+'_*_eof1_'+season+'_*_1900-2005'+ftail1+ftail2+'.png').readlines()
    files = sorted(files, key=lambda s:s.lower()) # Sort list alphabetically, case-insensitive

    # Bring the observation to beginning ---
    ref_file = '../'+mode+'/'+mode + '_*_eof1_'+season+'_obs_1900-2005' + ftail1 + '.png'
    ref_file_list = os.popen('ls '+ref_file).readlines()
    try: 
      files.remove(ref_file_list[0])
    except: 
      pass
    files = ref_file_list + files

    # Calculate optimum row/col ---
    num = len(files)
    col = int(math.ceil(num * 0.4)) # round up
    if col > 6: col = 6
    row = num // col
    if num % col > 0: row = row + 1
    if debug: print(num, col, row)

    # Set thumbnail plot size ---
    hor = 400
    ver = 400

    # Open new image ---
    result = Image.new("RGB", (col*hor, row*ver), (255,255,255,0))

    # Append plots ---
    for index, file in enumerate(files):
      if debug: print(index, file)
      path = os.path.expanduser(file)
      #img = Image.open(path)
      img = Image.open(path.strip())
      img.thumbnail((hor, ver), Image.ANTIALIAS)
      x = index % col * hor
      y = index // col * ver
      w, h = img.size
      if debug: print('pos {0},{1} size {2},{3}'.format(x, y, w, h))
      result.paste(img, (x, y, x + w, y + h))

    # Save image ---
    #output_image = 'combined_image_'+mode+'_' + season + ftail1 + ftail2 + '.png'
    #result.save(os.path.expanduser('./'+output_image))
    output_image = 'Combined_'+mode+'_' + season + ftail1 + ftail2 + '.pdf'
    result.save(os.path.expanduser('./'+output_image),"PDF", resoultion = 100.0)
