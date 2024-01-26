import warnings


class StringConstructor:
    """
    This class aims at spotting keywords in a string and replacing them.
    """

    def __init__(self, template=None):
        """
        Instantiates a StringConstructor object.
        """
        self.template = template
        # Generate the keys and set them to empty
        keys = self.keys()
        for k in keys:
            setattr(self, k, "")

    def keys(self, template=None):
        if template is None:
            template = self.template
        if template is None:
            return []
        # Determine the keywords in the template
        keys = []
        template_split = template.split("%(")[1:]
        if len(template_split) > 0:
            for k in template_split:
                sp = k.split(")")
                if sp[0] not in keys:
                    keys.append(sp[0])
        return keys

    def construct(self, template=None, **kw):
        """
        Accepts a string with an unlimited number of keywords to replace.
        """
        if template is None:
            template = self.template
        # Replace the keywords with their values
        for k in self.keys():
            if k not in kw:
                warnings.warn(f"Keyword '{k}' not provided for filling the template.")
            template = template.replace("%(" + k + ")", kw.get(k, getattr(self, k, "")))
        return template

    def reverse(self, name, debug=False):
        """
        The reverse function attempts to take a template and derive its keyword values based on name parameter.
        """
        out = {}
        template = self.template
        for k in self.keys():
            sp = template.split("%%(%s)" % k)
            i1 = name.find(sp[0]) + len(sp[0])
            j1 = sp[1].find("%(")
            if j1 == -1:
                if sp[1] == "":
                    val = name[i1:]
                else:
                    i2 = name.find(sp[1])
                    val = name[i1:i2]
            else:
                i2 = name[i1:].find(sp[1][:j1])
                val = name[i1 : i1 + i2]
            template = template.replace("%%(%s)" % k, val)
            out[k] = val
        if self.construct(self.template, **out) != name:
            raise ValueError("Invalid pattern sent")
        return out

    def __call__(self, *args, **kw):
        """default call is construct function"""
        return self.construct(*args, **kw)


def fill_template(template: str, **kwargs) -> str:
    """
    Fill in a template string with keyword values.

    Parameters
    ----------
    - template (str): The template string containing keywords of the form '%(keyword)'.
    - kwargs (dict): Keyword arguments with values to replace in the template.

    Returns
    -------
    - str: The filled-in string with replaced keywords.

    Examples
    --------
    >>> from pcmdi_metrics.utils import fill_template
    >>> template = "This is a %(adjective) %(noun) that %(verb)."
    >>> filled_string = fill_template(template, adjective="great", noun="example", verb="works")
    >>> print(filled_string)  # It will print "This is a great example that works."
    """
    filler = StringConstructor(template)
    filled_template = filler.construct(**kwargs)
    return filled_template
