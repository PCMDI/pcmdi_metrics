import copy

import pcmdi_metrics


def cloud_feedback_metrics_to_json(
    outdir, json_filename, result_dict, model=None, run=None, cmec_flag=False
):
    # Open JSON
    JSON = pcmdi_metrics.io.base.Base(outdir, json_filename)
    # Dict for JSON
    json_dict = copy.deepcopy(result_dict)
    if model is not None or run is not None:
        # Preserve only needed dict branch -- delete rest keys
        models_in_dict = list(json_dict["RESULTS"].keys())
        for m in models_in_dict:
            if m == model:
                runs_in_model_dict = list(json_dict["RESULTS"][m].keys())
                for r in runs_in_model_dict:
                    if r != run and run is not None:
                        del json_dict["RESULTS"][m][r]
            else:
                del json_dict["RESULTS"][m]
    # Write selected dict to JSON
    JSON.write(
        json_dict,
        json_structure=[
            "model",
            "realization",
            "statistic",
        ],
        sort_keys=False,
        indent=4,
        separators=(",", ": "),
    )
    if cmec_flag:
        print("Writing cmec file")
        JSON.write_cmec(indent=4, separators=(",", ": "))
