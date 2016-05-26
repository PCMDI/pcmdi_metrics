#!/usr/bin/env python
#
#
#  USER INPUT IS SET IN FILE "input_parameters.py"
#  Identified via --parameters key at startup
#
#
import pcmdi_metrics
import sys
import argparse
import os
import json
import genutil
import warnings
import cdms2
import MV2
import cdutil
import collections
import cdat_info

# Statistical tracker
cdat_info.pingPCMDIdb("pcmdi_metrics", "pcmdi_metrics_driver")

# Before we do anything else we need to create some units
# Salinity Units
import unidata
unidata.udunits_wrap.init()

# Create a dimensionless units named dimless
unidata.addDimensionlessUnit("dimless")

# Created scaled units for dimless
unidata.addScaledUnit("psu", .001, "dimless")
unidata.addScaledUnit("PSS-78", .001, "dimless")
unidata.addScaledUnit("Practical Salinity Scale 78", .001, "dimless")

regions_values = {"land": 100., "ocean": 0., "lnd": 100., "ocn": 0.}

# Load the obs dictionary
fjson = open(
    os.path.join(
        pcmdi_metrics.__path__[0],
        "..",
        "..",
        "..",
        "..",
        "share",
        "pcmdi",
        "obs_info_dictionary.json"))
obs_dic = json.loads(fjson.read())
fjson.close()


class DUP(object):

    def __init__(self, outfile):
        self.outfile = outfile

    def __call__(self, *args):
        msg = ""
        for a in args:
            msg += " " + str(a)
        print msg
        print>>self.outfile, msg


def applyCustomKeys(O, custom_dict, var):
    for k, v in custom_dict.iteritems():
        setattr(O, k, custom_dict.get(var, custom_dict.get(None, "")))

P = argparse.ArgumentParser(
    description='Runs PCMDI Metrics Computations',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

P.add_argument(
    "-p",
    "--parameters",
    dest="param",
    default="input_parameters.py",
    help="input parameter file containing local settings",
    required=True)

args = P.parse_args(sys.argv[1:])

pth, fnm = os.path.split(args.param)
if pth != "":
    sys.path.append(pth)
if fnm.lower()[-3:] == ".py":
    fnm = fnm[:-3]
    ext = ".py"
else:
    ext = ""
# We need to make sure there is no "dot" in filename or import will fail
if fnm.find(".") > -1:
    raise ValueError(
        "Sorry input parameter file name CANNOT contain" +
        " 'dots' (.), please rename it (e.g: %s%s)" %
        (fnm.replace(
            ".",
            "_"),
            ext))
sys.path.insert(0, os.getcwd())
parameters = ""  # dummy so flake8 knows about parameters
exec("import %s as parameters" % fnm)
if pth != "":
    sys.path.pop(-1)

# Checking if we have custom obs to add
if hasattr(parameters, "custom_observations"):
    fjson2 = open(parameters.custom_observations)
    obs_dic.update(json.load(fjson2))
    fjson2.close()

# Checking if user has custom_keys
if not hasattr(parameters, "custom_keys"):
    parameters.custom_keys = {}

# See if we have model tweaks for ALL models
# If not makes it empty dictionary
if hasattr(parameters, "model_tweaks"):
    tweaks_all = parameters.model_tweaks.get(None, {})
else:
    tweaks_all = {}

out = pcmdi_metrics.io.base.Base(
    os.path.abspath(
        os.path.join(
            parameters.metrics_output_path)),
            "errors_log.txt")
case_id = getattr(parameters, "case_id", "")
period = getattr(parameters, "period", "")

out.case_id = case_id
out = out()

try:
    os.makedirs(
        os.path.dirname(out)
    )
except:
    pass

Efile = open(out, "w")

dup = DUP(Efile)


# First of all attempt to prepare sftlf before/after for all models
sftlf = {}
# LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
for model_version in parameters.model_versions:
    sft = pcmdi_metrics.io.base.Base(
        parameters.mod_data_path,
        getattr(
            parameters,
            "sftlf_filename_template",
            parameters.filename_template))
    sft.model_version = model_version
    sft.table = "fx"
    sft.realm = "atmos"
    sft.period = period
    sft.ext = "nc"
    sft.case_id = case_id
    sft.targetGrid = None
    sft.realization = "r0i0p0"
    applyCustomKeys(sft, parameters.custom_keys, "sftlf")
    try:
        sftlf[model_version] = {"raw": sft.get("sftlf")}
        sftlf[model_version]["filename"] = os.path.basename(sft())
        sftlf[model_version]["md5"] = sft.hash()
    except:
        # Hum no sftlf...
        dup("No mask for ", sft())
        sftlf[model_version] = {"raw": None}
        sftlf[model_version]["filename"] = None
        sftlf[model_version]["md5"] = None
if parameters.targetGrid == "2.5x2.5":
    tGrid = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
else:
    tGrid = parameters.targetGrid

sft = cdutil.generateLandSeaMask(tGrid)
sft[:] = sft.filled(1.) * 100.
sftlf["targetGrid"] = sft

# At this point we need to create the tuples var/region to know if a
# variable needs to be ran over a specific region or global or both
regions = getattr(parameters, "regions", {})
vars = []

# Update/overwrite defsult region_values keys with user ones

regions_values.update(getattr(parameters, "regions_values", {}))


regions_dict = {}
for var in parameters.vars:
    vr = var.split("_")[0]
    rg = regions.get(vr, [None, ])
    if not isinstance(rg, (list, tuple)):
        rg = [rg, ]
    regions_dict[vr] = rg
saved_obs_masks = {}

disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pcmdi",
        "disclaimer.txt")).read()
