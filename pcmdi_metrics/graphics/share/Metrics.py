import copy
import glob
import os

import numpy as np
import pandas as pd

from pcmdi_metrics.graphics import read_mean_clim_json_files


class Metrics:
    """Mean climate metrics object class"""

    def __init__(self, files):
        """Initialize the mean climate metrics class

        This method initializes the mean climate metrics object given a
        single json file, a list of json files, or a directory containing
        a set of json files.

        Parameters
        ----------
        files : str, path-like or list
            Input json file(s) or directory containing json files

        Returns
        -------
        Metrics
            mean climte metrics object class
        """

        # if `files` input is a string, determine if it is a single file
        # or if it is a directory containing json files

        if isinstance(files, str):

            assert os.path.exists(files), "Specified path does not exist."

            if os.path.isfile(files):
                files = [files]
            elif os.path.isdir(files):
                files = glob.glob(f"{files}/*.json")

        else:

            assert isinstance(
                files, list
            ), "Input must either be a single file, directory, or list of files."

        # call `read_mean_clim_json_files` and save the results as
        # object attributes

        (
            self.df_dict,
            self.var_list,
            self.var_unit_list,
            self.var_ref_dict,
            self.regions,
            self.stats,
        ) = read_mean_clim_json_files(files)

    def copy(self):
        """method to deep copy a Metrics instance"""
        return copy.deepcopy(self)

    def merge(self, metrics_obj):
        """Method to merge Metrics instance with another instance

        This method merges an existing metrics instance with another instance
        by finding the superset of stats, seasons, and regions across the
        two instances

        Parameters
        ----------
        metrics_obj : Metrics
            Metrics object to merge with exisiting instance

        Returns
        -------
        Metrics
            merged Metrics instance
        """

        # ensure that second `metrics_obj` is a Metrics object
        assert isinstance(
            metrics_obj, Metrics
        ), "Metrics objects must be merged with other Metrics objects"

        # make a copy of the existing instance as the result
        result = self.copy()

        # loop over superset of `stats`
        stats = set(self.df_dict.keys()).union(metrics_obj.df_dict.keys())
        for stat in sorted(stats):

            # loop over superset of seasons
            seasons = set(self.df_dict[stat].keys()).union(
                metrics_obj.df_dict[stat].keys()
            )
            for season in seasons:

                # loop over superset of regions
                regions = set(self.df_dict[stat][season].keys()).union(
                    metrics_obj.df_dict[stat][season].keys()
                )
                for region in regions:

                    # consider both the current Metrics instance and
                    # candidate `metrics_obj` instance and determine if the
                    # [stat][season][region] nesting contains a pd.DataFrame.
                    # If a KeyError is thrown, it likely does not exist
                    # and initialize an empty pd.DataFrame. If some other
                    # exception occurs, raise it.

                    try:
                        _df1 = self.df_dict[stat][season][region]
                        assert isinstance(
                            _df1, pd.core.frame.DataFrame
                        ), "Unexpected object found"
                    except Exception as exception:
                        if isinstance(exception, KeyError):
                            _df1 = pd.DataFrame()
                        else:
                            raise exception

                    try:
                        _df2 = metrics_obj.df_dict[stat][season][region]
                        assert isinstance(
                            _df2, pd.core.frame.DataFrame
                        ), "Unexpected object found"
                    except Exception as exception:
                        if isinstance(exception, KeyError):
                            _df2 = pd.DataFrame()
                        else:
                            raise exception

                    # concatenate `merge_obj` to the end of the current
                    # instance. Fill `None` types as np.nan to avoid potential
                    # issues with future funcs, such as `normalize_by_median`

                    result.df_dict[stat][season][region] = pd.concat(
                        [_df1, _df2], ignore_index=True
                    ).fillna(value=np.nan)

        # determine the superset of the other attributes

        result.var_list = list(set(self.var_list + metrics_obj.var_list))
        result.var_unit_list = list(set(self.var_unit_list + metrics_obj.var_unit_list))
        result.var_ref_dict = {**self.var_ref_dict, **metrics_obj.var_ref_dict}
        result.regions = list(set(self.regions + metrics_obj.regions))
        result.stats = list(set(self.stats + metrics_obj.stats))

        return result


"""
# ----- sample usage -----

# existing library of mean climate metrics downloaded from portrait_plot_mean_clim.ipynb
library = Metrics("./json_files")

# new test case
test_case = Metrics("/net/jpk/output")

# merged
combined = library.merge(test_case)
"""
