import os
import glob
import re
import json
import time
import datetime
import xcdat as xc
import numpy as np
import pandas as pd
import shutil
import psutil
import subprocess
import matplotlib.pyplot as plt

import collections
from collections import OrderedDict

from itertools import chain
from subprocess import Popen, PIPE, call

import pcmdi_metrics

from pcmdi_metrics.io import (
    xcdat_open
)

from pcmdi_metrics.utils import (
    sort_human,
    create_land_sea_mask
)

from pcmdi_metrics.graphics import (
    Metrics,
    normalize_by_median,
    parallel_coordinate_plot,
    portrait_plot,
)

def childCount():
    current_process = psutil.Process()
    children = current_process.children()
    return(len(children))

def parallel_jobs(cmds,num_workers):
    procs = []
    # Start multiple subprocesses
    for i,p in enumerate(cmds):
       proc = Popen(p, stdout=PIPE, shell=True)
       procs.append(proc)
       if (len(procs) >= num_workers) or (i == len(cmds)-1):
         print('running {} subprocesses'.format(childCount()))  
         for proc in procs:
            stdout, error = proc.communicate()
            rcode = proc.returncode
            if error:
              exit("ERROR: process {} failed".format(p))
         time.sleep(0.25)
         procs = []
       
    return stdout,error,rcode

def serial_jobs(cmds,num_workers):
    for i,p in enumerate(cmds):
       print('running %s' % (str(p)))
       proc = Popen(p, stdout=PIPE, shell=True)
       stdout, error = proc.communicate()
       rcode = proc.returncode
       if error:
         exit("ERROR: process {} failed".format(p))
    return stdout,error,rcode 

def derive_var(path,vout,var_dic,fname):
    for i,var in enumerate(var_dic.keys()):
      fpath = sorted(glob.glob(os.path.join(path,"*."+var+".*.nc")))
      df = xcdat_open(fpath[0])
      if i == 0:
        template = fpath[0].split("/")[-1]
        #construct a copy of file for derived variable
        out = os.path.join(path,template.replace(".{}.".format(var),".{}.".format(vout)))
        shutil.copy(fpath[0],out)
        ds = xcdat_open(fpath[0])
        ds = ds.rename_vars({var:vout})
        ds[vout].data = ds[vout].data * var_dic[var]
      else:
        ds[vout].data = ds[vout].data + df[var].data * var_dic[var]
    ds.to_netcdf(out)
 
    return

def collect_data_info(test,test_set,refr,refr_set,variables,outset,outdir):
    #collect variables when both model and observations are available
    test_dic,refr_dic = OrderedDict(),OrderedDict()
    for i,var in enumerate(variables):
      if "_" in var or "-" in var:
        varin = re.split("_|-", var)[0]
      else:
        varin = var
      test_path = sorted(glob.glob(os.path.join(test,"*.{}.*.nc".format(varin))))
      refr_path = sorted(glob.glob(os.path.join(refr,"*.{}.*.nc".format(varin))))
      if (len(test_path) > 0) and (len(refr_path) > 0):
        if (os.path.exists(test_path[0])) and (os.path.exists(refr_path[0])):
          for j,path in enumerate([test_path[0],refr_path[0]]):
             fname = path.split("/")[-1]
             model = fname.split(".")[2]
             sbdic = { "mip"         : fname.split(".")[0],
                       "exp"         : fname.split(".")[1],
                       "model"       : fname.split(".")[2],
                       "realization" : fname.split(".")[3],
                       "tableID"     : fname.split(".")[4],
                       "yymms"       : fname.split(".")[6].split("-")[0],
                       "yymme"       : fname.split(".")[6].split("-")[1],
                       "var_in_file" : varin,
                       "var_name"    : var,
                       "yymms"       : fname.split(".")[6].split("-")[0],
                       "yymme"       : fname.split(".")[6].split("-")[1],
                       "var_in_file" : varin,
                       "var_name"    : var,
                       "file_path"   : path,
                       "template"    : fname 
                     }
             if j == 0:
               if varin not in test_dic.keys():
                 test_dic[varin] = {}
               if len(test_set) != len(variables):
                 kset = test_set[0]
               else:
                 kset = test_set[i]
               test_dic[varin]['set'] = kset
               test_dic[varin][kset]  = model
               test_dic[varin][model] = sbdic
             else:
               if varin not in refr_dic.keys():
                 refr_dic[varin] = {}
               if len(refr_set) != len(variables):
                 kset = refr_set[0]
               else:
                 kset = refr_set[i]
               refr_dic[varin]['set'] = kset
               refr_dic[varin][kset]  = model
               refr_dic[varin][model] = sbdic

    # Save test and obs/reference data information for next step
    for i,group in enumerate([test,refr]):
      if i == 0:
        out_dic = test_dic
      else:
        out_dic = refr_dic
      out_file = os.path.join(outdir,'{}_{}_catalogue.json'.format(group,outset))
      json.dump(out_dic,open(out_file, "w"),sort_keys=False,indent=4,separators=(",",": "))
 
    return test_dic,refr_dic

