import argparse
from argparse import RawTextHelpFormatter
import sys
import string

def AddParserArgument(parser):
  parser.add_argument("-m", "--model",
                      type = str,
                      help = "Give specific model name or 'all'\n"
                             "(CAUTION!!: Case Sensitive for specific model name)")
  parser.add_argument("-v", "--variability_mode",
                      type = str,
                      help = "Mode of variability: NAM, NAO, SAM, PNA, PDO\n"
                             "where:\n"
                             "      NAM: Northern Annular Mode\n"
                             "      NAO: Northern Atlantic Oscillation\n"
                             "      SAM: Southern Annular Mode\n"
                             "      PNA: Pacific North American Pattern\n"
                             "      PDO: Pacific Decadal Oscillation\n"
                             "(Case Insensitive)")
  parser.add_argument("-s", "--season",
                      type = str,
                      default = 'DJF',
                      help = "Season for mode of variability\n"
                             "- Available options: DJF (default), MAM, JJA, SON or all\n"
                             "- Variability mode PDO's definition is not based on season,\n"
                             "  thus season will be corrected to 'monthly' automatically\n"
                             "(Case Insensitive)")
  parser.add_argument("-y", "--year",
                      default = '1900,2005',
                      help = "Start and end year for the analysis time period\n"
                             "- Usage: 1900,2005 (default)\n"
                             "  (CAUTION: DO NOT INCLUDE SPACE btw numbers)")
  parser.add_argument("-r", "--realization",
                      type = str,
                      default = 'r1i1p1',
                      help = "Consider all accessible realizations as idividual\n"
                             "- r1i1p1: default, consider only one member which is 'r1i1p1'\n"
                             "          Or, you can give specific realization, e.g, r3i1p1'\n"
                             "- all: consider all available realizations")
  parser.add_argument("-eofn_o", "--eof_ordinal_number_for_observation",
                      type = int,
                      default = '1',
                      help = "EOF mode from observation as reference\n"
                             "Default is 1, which takes first variance mode of EOF")
  parser.add_argument("-eofn_m", "--eof_ordinal_number_for_model",
                      type = int,
                      default = '1',
                      help = "EOF mode from model\n"
                             "Default is 1, which takes first variance mode of EOF")
  parser.add_argument("-b", "--basedir",
                      type = str,
                      help = "Root directory below which subdirectories of individual simulations are expected")
  parser.add_argument("-o", "--outdir",
                      type = str,
                      default = './result',
                      help = "Output directory (default = ./result)\n"
                             "(CAUTION!!: Case Sensitive)")
  parser.add_argument("-d", "--debug",
                      type = bool,
                      default = False,
                      help = "Option for debug: False (defualt) or True")
  return parser

def ModelCheck(model):
  if model is None:
    parser.error('MODEL is NOT defined')
  else:
    if model.upper() == 'ALL':
      print 'consider entire models'
      models = [ 'all' ] # need to catch all available models here....
    else:
      models = [ args.model ]
    return models
  
def VariabilityModeCheck(mode):
  if mode is None:
    parser.error('VARIABILITY_MODE is NOT defined')
  else:
    if mode.upper() not in ['NAM', 'NAO', 'SAM', 'PNA', 'PDO']:
      parser.error('Given VARIABILITY_MODE, "'+mode+'", is NOT correct. Please refer help document by using "-h" option')
    mode = string.upper(mode)
    return mode

def SeasonCheck(season):
  if season.upper() == 'ALL':
    seasons = [ 'DJF', 'MAM', 'JJA', 'SON' ]
  else:
    if mode in ['NAM', 'NAO', 'SAM', 'PNA' ]:
      if season.upper() in [ 'DJF', 'MAM', 'JJA', 'SON' ]:
        seasons = [ season.upper() ]
      elif season.lower() in ['monthly']:
        seasons = [ season.lower() ]
      else:
        parser.error('Given SEASON, "'+season+'", is NOT available with given VARIABILITY_MODE, '+mode)
  if mode in ['PDO']:
    if season.lower() in ['monthly']:
      seasons = [ season.lower() ]
    else:
      print 'CAUTION!! PDO calculation is not based on season. Season was automatically set to "monthly"'
      seasons = [ 'monthly' ]
  return seasons

def YearCheck(year):
  try:
    syear = int(year.split(',')[0])
    eyear = int(year.split(',')[1])
  except:
    parser.error('Given YEAR, "'+str(year)+'", is NOT correct. Please refer help document by using "-h" option')

  if syear >= eyear:
    parser.error('Given YEAR, "'+str(year)+'", is NOT correct. Starting year is later than ending year.\n'+
                 'Please refer help document by using "-h" option')
  return syear, eyear

def RealizationCheck(realization):
  if realization.lower() == 'all':
    runs = '*'
  else:
    runs = realization.lower()
  return(runs)

