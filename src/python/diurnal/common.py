import genutil

monthname_d = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
               7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

def populateStringConstructor(template,args):
    template = genutil.StringConstructor(template)
    for k in template.keys():
        if hasattr(args,k):
            setattr(template,k,str(getattr(args,k)))
    return template

from pcmdi_metrics.driver.pmp_parser import PMPParser
P = PMPParser()
P.add_argument("-i", "--modroot",
                      default='data',
                      help="Root directory for model (or observed) 3-hourly data")
P.add_argument("-m", "--month",
                      type=int,
                      default=9,
                      help="Month to be processed, given as 2-char month number")
P.add_argument("-f", "--firstyear",
                      type=int,
                      default=1999,
                      help="First year of data processing")
P.add_argument("-l", "--lastyear",
                      type=int,
                      default=2005,
                      help="Last year of data processing")
P.add_argument("-o","--output_directory",
        default = "out",
        help="output directory")
P.add_argument("-r", "--realization",
                      default="r1i1p1",
                      help="Realization used")
P.add_argument("--version",default="*")
P.add_argument("--frequency",default="3hr")
P.add_argument("--realm",default="atm")
P.add_argument("--model",default="*")
P.add_argument("--experiment",default="historical")
P.add_argument("-t","--filename_template",
       default = "cmip5.%(model).%(experiment).%(realization).%(frequency).%(realm).%(frequency).%(variable).%(version).latestX.xml")
P.add_argument("--skip",default = [],
        help="models to skip",nargs="*")