def variable_region(regions,variables):
    regv_dic = OrderedDict()
    for var in variables:
       if "_" in var or "-" in var:
         vkey = re.split("_|-", var)[0]
       else:
         vkey = var
       regv_dic[vkey] = regions
    #save region info dictionary
    json.dump(regv_dic,
              open('regions.json', "w"),
              sort_keys=False,
              indent=4,
              separators=(",", ": "))
    return

def enso_obsvar_dict(obs_dic,variables):
    #orgnize observation for enso driver
    refr_dic = OrderedDict()
    for var in variables:
       if "_" in var or "-" in var:
         vkey = re.split("_|-", var)[0]
       else:
         vkey = var
       refset  = obs_dic[vkey]['set']
       refname = obs_dic[vkey][refset]
       #data file in model->var sequence
       if refname not in refr_dic.keys():
          refr_dic[refname] = {}
       refr_dic[refname][vkey] = obs_dic[vkey][refname]

    #save data file dictionary
    json.dump(refr_dic,
              open('obs_catalogue.json', "w"),
              sort_keys=False,
              indent=4,
              separators=(",", ": "))

    return

def enso_obsvar_lmsk(obs_dic,variables):
    #orgnize observation landmask for enso driver
    relf_dic = OrderedDict()
    for var in variables:
       if "_" in var or "-" in var:
         vkey = re.split("_|-", var)[0]
       else:
         vkey = var
       refset  = obs_dic[vkey]['set']
       refname = obs_dic[vkey][refset]
       #land/sea mask
       if refname not in  relf_dic.keys():
          relf_dic[refname] = os.path.join(
              'fixed',
              'sftlf.{}.nc'.format(refname))

    #save data file dictionary
    json.dump(relf_dic,
              open('obs_landmask.json', "w"),
              sort_keys=False,
              indent=4,
              separators=(",", ": "))

    return

def shift_row_to_bottom(df, index_to_shift):
    idx = [i for i in df.index if i != index_to_shift]
    return df.loc[idx + [index_to_shift]]

def merge_data(model_lib,cmip_lib,model_name):
    model_lib,cmip_lib = check_regions(model_lib,cmip_lib)
    merge_lib = cmip_lib.merge(model_lib)
    merge_lib = check_units(merge_lib)
    for stat in merge_lib.df_dict:
        for season in merge_lib.df_dict[stat]:
            for region in merge_lib.df_dict[stat][season]:
                highlight_models = []
                df = merge_lib.df_dict[stat][season][region]
                for model in df["model"].tolist():
                    if "e3sm" in model.lower():
                        highlight_models.append(model)
                    if model in model_name:
                        idxs = df[df.iloc[:, 0] == model].index
                        df.loc[idxs, "model"] = model_name
                highlight_models.append(model_name)
                for model in highlight_models:
                    for idx in df[df.iloc[:, 0] == model].index:
                        df = shift_row_to_bottom(df, idx)
                merge_lib.df_dict[stat][season][region] = df.fillna(value=np.nan)
                del(df)
    return merge_lib

def check_badvals(data_lib):
    var_model={"E3SM-1-0"    : "ta-850",
               "E3SM-1-1-ECA": "ta-850", 
               "CIESM"       : "pr"}
    # loop data metrics and check bad values 
    for stat in data_lib.df_dict:
        for season in data_lib.df_dict[stat]:
            for region in data_lib.df_dict[stat][season]:
                df = pd.DataFrame(data_lib.df_dict[stat][season][region])
                for i, model in enumerate(df["model"].tolist()):
                    if model in var_model.keys():
                        idx = df[df.iloc[:, 0] == model].index
                        df.loc[idx, var_model[model]] = np.nan
                #rewrite the data with revised values
                data_lib.df_dict[stat][season][region] = df
                del(df)
    return data_lib

def check_regions(data_lib,refr_lib):
    regions = [x for x in data_lib.regions if x in refr_lib.regions]
    for kk in range(2):
        if kk == 0: 
           df_dict = refr_lib.df_dict.copy()
        else:
           df_dict = data_lib.df_dict.copy()
        #only keep shared regions   
        for stat in df_dict:
            for season in df_dict[stat]:
                sets_dict = dict((k, df_dict[stat][season][k]) for k in regions)
                if kk == 0:
                    refr_lib.df_dict[stat][season] = sets_dict
                else:
                    data_lib.df_dict[stat][season] = sets_dict
                del(sets_dict)
    
    #reassign regions  
    refr_lib.regions,data_lib.regions = regions,regions
    
    return data_lib,refr_lib

def check_references(data_dict):
    reference_alias = {'CERES-EBAF-4-1': 'ceres_ebaf_v4_1',
                       'CERES-EBAF-4-0': 'ceres_ebaf_v4_0',
                       'CERES-EBAF-2-8': 'ceres_ebaf_v2_8',
                       'GPCP-2-3'      : 'GPCP_v2_3',
                       'GPCP-2-2'      : 'GPCP_v2_2',
                       'GPCP-3-2'      : 'GPCP_v3_2',
                       'NOAA_20C'      : 'NOAA-20C',
                       'ERA-INT'       : 'ERA-Interim',
                       'ERA-5'         : 'ERA5'}
    for key,values in data_dict.items():
        if values != None:
          for i,value in enumerate(values):
            if value in reference_alias.keys():
                values[i] = reference_alias[value]
        data_dict[key] = values
    return data_dict

