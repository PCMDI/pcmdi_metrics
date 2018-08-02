import cdp.cdp_parser
import pcmdi_metrics.driver.pmp_parameter
import os
import sys
import genutil


try:
    basestring  # noqa
except Exception:
    basestring = str

class PMPParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPParser, self).__init__(pcmdi_metrics.driver.pmp_parameter.PMPParameter,
                                        os.path.join(sys.prefix, "share", "cia", "DefArgsCIA.json"), *args, **kwargs)
        self.use("parameters")
        self.use("diags")

    def process_templated_argument(self, name, extra=None):
        """Applies arg parse values to a genutil.StringConstructor template type argument
        Input:
           name: name of the argument to process
           extra: other object(s) to get keys from
        Output: 
           formatted argument
        """

        process = getattr(self, name, None)
        if process is None:  # Ok not an argument from arg_parse maybe a template or string constructor itself
            if isinstance(name, basestring):
                process = name
            elif isinstance(name, genutil.StringConstructor):
                process = name.template
            else:
                raise RuntimeError("Could not figure out how to process argument {}".format(name))
        
        if not isinstance(process, basestring):
                raise RuntimeError(
                    "Could not figure out how to process argument {}".format(name))
            


class PMPMetricsParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPMetricsParser, self).__init__(pcmdi_metrics.driver.pmp_parameter.PMPMetricsParameter,
                                               os.path.join(sys.prefix, "share", "cia", "DefArgsCIA.json"),
                                               *args, **kwargs)
        self.use("parameters")
        self.use("diags")
