import pcmdi_metrics.driver.pmp_parser as pmp_parser


class PMPParser(pmp_parser.PMPParser):
    def __init__(self, warning=True, *args, **kwargs):
        # conflict_handler='resolve' lets new args override older ones
        super(PMPParser, self).__init__(*args, **kwargs)
        if warning:
            print("Deprecation warning: please use 'import pcmdi_metrics.driver.pmp_parser.PMPParser'")