def check_units(data_lib):
    # we define fixed sets of variables used for final plotting.
    units_all = {
        "prw"   : "[kg m$^{-2}$]", "pr"    : "[mm d$^{-1}$]", "prsn"   : "[mm d$^{-1}$]",
        "prc"   : "[mm d$^{-1}$]", "hfls"  : "[W m$^{-2}$]",  "hfss"   : "[W m$^{-2}$]",
        "clivi" : "[kg $m^{-2}$]", "clwvi" : "[kg $m^{-2}$]", "psl"    : "[Pa]",
        "rlds"  : "[W m$^{-2}$]",  "rldscs": "[W $m^{-2}$]",  "evspsbl": "[kg m$^{-2} s^{-1}$]",
        "rtmt"  : "[W m$^{-2}$]",  "rsdt"  : "[W m$^{-2}$]",  "rlus"   : "[W m$^{-2}$]",
        "rluscs": "[W m$^{-2}$]",  "rlut"  : "[W m$^{-2}$]",  "rlutcs" : "[W m$^{-2}$]",
        "rsds"  : "[W m$^{-2}$]",  "rsdscs": "[W m$^{-2}$]",  "rstcre" : "[W m$^{-2}$]",
        "rltcre": "[W m$^{-2}$]",  "rsus"  : "[W m$^{-2}$]",  "rsuscs" : "[W m$^{-2}$]",
        "rsut"  : "[W m$^{-2}$]",  "rsutcs": "[W m$^{-2}$]",  "ts"     : "[K]",
        "tas"   : "[K]",           "tauu"  : "[Pa]",          "tauv"   : "[Pa]",
        "zg-500": "[m]",           "ta-200": "[K]",           "sfcWind": "[m s$^{-1}$]",
        "ta-850": "[K]",           "ua-200": "[m s$^{-1}$]",  "ua-850" : "[m s$^{-1}$]",
        "va-200": "[m s$^{-1}$]",  "va-850": "[m s$^{-1}$]",  "uas"    : "[m s$^{-1}$]",
        "vas"   : "[m s$^{-1}$]",  "tasmin": "[K]",           "tasmax" : "[K]",
        "clt"   : "[%]"}

    common_vars = [x for x in data_lib.var_list if x in units_all.keys()]
    #special case
    if 'rtmt' not in common_vars:
        if ('rt' in data_lib.var_list) or ('rmt' in data_lib.var_list):
            common_vars.append('rtmt')

    #collect unit list
    common_unts = [units_all[x] for x in common_vars]

    #collect reference list
    reflist = data_lib.var_ref_dict.copy()
    for var in reflist:
        if var not in common_vars:
            if var in ['rt','rmt']:
                data_lib.var_ref_dict['rtmt'] = data_lib.var_ref_dict.pop(var)
            else:
                data_lib.var_ref_dict.pop(var)
    data_lib.var_ref_dict = check_references(data_lib.var_ref_dict)
    #now clean up data to exclude vars not in common lists
    for stat in data_lib.df_dict:
        for season in data_lib.df_dict[stat]:
            for region in data_lib.df_dict[stat][season]:
                df = data_lib.df_dict[stat][season][region]
                if 'rt' in df.columns:
                    df['rtmt'] = df['rt']
                elif 'rmt' in df.columns:
                    df['rtmt'] = df['rmt']
                for var in df.columns[3:]:
                    if var not in common_vars:
                        df = df.drop(var,axis=1)
                data_lib.df_dict[stat][season][region] = df
                del(df)

    data_lib.var_list = common_vars
    data_lib.var_unit_list = common_unts

    return data_lib

def collect_clim_metrics(parameter):
    #merge data to an exisiting cmip base
    cmip_files = glob.glob(os.path.join(
        parameter['cmip_path'],
        parameter['cmip_name'].split(".")[0],
        parameter['cmip_name'].split(".")[1],
        parameter['cmip_name'].split(".")[2],
        "*.{}.json".format(parameter['cmip_name'].split(".")[2])))
    if len(cmip_files) > 0 and os.path.exists(cmip_files[0]):
        print('CMIP PCMDI DIAGs for Sythetic Metrics Found, Read data...')
        cmip_lib = Metrics(cmip_files)
        cmip_lib = check_badvals(cmip_lib)
        cmip_lib = check_units(cmip_lib)
    else:
        exit("Warning: CMIP PCMDI DIAGs for Sythetic Metrics Not Found,....")

    model_name = '-'.join([
        parameter['test_name'].split(".")[2],
        parameter['test_name'].split(".")[3]])
    model_files = glob.glob(os.path.join(
        parameter['test_path'],
        "*_{}.json".format(parameter['case_id'])))
    if len(model_files) > 0 and os.path.exists(model_files[0]):
        print('{} PCMDI DIAGs for Sythetic Metrics Found, Read data...'.format(model_name))
        model_lib = Metrics(model_files)
        model_lib = check_units(model_lib)
    else:
        exit("Warning: Model PCMDI DIAGs for Sythetic Metrics Not Found,....")

    #merge model data with reference cmip data
    merge_lib = merge_data(model_lib,cmip_lib,model_name)
    
    return merge_lib

