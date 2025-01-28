# -*- coding:UTF-8 -*-
from __future__ import print_function
from sys import exit as sys_exit


# ---------------------------------------------------#
# colors for printing
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# ---------------------------------------------------------------------------------------------------------------------#
#
# Set of defined errors and warning functions used in EnsoUvcdatToolsLib.py
#
def plus_comma_space(string):
    """
    #################################################################################
    Description:
    Adds a comma and a space if the string is not empty or if the string is not composed of space only
    #################################################################################

    :param string: string
        string to which comma_space could be added

    :return string: string
        given string+', ' if applicable

    Examples
    ----------
    string = string('')
    print string
    ''
    # or
    string = string('     ')
    print string
    '     '
    # or
    string = string('Where there’s a will')
    print string
    'Where there’s a will, '
    """
    if string.isspace():
        return string
    elif not string:
        return string
    else:
        return string+', '


def message_formating(inspect_stack):
    """
    #################################################################################
    Description:
    Formats inspect.stack() as '   File filename, line n, in module'
    #################################################################################

    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()

    :return string: string
        formatted inspect.stack() in a string (using PlusCommaSpace)

    Examples
    ----------
    string = message_formating(inspect_stack)
    print string
    '   File filename, line n, in module'
    """
    string = '   '
    # adds file's name
    if inspect_stack[0][1] != '<stdin>':
        string = plus_comma_space(string) + 'File ' + str(inspect_stack[0][1])
    # adds line number
    string = plus_comma_space(string) + 'line ' + str(inspect_stack[0][2])
    # adds module's name
    if inspect_stack[0][3] != '<module>':
        string = plus_comma_space(string) + 'in ' + str(inspect_stack[0][3])
    return string


def my_warning(list_strings):
    """
    #################################################################################
    Description:
    Prints the strings in 'list_strings' and continues
    #################################################################################

    :param list_strings: list
        list of strings to print
    :return:
    """
    for ii in range(2):
        print(bcolors.WARNING + "")
    print(str().ljust(5) + "%%%%%     -----     %%%%%")
    for string in list_strings:
        print(str().ljust(5) + str(string))
    print(str().ljust(5) + "%%%%%     -----     %%%%%")
    for ii in range(2):
        print("" + bcolors.ENDC)
    return


# ---------------------------------------------------------------------------------------------------------------------#
#
# ERRORS
#
def my_error(list_strings):
    """
    #################################################################################
    Description:
    Prints the strings in 'list_strings' and exits
    #################################################################################

    :param list_strings: list
        list of strings to print
    :return:
    """
    for ii in range(2):
        print(bcolors.FAIL + "")
    print(str().ljust(5) + "%%%%%     -----     %%%%%")
    for string in list_strings:
        print(str().ljust(5) + str(string))
    print(str().ljust(5) + "%%%%%     -----     %%%%%")
    for ii in range(2):
        print("" + bcolors.ENDC)
    sys_exit("")
    return


