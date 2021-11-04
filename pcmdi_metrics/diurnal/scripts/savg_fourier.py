#!/usr/bin/env python

# Spatially vector-average pairs of lat/lon fields that store Fourier (amplitude, phase) values for the diurnal
# cycle of preciprecipitation. This version does not explicitly mask out areas where the diurnal cycle is weak,
# but such areas should count for little since the vector amplitudes there
# are small.


# This modifiction of ./savg_fourier.py has the PMP Parser "wrapped" around it, so it's executed with both input and
# output parameters specified in the Unix command line.
# ... but this version is designed to get land-sea masks for any model, not just MIROC5 and CCSM4.

# Charles Doutriaux                                     September 2017
# Curt Covey (from ./savg_fourierWrappedInOutCCSMandMIROC.py)
# June 2017

from __future__ import print_function
import cdms2
import cdutil
import MV2
import os
import glob
import pcmdi_metrics
import collections
import json
import pkg_resources
from pcmdi_metrics.diurnal.common import monthname_d, P, populateStringConstructor


def main():
    P.add_argument(
        "-j",
        "--outnamejson",
        type=str,
        dest="outnamejson",
        default="pr_%(month)_%(firstyear)-%(lastyear)_savg_DiurnalFourier.json",
        help="Output name for jsons",
    )

    P.add_argument("--lat1", type=float, default=-50.0, help="First latitude")
    P.add_argument("--lat2", type=float, default=50.0, help="Last latitude")
    P.add_argument("--lon1", type=float, default=0.0, help="First longitude")
    P.add_argument("--lon2", type=float, default=360.0, help="Last longitude")
    P.add_argument(
        "--region_name",
        type=str,
        default="TRMM",
        help="name for the region of interest",
    )

    P.add_argument(
        "-t",
        "--filename_template",
        default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_S.nc",
        help="template for getting at amplitude files",
    )
    P.add_argument(
        "--filename_template_tS",
        default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_tS.nc",
        help="template for phase files",
    )
    P.add_argument(
        "--filename_template_sftlf",
        default="cmip5.%(model).%(experiment).r0i0p0.fx.atm.fx.sftlf.%(version).latestX.xml",
        help="template for sftlf file names",
    )
    P.add_argument("--model", default="*")
    P.add_argument(
        "--cmec",
        dest="cmec",
        action="store_true",
        default=False,
        help="Use to save metrics in CMEC JSON format",
    )
    P.add_argument(
        "--no_cmec",
        dest="cmec",
        action="store_false",
        default=False,
        help="Use to disable saving metrics in CMEC JSON format",
    )

    args = P.get_parameter()
    month = args.month
    monthname = monthname_d[month]
    startyear = args.firstyear
    finalyear = args.lastyear
    years = "%s-%s" % (startyear, finalyear)  # noqa: F841
    cmec = args.cmec

    print("Specifying latitude / longitude domain of interest ...")
    # TRMM (observed) domain:
    latrange = (args.lat1, args.lat2)
    lonrange = (args.lon1, args.lon2)

    region = cdutil.region.domain(latitude=latrange, longitude=lonrange)

    if args.region_name == "":
        region_name = "{:g}_{:g}&{:g}_{:g}".format(*(latrange + lonrange))
    else:
        region_name = args.region_name

    # Amazon basin:
    # latrange = (-15.0,  -5.0)
    # lonrange = (285.0, 295.0)

    # Functions to convert phase between angle-in-radians and hours, for
    # either a 12- or 24-hour clock, i.e. for clocktype = 12 or 24:

    def hrs_to_rad(hours, clocktype):
        import MV2

        return 2 * MV2.pi * hours / clocktype

    def rad_to_hrs(phase, clocktype):
        import MV2

        return phase * clocktype / 2 / MV2.pi

    def vectoravg(hr1, hr2, clocktype):
        "Function to test vector-averaging of two time values:"
        import MV2

        sin_avg = (
            MV2.sin(hrs_to_rad(hr1, clocktype)) + MV2.sin(hrs_to_rad(hr2, clocktype))
        ) / 2
        cos_avg = (
            MV2.cos(hrs_to_rad(hr1, clocktype)) + MV2.cos(hrs_to_rad(hr2, clocktype))
        ) / 2
        return rad_to_hrs(MV2.arctan2(sin_avg, cos_avg), clocktype)

    def spacevavg(tvarb1, tvarb2, sftlf, model):
        """
        Given a "root filename" and month/year specifications, vector-average lat/lon arrays in an (amplitude, phase)
        pair of input data files. Each input data file contains diurnal (24h), semidiurnal (12h) and terdiurnal (8h)
        Fourier harmonic components of the composite mean day/night cycle.

        Vector-averaging means we consider the input data to be readings on an 8-, 12- or 24-hour clock and separately
        average the Cartesian components (called "cosine" and "sine" below). Then the averaged components are combined
        back into amplitude and phase values and returned.

        Space-averaging is done globally, as well as separately for land and ocean areas.
        """

        glolf = cdutil.averager(sftlf, axis="xy")
        print("  Global mean land fraction = %5.3f" % glolf)
        outD = {}  # Output dictionary to be returned by this function
        harmonics = [1, 2, 3]
        for harmonic in harmonics:
            ampl = tvarb1[harmonic - 1]
            tmax = tvarb2[harmonic - 1]
            # print ampl[:, :]
            # print tmax[:, :]
            clocktype = 24 / harmonic
            cosine = MV2.cos(hrs_to_rad(tmax, clocktype)) * ampl  # X-component
            sine = MV2.sin(hrs_to_rad(tmax, clocktype)) * ampl  # Y-component

            print("Area-averaging globally, over land only, and over ocean only ...")
            # Average Cartesian components ...
            cos_avg_glo = cdutil.averager(cosine, axis="xy")
            sin_avg_glo = cdutil.averager(sine, axis="xy")
            cos_avg_lnd = cdutil.averager(cosine * sftlf, axis="xy")
            sin_avg_lnd = cdutil.averager(sine * sftlf, axis="xy")
            cos_avg_ocn = cos_avg_glo - cos_avg_lnd
            sin_avg_ocn = sin_avg_glo - sin_avg_lnd
            # ... normalized by land-sea fraction:
            cos_avg_lnd /= glolf
            sin_avg_lnd /= glolf
            cos_avg_ocn /= 1 - glolf
            sin_avg_ocn /= 1 - glolf
            # Amplitude and phase:
            # * 86400 Convert kg/m2/s -> mm/d?
            amp_avg_glo = MV2.sqrt(sin_avg_glo ** 2 + cos_avg_glo ** 2)
            # * 86400 Convert kg/m2/s -> mm/d?
            amp_avg_lnd = MV2.sqrt(sin_avg_lnd ** 2 + cos_avg_lnd ** 2)
            # * 86400 Convert kg/m2/s -> mm/d?
            amp_avg_ocn = MV2.sqrt(sin_avg_ocn ** 2 + cos_avg_ocn ** 2)
            pha_avg_glo = MV2.remainder(
                rad_to_hrs(MV2.arctan2(sin_avg_glo, cos_avg_glo), clocktype), clocktype
            )
            pha_avg_lnd = MV2.remainder(
                rad_to_hrs(MV2.arctan2(sin_avg_lnd, cos_avg_lnd), clocktype), clocktype
            )
            pha_avg_ocn = MV2.remainder(
                rad_to_hrs(MV2.arctan2(sin_avg_ocn, cos_avg_ocn), clocktype), clocktype
            )
            if "CMCC-CM" in model:
                # print '** Correcting erroneous time recording in ', rootfname
                pha_avg_lnd -= 3.0
                pha_avg_lnd = MV2.remainder(pha_avg_lnd, clocktype)
            elif "BNU-ESM" in model or "CCSM4" in model or "CNRM-CM5" in model:
                # print '** Correcting erroneous time recording in ', rootfname
                pha_avg_lnd -= 1.5
                pha_avg_lnd = MV2.remainder(pha_avg_lnd, clocktype)
            print(
                "Converting singleton transient variables to plain floating-point numbers ..."
            )
            amp_avg_glo = float(amp_avg_glo)
            pha_avg_glo = float(pha_avg_glo)
            amp_avg_lnd = float(amp_avg_lnd)
            pha_avg_lnd = float(pha_avg_lnd)
            amp_avg_ocn = float(amp_avg_ocn)
            pha_avg_ocn = float(pha_avg_ocn)
            print(
                "%s %s-harmonic amplitude, phase = %7.3f mm/d, %7.3f hrsLST averaged globally"
                % (monthname, harmonic, amp_avg_glo, pha_avg_glo)
            )
            print(
                "%s %s-harmonic amplitude, phase = %7.3f mm/d, %7.3f hrsLST averaged over land"
                % (monthname, harmonic, amp_avg_lnd, pha_avg_lnd)
            )
            print(
                "%s %s-harmonic amplitude, phase = %7.3f mm/d, %7.3f hrsLST averaged over ocean"
                % (monthname, harmonic, amp_avg_ocn, pha_avg_ocn)
            )
            # Sub-dictionaries, one for each harmonic component:
            outD["harmonic" + str(harmonic)] = {}
            outD["harmonic" + str(harmonic)]["amp_avg_lnd"] = amp_avg_lnd
            outD["harmonic" + str(harmonic)]["pha_avg_lnd"] = pha_avg_lnd
            outD["harmonic" + str(harmonic)]["amp_avg_ocn"] = amp_avg_ocn
            outD["harmonic" + str(harmonic)]["pha_avg_ocn"] = pha_avg_ocn
        return outD

    print("Preparing to write output to JSON file ...")
    if not os.path.exists(args.results_dir):
        os.makedirs(args.results_dir)
    jsonFile = populateStringConstructor(args.outnamejson, args)
    jsonFile.month = monthname

    jsonname = os.path.join(os.path.abspath(args.results_dir), jsonFile())

    if not os.path.exists(jsonname) or args.append is False:
        print("Initializing dictionary of statistical results ...")
        stats_dic = {}
        metrics_dictionary = collections.OrderedDict()
    else:
        with open(jsonname) as f:
            metrics_dictionary = json.load(f)
            stats_dic = metrics_dictionary["RESULTS"]

    OUT = pcmdi_metrics.io.base.Base(
        os.path.abspath(args.results_dir), os.path.basename(jsonname)
    )
    try:
        egg_pth = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse("pcmdi_metrics"), "share/pmp"
        )
    except Exception:
        # python 2 seems to fail when ran in home directory of source?
        egg_pth = os.path.join(os.getcwd(), "share", "pmp")
    disclaimer = open(os.path.join(egg_pth, "disclaimer.txt")).read()
    metrics_dictionary["DISCLAIMER"] = disclaimer
    metrics_dictionary[
        "REFERENCE"
    ] = "The statistics in this file are based on Covey et al., J Climate 2016"

    # Accumulate output from each model (or observed) data source in the
    # Python dictionary.
    template_S = populateStringConstructor(args.filename_template, args)
    template_S.month = monthname
    template_tS = populateStringConstructor(args.filename_template_tS, args)
    template_tS.month = monthname
    template_sftlf = populateStringConstructor(args.filename_template_sftlf, args)
    template_sftlf.month = monthname

    print("TEMPLATE:", template_S())
    files_S = glob.glob(os.path.join(args.modpath, template_S()))
    print(files_S)
    for file_S in files_S:
        print("Reading Amplitude from %s ..." % file_S)
        reverted = template_S.reverse(os.path.basename(file_S))
        model = reverted["model"]
        try:
            template_tS.model = model
            template_sftlf.model = model
            S = cdms2.open(file_S)("S", region)
            print(
                "Reading Phase from %s ..." % os.path.join(args.modpath, template_tS())
            )
            tS = cdms2.open(os.path.join(args.modpath, template_tS()))("tS", region)
            print(
                "Reading sftlf from %s ..."
                % os.path.join(args.modpath, template_sftlf())
            )
            try:
                sftlf_fnm = glob.glob(os.path.join(args.modpath, template_sftlf()))[0]
                sftlf = cdms2.open(sftlf_fnm)("sftlf", region) / 100.0
            except BaseException as err:
                print("Failed reading sftlf from file (error was: %s)" % err)
                print("Creating one for you")
                sftlf = cdutil.generateLandSeaMask(S.getGrid())

            if model not in stats_dic:
                stats_dic[model] = {region_name: spacevavg(S, tS, sftlf, model)}
            else:
                stats_dic[model].update({region_name: spacevavg(S, tS, sftlf, model)})
            print(stats_dic)
        except Exception as err:
            print("Failed for model %s with error %s" % (model, err))

    # Write output to JSON file.
    metrics_dictionary["RESULTS"] = stats_dic
    rgmsk = metrics_dictionary.get("RegionalMasking", {})
    nm = region_name
    region.id = nm
    rgmsk[nm] = {"id": nm, "domain": region}
    metrics_dictionary["RegionalMasking"] = rgmsk
    OUT.write(
        metrics_dictionary,
        json_structure=["model", "domain", "harmonic", "statistic"],
        indent=4,
        separators=(",", ": "),
    )
    if cmec:
        print("Writing cmec file")
        OUT.write_cmec(indent=4, separators=(",", ": "))
    print("done")


if __name__ == "__main__":
    main()