def movs_load_file(file_lists,modes):
    json_lib = dict()
    for mode in modes:
        if mode in ['PSA1', 'NPO', 'NPGO']:
            eof = 'EOF2'
        elif mode in ['PSA2']:
            eof = 'EOF3'
        else:
            eof = 'EOF1'
        for json_file in file_lists:
            if mode in json_file and eof in json_file: 
                with open(json_file) as fj:
                    dict_temp = json.load(fj)['RESULTS']
                    json_lib[mode] = dict_temp
    return json_lib

def movs_dict2df(movs_dict,stat,modes):
    models = sorted(list(movs_dict['NAM'].keys()))
    df = pd.DataFrame()
    df['model'] = models
    df['num_runs'] = np.nan
    mode_season_list = list()
    for mode in modes:
        if mode in ['PDO','NPGO']:
            seasons = ['monthly']
        elif mode in ['AMO']:
            seasons = ['yearly']
        else:
            seasons = ['DJF','MAM','JJA','SON']
        for season in seasons:
            df[mode+"_"+season] = np.nan
            mode_season_list.append(mode+"_"+season)
            for index, model in enumerate(models):
                if mode in movs_dict.keys() and model in list(movs_dict[mode].keys()):
                    runs = sort_human(list(movs_dict[mode][model].keys()))
                    stat_run_list = list()
                    for run in runs:
                        stat_run = (
                            movs_dict[mode][model][run]['defaultReference'][mode][season]['cbf'][stat]
                        )
                        stat_run_list.append(stat_run)
                    stat_model = np.average(np.array(stat_run_list))
                    num_runs = len(runs)
                    df.at[index, mode+"_"+season] = stat_model
                    if np.isnan(df.at[index, 'num_runs']):
                        df.at[index, 'num_runs'] = num_runs
                else:
                    stat_model = np.nan
                    num_runs = 0
                    # assign missing values for modes not in cmip datasets
                    df.at[index, mode+"_"+season] = stat_model
                    df.at[index, 'num_runs'] = 0 

    return df, mode_season_list

def collect_movs_metrics(parameter):
    #merge data to an exisiting cmip base
    cmip_files = glob.glob(os.path.join(
        parameter['cmip_path'],
        parameter['cmip_name'].split(".")[0],
        parameter['cmip_name'].split(".")[1],
        parameter['cmip_name'].split(".")[2],
        "*/*/var_mode_*.json"))
    if len(cmip_files) > 0 and os.path.exists(cmip_files[0]):
        print('CMIP PCMDI DIAGs for Sythetic Metrics Found, Read data...')
        cmip_lib = movs_load_file(cmip_files,parameter['movs_mode'])
    else:
        exit("Warning: CMIP PCMDI DIAGs for Sythetic Metrics Not Found,....")

    model_name = '-'.join([
        parameter['test_name'].split(".")[2],
        parameter['test_name'].split(".")[3]])
    model_files = glob.glob(os.path.join(
        parameter['test_path'],
        "*_{}.json".format(parameter['case_id'])))
    if len(model_files) > 0 and os.path.exists(model_files[0]):
        print('{} PCMDI DIAGs for Sythetic Metrics Found, Read data...'.format(model_name))
        model_lib = movs_load_file(model_files,parameter['movs_mode'])
    else:
        exit("Warning: Model PCMDI DIAGs for Sythetic Metrics Not Found,....")

    merge_lib = dict()
    for stat in parameter['diag_vars'].keys():
        cmip_df, mode_season_list = movs_dict2df(cmip_lib,stat,parameter['movs_mode'])
        model_df, mode_season_list = movs_dict2df(model_lib,stat,parameter['movs_mode'])
        merge_df = pd.concat([cmip_df, model_df],ignore_index=True)
        for model in merge_df["model"].tolist():
            if "e3sm" in model.lower():
                for idx in merge_df[merge_df.iloc[:, 0] == model].index:
                    merge_df = shift_row_to_bottom(merge_df, idx)
        for model in merge_df["model"].tolist():
            if model in model_name:
                for idx in merge_df[merge_df.iloc[:, 0] == model].index:
                    merge_df.loc[idx,"model"] = model_name
                    merge_df = shift_row_to_bottom(merge_df, idx)
        merge_lib[stat] = merge_df 
        del(cmip_df,model_df,merge_df)

    return merge_lib,mode_season_list