def mismatch_shapes_error(tab1, tab2, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_error' in the case of array shape error
    Prints strings and exits
    #################################################################################

    :param tab1: masked_array
    :param tab2: masked_array
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    try: name1 = tab1.name
    except: name1 = 'no_name'
    try: name2 = tab2.name
    except: name2 = 'no_name'
    list_strings = ["ERROR " + message_formating(inspect_stack) + ": array shape",
                    str().ljust(5) + "arrays shapes mismatch: " + str(name1) + " = " + str(tab1.shape) + "', and "
                    + str(name2) + " = " + str(tab2.shape)]
    my_warning(list_strings)
    return


def object_type_error(parameter_name, type_parameter, type_parameter_should_be, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_error' in the case of object type error
    Prints strings and exits
    #################################################################################

    :param parameter_name: string
        name of a parameter from which the error comes from
    :param type_parameter: string
        parameter's type
    :param type_parameter_should_be: string
        what the parameter's type should be
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR " + message_formating(inspect_stack) + ": object type",
                    str().ljust(5) + str(parameter_name) + ": should be '" + str(type_parameter_should_be) + "', not '"
                    + str(type_parameter) + "'"]
    my_warning(list_strings)
    return


def too_short_time_period(metric_name, length, minimum_length, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_warning' in the case of a too short time-period
    Prints strings and exits
    #################################################################################

    :param metric_name: string
        name of the metric from which the error comes from
    :param length: integer
        length of the time axis of the variable
    :param minimum_length: integer
        minimum length of the time axis for the metric to make sens (defined in the metrics collection)
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR " + message_formating(inspect_stack) + ": too short time-period",
                    str().ljust(5) + str(metric_name) + ": the time-period is too short: " + str(length)
                    + " (minimum time-period: " + str(minimum_length) + ")"]
    my_warning(list_strings)
    return


def unlikely_units(var_name, name_in_file, units, min_max, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_warning' in the case of unlikely units
    Prints strings and exits
    #################################################################################

    :param var_name: string
        generic name of the variable that has unlikely units
    :param name_in_file: string
        name of the variable in the file (usually the short_name) that has unlikely units
    :param units: string
        units of the variable
    :param min_max: list
        minimum and maximum values of 'var_name'
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR " + message_formating(inspect_stack) + ": units",
                    str().ljust(5) + "the file says that " + str(var_name) + " (" + str(name_in_file)
                    + ") is in " + str(units) + " but it seems unlikely (" + str(min_max) + ")"]
    my_warning(list_strings)
    return


def unknown_averaging(average, known_average, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_error' in the case of unknown frequency
    Prints strings
    #################################################################################

    :param average: string
        averaging method (axis) (should by horizontal, meridional, temporal or zonal)
    :param known_average: string
        list of defined averaging method (axis)
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR" + message_formating(inspect_stack) + ": averaging method",
                    str().ljust(5) + "unkwown averaging method (axis): " + str(average),
                    str().ljust(10) + "known averaging method: " + str(sorted(known_average))]
    my_error(list_strings)
    return


def unknown_frequency(frequency, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_error' in the case of unknown frequency
    Prints strings
    #################################################################################

    :param frequency: string
        frequency of a dataset (should by daily, monthly or yearly)
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR" + message_formating(inspect_stack) + ": frequency",
                    str().ljust(5) + "unknown frequency: " + str(frequency)]
    my_error(list_strings)
    return


def unknown_key_arg(arg, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'my_error' in the case of unknown argument
    Prints strings
    #################################################################################

    :param arg: string
        argument of a function
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR" + message_formating(inspect_stack) + ": argument",
                    str().ljust(5) + "unknown argument(s): " + str(arg)]
    my_warning(list_strings)
    return


def unknown_units(var_name, name_in_file, units, inspect_stack):
    """
    #################################################################################
    Description:
    Function 'MyError' in the case of unknown units
    Prints strings and exits
    #################################################################################

    :param var_name: string
        generic name of the variable that has unlikely units
    :param name_in_file: string
        name of the variable in the file (usually the short_name) that has unlikely units
    :param units: string
        units of the variable
    :param inspect_stack: array
        list of information about the program/module/line,... created using inspect.stack()
    :return:
    """
    list_strings = ["ERROR" + message_formating(inspect_stack) + ": units",
                    str().ljust(5) + "unknown units: " + str(var_name) + " (" + str(name_in_file)
                    + ") is in " + str(units)]
    my_warning(list_strings)
    return
# ---------------------------------------------------------------------------------------------------------------------#


# ---------------------------------------------------------------------------------------------------------------------#
# Just prints
def debug_mode(color, title, nbr_spaces, axes1='', axes2='', axes3='', axes4='', file1='', file2='', file3='', file4='',
               line1='', line2='', line3='', line4='', nina1='', nina2='', nina3='', nina4='', nino1='', nino2='',
               nino3='', nino4='', shape1='', shape2='', shape3='', shape4='', time1='', time2='', time3='', time4='',
               var1='', var2='', var3='', var4=''):
    """
    #################################################################################
    Description:
    Prints strings to ease debugging
    #################################################################################

    :param color: string
        color code (e.g. '\033[94m' is blue, '\033[92m' is green)
    :param title: string
        name of the section that is printed
    :param nbr_spaces: int
        number of leading spaces before printing the title
    :param axes1: string, optional
        axis list of variable 1
    :param axes2: string, optional
        axis list of variable 2
    :param axes3: string, optional
        axis list of variable 3
    :param axes4: string, optional
        axis list of variable 4
    :param file1: string, optional
        file name of variable 1
    :param file2: string, optional
        file name of variable 2
    :param file3: string, optional
        file name of variable 3
    :param file4: string, optional
        file name of variable 4
    :param line1: string, optional
        just a line to print 1
    :param line2: string, optional
        just a line to print 2
    :param line3: string, optional
        just a line to print 3
    :param line4: string, optional
        just a line to print 4
    :param nina1: string, optional
        list of nina years 1
    :param nina2: string, optional
        list of nina years 2
    :param nina3: string, optional
        list of nina years 3
    :param nina4: string, optional
        list of nina years 4
    :param nino1: string, optional
        list of nino years 1
    :param nino2: string, optional
        list of nino years 2
    :param nino3: string, optional
        list of nino years 3
    :param nino4: string, optional
        list of nino years 4
    :param shape1: string, optional
        shape of the array containing variable 1
    :param shape2: string, optional
        shape of the array containing variable 2
    :param shape3: string, optional
        shape of the array containing variable 3
    :param shape4: string, optional
        shape of the array containing variable 4
    :param time1: string, optional
        time bounds of variable 1
    :param time2: string, optional
        time bounds of variable 2
    :param time3: string, optional
        time bounds of variable 3
    :param time4: string, optional
        time bounds of variable 4
    :param var1: string, optional
        variable name 1
    :param var2: string, optional
        variable name 2
    :param var3: string, optional
        variable name 3
    :param var4: string, optional
        variable name 4
    :return:
    """
    # first variable
    print(color + str().ljust(nbr_spaces) + title + bcolors.ENDC)
    if file1:
        print(color + str().ljust(nbr_spaces+5) + 'file name 1: ' + file1 + bcolors.ENDC)
    if var1:
        print(color + str().ljust(nbr_spaces+5) + 'variable name 1: ' + var1 + bcolors.ENDC)
    if axes1:
        print(color + str().ljust(nbr_spaces+5) + 'axes list 1: ' + axes1 + bcolors.ENDC)
    if time1:
        print(color + str().ljust(nbr_spaces+5) + 'time bounds 1: ' + time1 + bcolors.ENDC)
    if shape1:
        print(color + str().ljust(nbr_spaces+5) + 'shape 1: ' + shape1 + bcolors.ENDC)
    if nina1:
        print(color + str().ljust(nbr_spaces+5) + 'nina year 1: ' + nina1 + bcolors.ENDC)
    if nino1:
        print(color + str().ljust(nbr_spaces+5) + 'nino year 1: ' + nino1 + bcolors.ENDC)
    if line1:
        print(color + str().ljust(nbr_spaces+5) + line1 + bcolors.ENDC)
    # second variable
    if file2:
        print(color + str().ljust(nbr_spaces+5) + 'file name 2: ' + file2 + bcolors.ENDC)
    if var2:
        print(color + str().ljust(nbr_spaces+5) + 'variable name 2: ' + var2 + bcolors.ENDC)
    if axes2:
        print(color + str().ljust(nbr_spaces+5) + 'axes list 2: ' + axes2 + bcolors.ENDC)
    if time2:
        print(color + str().ljust(nbr_spaces+5) + 'time bounds 2: ' + time2 + bcolors.ENDC)
    if shape2:
        print(color + str().ljust(nbr_spaces+5) + 'shape 2: ' + shape2 + bcolors.ENDC)
    if nina2:
        print(color + str().ljust(nbr_spaces+5) + 'nina year 2: ' + nina2 + bcolors.ENDC)
    if nino2:
        print(color + str().ljust(nbr_spaces+5) + 'nino year 2: ' + nino2 + bcolors.ENDC)
    if line2:
        print(color + str().ljust(nbr_spaces+5) + line2 + bcolors.ENDC)
    # third variable
    if file3:
        print(color + str().ljust(nbr_spaces + 5) + 'file name 3: ' + file3 + bcolors.ENDC)
    if var3:
        print(color + str().ljust(nbr_spaces + 5) + 'variable name 3: ' + var3 + bcolors.ENDC)
    if axes3:
        print(color + str().ljust(nbr_spaces + 5) + 'axes list 3: ' + axes3 + bcolors.ENDC)
    if time3:
        print(color + str().ljust(nbr_spaces + 5) + 'time bounds 3: ' + time3 + bcolors.ENDC)
    if shape3:
        print(color + str().ljust(nbr_spaces + 5) + 'shape 3: ' + shape3 + bcolors.ENDC)
    if nina3:
        print(color + str().ljust(nbr_spaces + 5) + 'nina year 3: ' + nina3 + bcolors.ENDC)
    if nino3:
        print(color + str().ljust(nbr_spaces + 5) + 'nino year 3: ' + nino3 + bcolors.ENDC)
    if line3:
        print(color + str().ljust(nbr_spaces + 5) + line3 + bcolors.ENDC)
    # fourth variable
    if file4:
        print(color + str().ljust(nbr_spaces + 5) + 'file name 4: ' + file4 + bcolors.ENDC)
    if var4:
        print(color + str().ljust(nbr_spaces + 5) + 'variable name 4: ' + var4 + bcolors.ENDC)
    if axes4:
        print(color + str().ljust(nbr_spaces + 5) + 'axes list 4: ' + axes4 + bcolors.ENDC)
    if time4:
        print(color + str().ljust(nbr_spaces + 5) + 'time bounds 4: ' + time4 + bcolors.ENDC)
    if shape4:
        print(color + str().ljust(nbr_spaces + 5) + 'shape 4: ' + shape4 + bcolors.ENDC)
    if nina4:
        print(color + str().ljust(nbr_spaces + 5) + 'nina year 4: ' + nina4 + bcolors.ENDC)
    if nino4:
        print(color + str().ljust(nbr_spaces + 5) + 'nino year 4: ' + nino4 + bcolors.ENDC)
    if line4:
        print(color + str().ljust(nbr_spaces + 5) + line4 + bcolors.ENDC)
    return
# ---------------------------------------------------------------------------------------------------------------------#