for Var in parameters.vars:  # CALCULATE METRICS FOR ALL VARIABLES IN vars
    try:
        metrics_dictionary = collections.OrderedDict()
        metrics_def_dictionary = collections.OrderedDict()
        metrics_dictionary["DISCLAIMER"] = disclaimer
        metrics_dictionary["RESULTS"] = collections.OrderedDict()
        # REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID (ATM OR OCN GRID)
        sp = Var.split("_")
        var = sp[0]
        if len(sp) > 1:
            level = float(sp[-1]) * 100.
        else:
            level = None

        if obs_dic[var][obs_dic[var]["default"]]["CMIP_CMOR_TABLE"] == "Omon":
            regridMethod = parameters.regrid_method_ocn
            regridTool = parameters.regrid_tool_ocn
            table_realm = 'Omon'
            realm = "ocn"
        else:
            regridMethod = parameters.regrid_method
            regridTool = parameters.regrid_tool
            table_realm = 'Amon'
            realm = "atm"
        grd = {}
        grd["RegridMethod"] = regridMethod
        grd["RegridTool"] = regridTool
        grd["GridName"] = parameters.targetGrid

        # Ok at that stage we need to loop thru obs
        dup('parameter file ref is: ', parameters.ref)
        refs = parameters.ref
        if isinstance(refs, list) and "all" in [x.lower() for x in refs]:
            refs = "all"
        if isinstance(refs, (unicode, str)):
            # Is it "all"
            if refs.lower() == "all":
                Refs = obs_dic[var].keys()
                refs = []
                for r in Refs:
                    if isinstance(obs_dic[var][r], (unicode, str)):
                        refs.append(r)
                dup("refs:", refs)
            else:
                refs = [refs, ]
        dup('ref is: ', refs)

        OUT = pcmdi_metrics.io.base.Base(
            parameters.metrics_output_path,
            "%(var)%(level)_%(targetGridName)_" +
            "%(regridTool)_%(regridMethod)_metrics")
        OUT.setTargetGrid(parameters.targetGrid, regridTool, regridMethod)
        OUT.var = var
        OUT.realm = realm
        OUT.table = table_realm
        OUT.case_id = case_id
        applyCustomKeys(OUT, parameters.custom_keys, var)
        metrics_dictionary["References"] = {}
        metrics_dictionary["RegionalMasking"] = {}
        for region in regions_dict[var]:
            if isinstance(region, str):
                region_name = region
                region = regions_values.get(
                    region_name,
                    regions_values.get(
                        region_name.lower()))
            elif region is None:
                region_name = "global"
            else:
                region_name = "%i" % region
            metrics_dictionary["RegionalMasking"][region_name] = region
            for ref in refs:
                if ref[:9] in ["default", "alternate"]:
                    refabbv = ref + "Reference"
                else:
                    refabbv = ref
                if isinstance(obs_dic[var][ref], (str, unicode)):
                    obs_var_ref = obs_dic[var][obs_dic[var][ref]]
                else:
                    obs_var_ref = obs_dic[var][ref]
                metrics_dictionary["References"][ref] = obs_var_ref
                try:
                    if obs_var_ref["CMIP_CMOR_TABLE"] == "Omon":
                        OBS = pcmdi_metrics.pcmdi.io.OBS(
                            parameters.obs_data_path,
                            var,
                            obs_dic,
                            ref)
                    else:
                        OBS = pcmdi_metrics.pcmdi.io.OBS(
                            parameters.obs_data_path,
                            var,
                            obs_dic,
                            ref)
                    OBS.setTargetGrid(
                        parameters.targetGrid,
                        regridTool,
                        regridMethod)
                    OBS.realm = realm
                    OBS.table = table_realm
                    OBS.case_id = case_id
                    applyCustomKeys(OBS, parameters.custom_keys, var)
                    if region is not None:
                        # Ok we need to apply a mask
                        # First try to read from obs json file
                        try:
                            oMask = pcmdi_metrics.pcmdi.io.OBS(
                                parameters.obs_data_path,
                                "sftlf",
                                obs_dic,
                                obs_var_ref["RefName"])
                            oMasknm = oMask()
                        except Exception as err:
                            dup("error retrieving mask for obs: %s, \n%s" %
                                (obs_dic[var][ref], err))
                            oMasknm = "%s_%s" % (var, ref)
                        tmpoMask = saved_obs_masks.get(oMasknm, None)
                        if tmpoMask is not None:
                            # ok we got this one already
                            oMask = tmpoMask
                        else:
                            try:
                                oMask = oMask.get("sftlf")
                            # ok that failed falling back on autogenerate
                            except:
                                dup("Could not find obs mask, generating")
                                foGrd = cdms2.open(OBS())
                                oGrd = foGrd(var, time=slice(0, 1))
                                foGrd.close()
                                oMask = cdutil.generateLandSeaMask(
                                    oGrd,
                                    regridTool=regridTool).filled(1.) * 100.
                                oMask = MV2.array(oMask)
                                oMask.setAxis(-1, oGrd.getLongitude())
                                oMask.setAxis(-2, oGrd.getLatitude())
                            saved_obs_masks[oMasknm] = oMask
                        OBS.mask = MV2.logical_not(MV2.equal(oMask, region))
                        OBS.targetMask = MV2.logical_not(
                            MV2.equal(
                                sftlf["targetGrid"],
                                region))
                    try:
                        if level is not None:
                            do = OBS.get(var, level=level)
                        else:
                            do = OBS.get(var)
                    except Exception as err:
                        dup('failed with 4D OBS', var, ref, err)
                        continue
                    grd["GridResolution"] = do.shape[1:]
                    metrics_dictionary["GridInfo"] = grd

                    dup('OBS SHAPE IS ', do.shape)

                    # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM
                    # input_model_data.py
                    for model_version in parameters.model_versions:
                        success = True
                        # See if we have model tweaks for THIS model
                        # If not makes it empty dictionary
                        if hasattr(parameters, "model_tweaks"):
                            tweaks = parameters.model_tweaks.get(
                                model_version,
                                {})
                        else:
                            tweaks = {}

                        while success:

                            MODEL = pcmdi_metrics.io.base.Base(
                                parameters.mod_data_path,
                                parameters.filename_template)
                            MODEL.model_version = model_version
                            MODEL.table = table_realm
                            MODEL.realm = realm
                            MODEL.period = period
                            MODEL.ext = "nc"
                            MODEL.case_id = case_id
                            MODEL.setTargetGrid(
                                parameters.targetGrid,
                                regridTool,
                                regridMethod)
                            MODEL.realization = parameters.realization
                            applyCustomKeys(MODEL, parameters.custom_keys, var)
                            varInFile = tweaks.get(
                                "variable_mapping",
                                {}).get(
                                var,
                                None)
                            # ok no mapping for THIS model
                            if varInFile is None:
                                # Trying to get the "All models" mapping and
                                # fallback and var we are using
                                varInFile = tweaks_all.get(
                                    "variable_mapping",
                                    {}).get(
                                    var,
                                    var)
                            if region is not None:
                                if sftlf[model_version]["raw"] is None:
                                    if not hasattr(
                                        parameters, "generate_sftlf") or \
                                            parameters.generate_sftlf is False:
                                        dup("Model %s does not have sftlf, " % model_version +
                                            "skipping region: %s" % region)
                                        success = False
                                        continue
                                    else:
                                        # ok we can try to generate the sftlf
                                        MODEL.variable = var
                                        dup("auto generating sftlf " +
                                            "for model %s " %
                                            MODEL())
                                        if os.path.exists(MODEL()):
                                            fv = cdms2.open(MODEL())
                                            Vr = fv[varInFile]
                                            # Need to recover only first
                                            # time/leve/etc...
                                            N = Vr.rank() - 2  # minus lat/lon
                                            sft = cdutil.generateLandSeaMask(
                                                Vr(*(slice(0, 1),) * N)) * 100.
                                            sft[:] = sft.filled(100.)
                                            sftlf[model_version]["raw"] = sft
                                            fv.close()
                                            dup("auto generated sftlf" +
                                                " for model %s " %
                                                model_version)

                                MODEL.mask = MV2.logical_not(
                                    MV2.equal(
                                        sftlf[model_version]["raw"],
                                        region))
                                MODEL.targetMask = MV2.logical_not(
                                    MV2.equal(
                                        sftlf["targetGrid"],
                                        region))
                            try:
                                if level is None:
                                    OUT.level = ""
                                    dm = MODEL.get(
                                        var,
                                        varInFile=varInFile)  # +"_ac")
                                else:
                                    OUT.level = "-%i" % (int(level / 100.))
                                    # Ok now fetch this
                                    dm = MODEL.get(
                                        var,
                                        varInFile=varInFile,
                                        level=level)
                            except Exception as err:
                                success = False
                                dup('Failed to get variable %s ' % var +
                                    'for version: %s, error:\n%s' % (
                                        model_version, err))
                                break

                            dup(var,
                                ' ',
                                model_version,
                                ' ',
                                dm.shape,
                                ' ',
                                do.shape,
                                '  ',
                                ref)
                            #
                            # Basic checks
                            #
                            if dm.shape != do.shape:
                                raise RuntimeError(
                                    "Obs and Model -%s- have different" % model_version +
                                    "shapes %s vs %s" %
                                    (do.shape, dm.shape))
                            # Ok possible issue with units
                            if hasattr(dm, "units") and do.units != dm.units:
                                u = genutil.udunits(1, dm.units)
                                try:
                                    scaling, offset = u.how(do.units)
                                    dm = dm * scaling + offset
                                    wrn = "Model and observation units differed, converted model" +\
                                          "(%s) to observation unit (%s) scaling: %g offset: %g" % (
                                              dm.units, do.units, scaling, offset)
                                    warnings.warn(wrn)
                                except:
                                    raise RuntimeError(
                                        "Could not convert model units (%s) " % dm.units +
                                        "to obs units: (%s)" % (do.units))

                            #
                            # OBS INFO FOR JSON/ASCII FILES
                            #
                            onm = obs_dic[var][ref]

                            #
                            # METRICS CALCULATIONS
                            #
                            metrics_dictionary["RESULTS"][model_version] = \
                                metrics_dictionary["RESULTS"].get(
                                model_version,
                                {})
                            # Stores model's simul description
                            if "SimulationDescription" not in \
                                    metrics_dictionary["RESULTS"][model_version]:
                                descr = {"MIPTable":
                                         obs_var_ref["CMIP_CMOR_TABLE"],
                                         "Model": model_version,
                                         }

                                sim_descr_mapping = {
                                    "ModelActivity": "project_id",
                                    "ModellingGroup": "institute_id",
                                    "Experiment": "experiment",
                                    "ModelFreeSpace": "ModelFreeSpace",
                                    "Realization": "realization",
                                    "creation_date": "creation_date",
                                }

                                sim_descr_mapping.update(
                                    getattr(
                                        parameters,
                                        "simulation_description_mapping",
                                        {}))
                                for att in sim_descr_mapping.keys():
                                    nm = sim_descr_mapping[att]
                                    if not isinstance(nm, (list, tuple)):
                                        nm = ["%s", nm]
                                    fmt = nm[0]
                                    vals = []
                                    for a in nm[1:]:
                                        # First trying from parameter file
                                        if hasattr(parameters, a):
                                            vals.append(getattr(parameters, a))
                                        # Now fall back on file...
                                        else:
                                            f = cdms2.open(MODEL())
                                            if hasattr(f, a):
                                                try:
                                                    vals.append(
                                                        float(
                                                            getattr(
                                                                f,
                                                                a)))
                                                except:
                                                    vals.append(getattr(f, a))
                                            # Ok couldn't find it anywhere
                                            # setting to N/A
                                            else:
                                                vals.append("N/A")
                                            f.close()
                                    descr[att] = fmt % tuple(vals)
                                metrics_dictionary[
                                    "RESULTS"][
                                        model_version][
                                            "units"] = getattr(
                                                dm,
                                                "units",
                                                "N/A")
                                metrics_dictionary["RESULTS"][model_version][
                                    "SimulationDescription"] = descr
                                metrics_dictionary["RESULTS"][model_version][
                                    "InputClimatologyFileName"] = \
                                    os.path.basename(MODEL())
                                metrics_dictionary["RESULTS"][model_version][
                                    "InputClimatologyMD5"] = MODEL.hash()
                                # Not just global
                                if len(regions_dict[var]) > 1:
                                    metrics_dictionary["RESULTS"][model_version][
                                        "InputRegionFileName"] = \
                                        sftlf[model_version]["filename"]
                                    metrics_dictionary["RESULTS"][model_version][
                                        "InputRegionMD5"] = \
                                        sftlf[model_version]["md5"]

                            if refabbv not in metrics_dictionary["RESULTS"][model_version]:
                                metrics_dictionary["RESULTS"][model_version][
                                    refabbv] = {'source': onm}
                            pr = metrics_dictionary["RESULTS"][model_version][refabbv].\
                                get(
                                parameters.realization,
                                {})
                            pr_rgn = pcmdi_metrics.pcmdi.compute_metrics(
                                Var,
                                dm,
                                do)
                            # Calling compute metrics with None for model and
                            # obs, triggers it to send back the defs.
                            metrics_def_dictionary.update(
                                pcmdi_metrics.pcmdi.compute_metrics(
                                    Var,
                                    None,
                                    None))
                            #
                            # The follwoing allow users to plug in a set of
                            # custom metrics
                            # Function needs to take in var name,
                            # model clim, obs clim
                            #
                            if hasattr(parameters, "compute_custom_metrics"):
                                pr_rgn.update(
                                    parameters.compute_custom_metrics(
                                        Var,
                                        dm,
                                        do))
                                # Calling compute metrics with None
                                # for model and
                                # obs, triggers it to send back the defs.
                                # But we are wrapping this in an except/try in
                                # case user did not implement
                                try:
                                    metrics_def_dictionary.update(
                                        parameters.compute_custom_metrics(
                                            Var,
                                            None,
                                            None))
                                except:
                                    # Better than nothing we will use the doc
                                    # string
                                    metrics_def_dictionary.update(
                                        {"custom": parameters.
                                         compute_custom_metrics.__doc__})
                            pr[region_name] = collections.OrderedDict(
                                (k,
                                 pr_rgn[k]) for k in sorted(
                                    pr_rgn.keys()))
                            metrics_dictionary["RESULTS"][model_version][refabbv][
                                parameters.realization] = pr

                            # OUTPUT INTERPOLATED MODEL CLIMATOLOGIES
                            # Only the first time thru an obs set (always the
                            # same after)
                            if parameters.save_mod_clims and ref == refs[0]:
                                CLIM = pcmdi_metrics.io.base.Base(
                                    parameters.
                                    model_clims_interpolated_output,
                                    parameters.filename_output_template)
                                CLIM.level = OUT.level
                                CLIM.model_version = model_version
                                CLIM.table = table_realm
                                CLIM.period = period
                                CLIM.case_id = case_id
                                CLIM.setTargetGrid(
                                    parameters.targetGrid,
                                    regridTool,
                                    regridMethod)
                                if level is None:
                                    varid = var
                                else:
                                    varid = "%s_%i" % (var, int(level))
                                CLIM.variable = varid
                                CLIM.region = region_name
                                CLIM.realization = parameters.realization
                                applyCustomKeys(
                                    CLIM,
                                    parameters.custom_keys,
                                    var)
                                CLIM.write(dm, type="nc", id=varid)

                            break
                except Exception as err:
                    dup("Error while processing observation %s" % ref +
                        " for variable %s:\n\t%s" % (
                            var, str(err)))
            # Done with obs and models loops , let's dum before next var
        # Ok at this point we need to add the metrics def in the dictionary so
        # that it is stored
        metrics_dictionary["METRICS"] = metrics_def_dictionary
        # OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES
        OUT.write(
            metrics_dictionary,
            mode="w",
            indent=4,
            separators=(
                ',',
                ': '))
        # CREATE OUTPUT AS ASCII FILE
        OUT.write(metrics_dictionary, mode="w", type="txt")
    except Exception as err:
        dup("Error while processing variable %s:\n\t%s" % (var, err))