def create_data_lmask(test,refr,subset,fixed_dir): 
    #loop each group and process land/mask if not exist
    for group in [test,refr]:
       dic_file = os.path.join(
               'pcmdi_diags',
               '{}_{}_catalogue.json'.format(group,subset)
       )
       data_dic = json.load(open(dic_file))
       for var in data_dic.keys():
         mdset = data_dic[var]['set']
         model = data_dic[var][mdset]
         mpath = data_dic[var][model]['file_path']
         mpath_lf = os.path.join(
               fixed_dir,
               'sftlf.{}.nc'.format(model)
         )
         if not os.path.exists(fixed_dir):
            os.makedirs(fixed_dir)
         # generate land/sea mask if not exist
         if not os.path.exists(mpath_lf):
           ds = xcdat_open(mpath, decode_times=True)
           ds = ds.bounds.add_missing_bounds()
           try:
               lf_array = create_land_sea_mask(ds, method="regionmask")
               print("land mask is estimated using regionmask method.")
           except Exception:
               lf_array = create_land_sea_mask(ds, method="pcmdi")
               print("land mask is estimated using pcmdi method.")
           lf_array = lf_array * 100.0
           lf_array.attrs['long_name']= "land_area_fraction"
           lf_array.attrs['units'] = "%"
           lf_array.attrs['id'] = "sftlf"  # Rename
           ds_lf = lf_array.to_dataset(name='sftlf').compute()
           ds_lf = ds_lf.bounds.add_missing_bounds()
           ds_lf.fillna(1.0e20)
           ds_lf.attrs['model'] = model
           ds_lf.attrs['associated_files'] = mpath
           ds_lf.attrs['history'] = "File processed: " + datetime.datetime.now().strftime("%Y%m%d")
           comp = dict(_FillValue=1.0e20,zlib=True,complevel=5)
           encoding = {var: comp for var in list(ds_lf.data_vars)+list(ds_lf.coords)}
           ds_lf.to_netcdf(mpath_lf,encoding=encoding)
           del(ds,ds_lf,lf_array)

    return 

def archive_data(
        region,stat,season,data_dict,
        model_name,var_names,var_units,
        outdir
    ):
    outdic = pd.DataFrame(data_dict)
    for var in list(outdic.columns.values[3:]):
        if var not in var_names:
           outdic = outdic.drop(columns=[var])
        elif var_units != None:
           # replace the variable with the name + units
           outdic.columns.values[outdic.columns.values.tolist().index(var)] = (
                  var_units[var_names.index(var)])
    # save data to .csv file
    if not os.path.exists(outdir):
       os.makedirs(outdir)
    outfile = "{}_{}_{}_{}.csv".format(stat,region,season,model_name)
    outdic.to_csv(os.path.join(outdir,outfile))
    return

def drop_vars(data_dict,var_names,var_units):
    #drop data if all is NaNs
    for column in data_dict.columns:
        if column not in ['model','run','model_run','num_runs']:
            nnans = data_dict[column].isnull().sum()
            nsize = data_dict[column].size
            if nnans > 0.9*nsize:
                data_dict = data_dict.drop(column, axis=1)
                index = var_names.index(column)
                var_names.remove(var_names[index])
                if var_units != None:
                    var_units.remove(var_units[index])
    return data_dict, var_names, var_units

def variability_modes_plot_driver(
        metric,stat,model_name,
        metric_dict,df_dict,
        mode_season_list,
        save_data,out_path
    ):
    """Driver Function for the modes variability metrics plot"""
    season = "mon"
    for mtype in metric_dict['type']:
        if mtype == "portrait":
            print("Processing Portrait  Plots for {} {}....".format(metric,stat))
            if stat not in ["stdv_pc_ratio_to_obs"]:
                data_nor = normalize_by_median(
                        df_dict[mode_season_list].to_numpy().T, axis=1)
            else:
                data_nor = df_dict[mode_season_list].to_numpy().T
            if save_data:
                df_dict[mode_season_list] = data_nor.T
                outdir = os.path.join(out_path,metric)
                archive_data(metric,stat,season,df_dict,model_name,
                        mode_season_list,None,outdir)
            run_list = df_dict['model'].to_list() 
            stat_name = metric_dict['name']
            portrait_metric_plot(metric,stat,season,data_nor,
                                 stat_name,model_name,mode_season_list,
                                 run_list,out_path)
        elif mtype == "parcoord":
            print("Processing Parallel Coordinate Plots for {} {}....".format(metric,stat))
            #drop data if all is NaNs
            data_dict,var_names,var_units = drop_vars(df_dict.copy(),mode_season_list.copy(),None)
            if save_data:
                outdir = os.path.join(out_path,metric)
                archive_data(metric,stat,season,data_dict,model_name,
                        mode_season_list,None,outdir)
            run_list = data_dict['model'].to_list() 
            stat_name = metric_dict['name']
            parcoord_metric_plot(metric,stat,season,data_dict,
                                 stat_name,model_name,
                                 var_names,var_units,
                                 run_list,out_path)

    return 

