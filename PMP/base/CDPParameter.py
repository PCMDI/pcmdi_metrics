import abc
import importlib
import sys
import os


class CDPParameter(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def check_values():
        """Check that all of the variables in this parameter file are valid.
        If loading from a file using load_parameter_from_py(), check if all of
        the correct variables are defined in that file.
        """
        raise NotImplementedError()

    def __get__(self):
        self.check_values()

    def import_user_parameter_file_as_module(self, parameter_file_path):
        # Ex: parameter_file_path is '/Users/shaheen2/Desktop/parameter.py'
        # Then self.path_to_module = '/Users/shaheen2/Desktop'
        # And self.module_name = 'parameter'
        # self.user_file_module is a reference to the parameter file,
        #  which is parameter.py in this case
        if not os.path.isfile(parameter_file_path):
            raise IOError('Parameter file %s not found.' % parameter_file_path)

        self.path_to_module = os.path.split(parameter_file_path)[0]
        self.module_name = os.path.split(parameter_file_path)[1]
        if self.module_name.count('.') > 1:
            raise ValueError("Filename cannot contain '.' outside extension.")
        if '.' in self.module_name:
            self.module_name = self.module_name.split('.')[0]

        sys.path.insert(0, self.path_to_module)
        self.user_file_module = importlib.import_module(self.module_name)

    def load_vars_from_user_module(self):
        # self.user_defined_vars has all of the defined variables
        #  such as vars, output_path, etc.
        self.user_defined_vars = []
        for user_var in dir(self.user_file_module):
            if not user_var.startswith('__'):
                self.user_defined_vars.append(user_var)

        # initalize the variables in this parameter, so the driver can
        #  access them as if they were defined regularly.
        # This is the bad practice I was talking about.
        for var in self.user_defined_vars:
            exec("self." + var + " = self.user_file_module." + var)

    # Parameter files can also be initalized from a file.
    # This is bad practice, but it was a requirement.
    def load_parameter_from_py(self, parameter_file_path):
        self.import_user_parameter_file_as_module(parameter_file_path)
        self.load_vars_from_user_module()
