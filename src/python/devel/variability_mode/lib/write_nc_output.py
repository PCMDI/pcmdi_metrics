def write_nc_output(output_file_name,
                    eofMap, pc, frac, slopeMap, interceptMap):

  import cdms2 as cdms
  fout = cdms.open(output_file_name+'.nc','w')
  fout.write(eofMap,id='eof')
  fout.write(slopeMap,id='slope')
  fout.write(interceptMap,id='intercept')
  fout.write(pc,id='pc')
  fout.write(frac,id='frac')
  fout.close()