def mean_climate_plot_driver(
        metric,stat,regions,model_name,
        metric_dict,df_dict,
        var_list,var_unit_list,
        save_data,out_path
    ):
    """Driver Function for the mean climate metrics plot"""
    for region in regions:
        if metric_dict['type'] == "portrait":
            print("Processing Portrait  Plots for {} {} {}....".format(metric,region,stat))
            var_names = sorted(var_list.copy())
            #label information
            var_units = []
            for i,var in enumerate(var_names):
                index = var_list.index(var)
                var_units.append(var_unit_list[index])
            data_nor = dict()
            for season in metric_dict['season']:
                data_dict = df_dict[season][region].copy()
                if stat == "cor_xy":
                   data_nor[season] = data_dict[var_names].to_numpy().T
                else:
                   data_nor[season] = normalize_by_median(
                      data_dict[var_names].to_numpy().T, axis=1)
                if save_data:
                   outdir = os.path.join(out_path,metric,region)
                   outdic = data_dict.drop(columns=["model_run"]).copy()
                   outdic[var_names] = data_nor[season].T
                   archive_data(region,stat,season,data_dict,model_name,
                                var_names,var_units,outdir)
            run_list = data_dict['model'].to_list()
            stat_name = metric_dict['name']
            outdir = os.path.join(out_path,metric)
            portrait_metric_plot(region,stat,metric,data_nor,
                                 stat_name,model_name,var_names,
                                 run_list,outdir)

        elif metric_dict['type'] == "parcoord":
            print("Processing Parallel Coordinate Plots for {} {} {}....".format(metric,region,stat))
            for season in metric_dict['season']:
                #drop data if all is NaNs
                data_dict,var_names,var_units = drop_vars(
                        df_dict[season][region].copy(),
                        var_list.copy(),
                        var_unit_list.copy())
                if save_data:
                    outdir = os.path.join(out_path,metric,region)
                    outdic = data_dict.drop(columns=["model_run"]).copy()
                    archive_data(region,stat,season,outdic,model_name,
                                 var_list,var_unit_list,outdir)
                run_list = data_dict['model'].to_list()
                stat_name = metric_dict['name']
                outdir = os.path.join(out_path,metric)
                parcoord_metric_plot(region,stat,metric,data_dict,
                                     stat_name,model_name,
                                     var_names,var_units,
                                     run_list,outdir)
    return 

def parcoord_metric_plot(
        region,stat,group,data_dict,
        stat_name,model_name,
        var_names,var_units,
        model_list,out_path
    ):
    """ Function for parallel coordinate plots """
    fontsize = 18
    figsize = (40, 18)
    shrink = 0.8
    legend_box_xy = (1.08, 1.18)
    legend_box_size = 4
    legend_lw = 1.5
    legend_fontsize = fontsize * 0.8
    legend_ncol = int(7 * figsize[0] / 40.0)
    legend_posistion = (0.50, -0.14)
    # hide markers for CMIP models
    identify_all_models = False
    # colors for highlight lines
    xcolors = ["#000000","#e41a1c","#ff7f00","#4daf4a","#f781bf",
               "#a65628","#984ea3","#999999","#377eb8","#dede00"]

    highlight_model1 = []
    for model in data_dict['model'].to_list():
        if "e3sm" in model.lower():
           highlight_model1.append(model)
        elif model in model_name:
           highlight_model1.append(model_name)

    # ensemble mean for CMIP group
    irow_sub = data_dict[data_dict['model'] == highlight_model1[0]].index[0]
    data_dict.loc["CMIP MMM"] = data_dict[:irow_sub].mean(
            numeric_only=True, skipna=True)
    data_dict.at["CMIP MMM", "model"] = "CMIP MMM"
    data_dict.loc["E3SM MMM"] = data_dict[irow_sub:].mean(
            numeric_only=True, skipna=True)
    data_dict.at["E3SM MMM", "model"] = "E3SM MMM"

    model_list = data_dict['model'].to_list()
    highlight_model2 = data_dict['model'].to_list()[-3:]

    var_name1 = sorted(var_names.copy())
    #label information
    var_labels = []
    for i,var in enumerate(var_name1):
        index = var_names.index(var)
        if var_units != None:
            var_labels.append(var_names[index] + "\n"  + var_units[index])
        else:
            var_labels.append(var_names[index])

    #final plot data
    data_var = data_dict[var_name1].to_numpy()

    xlabel = "Metric"
    ylabel = '{} ({})'.format(stat_name,stat.upper())
    # colors for highlight lines
    lncolors = xcolors[1 : len(highlight_model2)] + [xcolors[0]]
    color_map = "tab20_r" 

    if "mean_climate" in [group,region]: 
        title = "Model Performance of Annual Climatology ({}, {})".format(
                 stat.upper(), region.upper())
    elif "variability_modes" in [group,region]:
        title = "Model Performance of Modes Variability ({})".format(
                 stat.upper())
    elif "enso" in [group,region]: 
        title = "Model Performance of ENSO ({})".format(
                 stat.upper())

    fig,ax = parallel_coordinate_plot(
        data_var,
        var_labels,
        model_list,
        model_names2=highlight_model1,
        group1_name="CMIP6",
        group2_name="E3SM",
        models_to_highlight=highlight_model2,
        models_to_highlight_colors=lncolors,
        models_to_highlight_labels=highlight_model2,
        identify_all_models=identify_all_models,
        vertical_center="median",
        vertical_center_line=True,
        title=title,
        figsize=figsize,
        colormap=color_map,
        show_boxplot=False,
        show_violin=True,
        violin_colors=("lightgrey", "pink"),
        legend_ncol=legend_ncol,
        legend_bbox_to_anchor=legend_posistion,
        legend_fontsize=fontsize * 0.85,
        xtick_labelsize=fontsize * 0.95,
        ytick_labelsize=fontsize * 0.95,
        logo_rect=[0, 0, 0, 0],
        logo_off=True)
    
    ax.set_xlabel(xlabel, fontsize = fontsize * 1.1)
    ax.set_ylabel(ylabel, fontsize = fontsize * 1.1)
    ax.set_title(title,   fontsize = fontsize * 1.1)

    # Save figure as an image file
    outdir = os.path.join(out_path,region)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outfile = "{}_{}_parcoord_{}.png".format(stat,region,group)
    fig.savefig(os.path.join(outdir,outfile),facecolor="w", bbox_inches="tight")
    plt.close(fig)

    return 

