import genutil
from pcmdi_metrics.driver.pmp_parser import PMPParser

monthname_d = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
               7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}


class INPUT(object):
    def __init__(self, args, filename, filename_template, varname="pr"):
        self.fileName = filename
        self.args = args
        self.monthname = monthname_d[args.month]
        self.varname = varname
        self.template = filename_template


def populateStringConstructor(template, args):
    template = genutil.StringConstructor(template)
    for k in template.keys():
        if hasattr(args, k):
            setattr(template, k, str(getattr(args, k)))
    return template


P = PMPParser()
P.use("--modpath")
P.use("--results_dir")
P.use("--num_workers")

P.add_argument("-m", "--month",
               type=int,
               default=7,
               help="Month to be processed, given as 2-char month number")
P.add_argument("-f", "--firstyear",
               type=int,
               default=1999,
               help="First year of data processing")
P.add_argument("-l", "--lastyear",
               type=int,
               default=2005,
               help="Last year of data processing")
P.add_argument("-r", "--realization",
               default="r1i1p1",
               help="Realization used")
P.add_argument("--version", default="*")
P.add_argument("--frequency", default="3hr")
P.add_argument("--realm", default="atm")
P.add_argument("--model", default="*")
P.add_argument("--experiment", default="historical")
P.add_argument("-t", "--filename_template",
               default="cmip5.%(model).%(experiment).%(realization).%(frequency).%(realm).%(frequency).%(variable).%(version).latestX.xml")  # noqa
P.add_argument("--skip", default=[],
               help="models to skip", nargs="*")
P.add_argument(
    "-a",
    "--append",
    default=False,
    action="store_true",
    help="append in json file if json exist (e.g. adding a model to file)")