def portrait_metric_plot(
        region,stat,group,data_dict,
        stat_name,model_name,
        var_list,model_list,
        out_path
    ):
    # process figure
    fontsize = 20
    add_vertical_line = True
    figsize = (40, 18)
    legend_box_xy = (1.08, 1.18)
    legend_box_size = 4
    legend_lw = 1.5
    shrink = 0.8
    legend_fontsize = fontsize * 0.8

    if group == "mean_climate":
       # data for final plot
       data_all_nor = np.stack(
          [data_dict["djf"], data_dict["mam"], data_dict["jja"], data_dict["son"]]
       )
       legend_on = True
       legend_labels = ["DJF", "MAM", "JJA", "SON"]
    else:
       data_all_nor = data_dict
       legend_on = False
       legend_labels = []

    lable_colors = []
    highlight_models = []
    for model in model_list:
        if "e3sm" in model.lower():
           highlight_models.append(model)
           lable_colors.append("#5170d7")
        elif model in model_name:
           highlight_models.append(model_name)
           lable_colors.append("#FC5A50")
        else:
           lable_colors.append("#000000")

    if stat in ["cor_xy"]:
       var_range = (0, 1.0)
       cmap_color = "viridis" 
       cmap_bounds = np.linspace(0,1,21)
    elif stat in ["stdv_pc_ratio_to_obs"]:
       var_range = (0.5, 1.5)
       cmap_color = 'jet'
       cmap_bounds = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
       cmap_bounds = [r/10 for r in range(5, 16, 1)]
    else:
       var_range = (-0.5, 0.5)
       cmap_color = "RdYlBu_r"
       cmap_bounds = np.linspace(-0.5,0.5,11)
     
    fig, ax, cbar = portrait_plot(
            data_all_nor,
            xaxis_labels=model_list,
            yaxis_labels=var_list,
            cbar_label=stat_name,
            cbar_label_fontsize=fontsize * 1.0,
            cbar_tick_fontsize=fontsize,
            box_as_square=True,
            vrange=var_range,
            figsize=figsize,
            cmap=cmap_color,
            cmap_bounds=cmap_bounds,
            cbar_kw={"extend": "both", "shrink": shrink},
            missing_color="white",
            legend_on=legend_on,
            legend_labels=legend_labels,
            legend_box_xy=legend_box_xy,
            legend_box_size=legend_box_size,
            legend_lw=legend_lw,
            legend_fontsize=legend_fontsize,
            logo_rect=[0, 0, 0, 0],
            logo_off=True)

    ax.axvline(x=len(model_list)-len(highlight_models),color="k",linewidth=3)
    ax.set_xticklabels(model_list,rotation=45,va="bottom",ha="left")
    ax.set_yticklabels(var_list,rotation=0,va="center",ha="right")
    for xtick,color in zip(ax.get_xticklabels(),lable_colors):
        xtick.set_color(color)
    ax.yaxis.label.set_color(lable_colors[0])

    # Save figure as an image file
    outdir = os.path.join(out_path,region)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outfile = "{}_{}_portrait_{}.png".format(stat,region,group)
    fig.savefig(os.path.join(outdir,outfile),facecolor="w", bbox_inches="tight")
    plt.close(fig)

    return

def collect_clim_diags(regions,variables,fig_format,model_name,case_id,input_dir,output_dir):
    diag_metric = "mean_climate"
    seasons = ['DJF','MAM','JJA','SON','AC']
    input_dir = input_dir.replace("%(metric_type)",diag_metric)

    #group figures 
    fig_sets = OrderedDict()
    fig_sets['CLIM_patttern'] = ['graphics','*']
    for fset in fig_sets.keys():
      for region in regions:
        for season in seasons:
          for var in variables:
             indir = input_dir.replace('%(output_type)',fig_sets[fset][0]) 
             fpaths = sorted(glob.glob(os.path.join(indir,var,
                     '{}{}_{}*.{}'.format(fig_sets[fset][1],region,season,fig_format))))
             for fpath in fpaths:
                refname = fpath.split("/")[-1].split("_")
                filname = '{}_{}_{}.{}'.format(refname[0],region,season,fig_format)
                outpath = os.path.join(
                            output_dir.replace("%(group_type)",fset),
                            region,season)
                if not os.path.exists(outpath):
                   os.makedirs(outpath)
                outfile = os.path.join(outpath,filname)
                os.rename(fpath,outfile)

    #orgnize metrics jason file
    inpath = input_dir.replace('%(output_type)','metrics_results')
    outpath = output_dir.replace('%(group_type)','metrics_data')
    if not os.path.exists(outpath):
          os.makedirs(outpath)
    fpaths = sorted(glob.glob(os.path.join(inpath,'*.json')))
    for fpath in fpaths:
       refname = fpath.split("/")[-1].split("_")
       filname = '{}.{}.{}.{}.json'.format( 
                    refname[0],refname[1],model_name,case_id,
                  )
       outfile = os.path.join(outpath,filname)
       os.rename(fpath,outfile)
    return

def collect_movs_diags(modes,fig_format,model_name,case_id,input_dir,output_dir):
    diag_metric = "variability_modes"
    seasons = ['DJF','MAM','JJA','SON','yearly','monthly']
    input_dir = input_dir.replace("%(metric_type)",diag_metric)

    #group figures
    fig_sets = OrderedDict()
    fig_sets['MOV_eoftest'] = ['diagnostic_results','EG_Spec*']
    fig_sets['MOV_compose'] = ['graphics','*compare_obs']
    fig_sets['MOV_telecon'] = ['graphics','*teleconnection']
    fig_sets['MOV_pattern'] = ['graphics','*']
    
    for fset in fig_sets.keys():
      for mode in modes:
        for season in seasons:
            if fset == "MOV_eoftest":
               indir = input_dir.replace('%(output_type)',fig_sets[fset][0]) 
               template = '{}_{}_{}*.{}'.format(fig_sets[fset][1],mode,season,fig_format)
            else:
               indir = input_dir.replace('%(output_type)',fig_sets[fset][0]) 
               template = '{}*_{}*_{}.{}'.format(mode,season,fig_sets[fset][1],fig_format)
            fpaths = sorted(glob.glob(os.path.join(indir,mode,'*',template)))
            for fpath in fpaths:
                refname = fpath.split("/")[-2]
                filname = fpath.split("/")[-1]
                if "_cbf_" in filname:
                   outfile = '{}_{}_{}_cbf.{}'.format(fset,mode,season,fig_format)
                elif "EOF1" in filname:
                   outfile = '{}_{}_{}_eof1.{}'.format(fset,mode,season,fig_format)
                elif "EOF2" in filname:
                   outfile = '{}_{}_{}_eof2.{}'.format(fset,mode,season,fig_format)
                elif "EOF3" in filname:
                   outfile = '{}_{}_{}_eof3.{}'.format(fset,mode,season,fig_format)
                outpath = os.path.join(
                            output_dir.replace("%(group_type)","MOV_metric"),
                            fset,season)
                if not os.path.exists(outpath):
                   os.makedirs(outpath)
                os.rename(fpath,os.path.join(outpath,outfile))

    #orgnize metrics jason file
    inpath = input_dir.replace('%(output_type)','metrics_results')
    outpath = output_dir.replace('%(group_type)','metrics_data')
    if not os.path.exists(outpath):
          os.makedirs(outpath)
    fpaths = sorted(glob.glob(os.path.join(inpath,diag_metric,'*/*/*.json')))
    for fpath in fpaths:
       refmode = fpath.split("/")[-3] 
       refname = fpath.split("/")[-2]
       reffile = fpath.split("/")[-1]
       filname = '{}.{}.{}.{}.json'.format(
                    refmode,refname,model_name,case_id,
                  )
       if 'diveDown' in reffile:
          outfile = os.path.join(outpath,filname.replace(".json","diveDown.json")) 
       else:
          outfile = os.path.join(outpath,filname)
       os.rename(fpath,outfile)
    return

def collect_enso_diags(groups,fig_format,refname,model_name,case_id,input_dir,output_dir):
    diag_metric = "enso_metric"
    input_dir = input_dir.replace("%(metric_type)",diag_metric)

    #group figures
    fig_sets = OrderedDict()
    fig_sets['ENSO_metric'] = ['graphics','*']
    for fset in fig_sets.keys():
      for group in groups:
         fdir = input_dir.replace('%(output_type)',fig_sets[fset][0] )
         fpaths = sorted(glob.glob(os.path.join(fdir,group,
                         '{}.{}'.format(fig_sets[fset][1],fig_format))))
         for fpath in fpaths:
             filname = fpath.split("/")[-1].split("_")
             outpath = os.path.join(output_dir.replace("%(group_type)",fset),group)
             if not os.path.exists(outpath):
                os.makedirs(outpath)
             outfile = '{}_{}_{}_{}'.format(group,filname[-3],filname[-2],filname[-1])
             os.rename(fpath,os.path.join(outpath,outfile))

    #orgnize metrics jason file
    inpath = input_dir.replace('%(output_type)','metrics_results')
    outpath = output_dir.replace('%(group_type)','metrics_data')
    if not os.path.exists(outpath):
          os.makedirs(outpath)
    fpaths = sorted(glob.glob(os.path.join(inpath,diag_metric,'*/*.json')))
    for fpath in fpaths:
       refmode = fpath.split("/")[-2]
       reffile = fpath.split("/")[-1]
       filname = '{}.{}.{}.{}.json'.format(
                    refmode,refname,model_name,case_id,
                  )
       if 'diveDown' in reffile:
          outfile = os.path.join(outpath,filname.replace(".json","diveDown.json"))
       else:
          outfile = os.path.join(outpath,filname)
       os.rename(fpath,outfile)
    return

