# - Generate an html file(s) summary of compiled PMP graphics using Bokeh.
# - Author: Kristin Chang (2024.12)
# - Last Update: 2025.04

import json
import os
from datetime import datetime
from glob import glob
from typing import Optional

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    DataTable,
    Div,
    HTMLTemplateFormatter,
    MultiChoice,
    TableColumn,
)

from pcmdi_metrics.enso.lib import json_dict_to_numpy_array_list
from pcmdi_metrics.utils import (
    database_metrics,
    download_files_from_github,
    find_pmp_archive_json_urls,
    load_json_from_url,
)
from pcmdi_metrics.utils.sort_human import sort_human


def view_pmp_output(
    mips: list = ["cmip5", "cmip6"],
    exps: list = ["historical", "amip"],
    metrics: list = ["mean_climate", "variability_modes", "enso_metric"],
):
    """
    Writes out bokeh layout objects as HTML files and creates base gallery style HTML file with links to each summary metric page based on mip, exp, and metrics.

    Parameters
    ----------
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).
    metrics : list
        List of metrics (e.g., ['mean_climate', 'variability_modes', 'enso_metric']).

    Returns
    ----------
    html
        An HTML file containing an image gallery with links to each metric page from the metrics list.
    """
    todays_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    home_content = f"""
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PMP Viewer</title>
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css">
        <link rel="stylesheet" href="./assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
        <div class="banner">
            <div class="viewer">
                <p>
                    (Prototype) <br>
                    <b>MIPs:</b> {", ".join(mips)} <br>
                    <b>EXPs:</b> {", ".join(exps)} <br>
                    <b>Created:</b> {todays_date}
                </p>
                <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo">
                <h1>VIEWER</h1>
            </div>
        </div>
    </head>

    <body>
    """

    # Run each summary function to generate individual pages

    if mips:
        viewer_dict = create_viewer_dict(mips=mips, exps=exps, metrics=metrics)
        if "mean_climate" in metrics:
            mean_clim_dict = viewer_dict["mean_climate"]
            mean_clim_divedown_layout = create_mean_clim_divedown_layout(
                mean_clim_dict, mips, exps, todays_date
            )
            output_file("./mean_climate_divedown.html")
            save(mean_clim_divedown_layout)

            mean_clim_portrait_layout = create_mean_clim_portrait_layout(
                mips, exps, todays_date
            )
            output_file("./mean_climate_portrait.html")
            save(mean_clim_portrait_layout)

            home_content += """
            <div class="container">
                <div class="responsive">
                    <div class="gallery">
                        <a target="_blank" href="./mean_climate_divedown.html">
                            <img src="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_ann_global.png" alt="mean_clim_divedown_test_img" width="auto" height="348">
                        </a>
                        <div class="desc">Mean Climate Dive Down Plots</div>
                    </div>
                </div>

                <div class="responsive">
                    <div class="gallery">
                        <a target="_blank" href="./mean_climate_portrait.html">
                            <img src="./assets/mean_climate_portrait_plot_20250213.png" alt="mean_clim_portrait_test_img" width="400" height="348">
                        </a>
                        <div class="desc">Mean Climate Portrait Plots</div>
                    </div>
                </div>
            </div>
            """
        if "variability_modes" in metrics:
            mov_dict = viewer_dict["variability_modes"]
            variability_modes_layout = create_mov_layout(
                mov_dict, mips, exps, todays_date
            )
            output_file("./variability_modes.html")
            save(variability_modes_layout)

            home_content += """
            <div class="container">
                <div class="responsive">
                    <div class="gallery">
                        <a target="_blank" href="./variability_modes.html">
                            <img src="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/variability_modes/cmip6/historical/v20220825/PDO/HadISSTv1.1/PDO_ts_EOF1_monthly_cmip6_ACCESS-CM2_historical_r1i1p1f1_mo_atm_1900-2005_cbf.png" alt="mov_test_img" width="auto" height="348">
                        </a>
                        <div class="desc">Extratropical Modes of Variability Plots</div>
                    </div>
                </div>
                """

        if "enso_metric" in metrics:
            enso_dict = viewer_dict["enso_metric"]
            enso_layout = create_enso_layout(enso_dict, mips, exps, todays_date)
            output_file("./enso_metric.html")
            save(enso_layout)

            home_content += """
            <div class="responsive">
                <div class="gallery">
                    <a target="_blank" href="./enso_metric.html">
                        <img src="assets/ENSO_ACCESS-CM2_thumbnail.png" alt="enso_test_img" width="auto" height="348">
                    </a>
                    <div class="desc">ENSO Metric Plots</div>
                </div>
            </div>
            """

    # close html tags
    home_content += """
    </div>
    </body>
    </html>
    """
    # save home page as html
    with open("pmp_output_viewer.html", "w") as pov_file:
        pov_file.write(home_content)

    cwd = os.getcwd()
    return print(f"POV created in {cwd}")


# -----------------
# Layer I Functions
# -----------------
def create_mean_clim_divedown_layout(mean_climate_dict, mips, exps, todays_date):
    """
    Creates a bokeh layout object for mean climate dive down plots.

    Parameters
    ----------
    mean_climate_dict : dict
        A dictionary of json URLs for each mip and exp available in the PMP archive for mean climate.
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).
    todays_date : str
        The current date and time the script is run (Format: %Y-%m-%d %H:%M:%S).

    Returns
    ----------
    bokeh layout
        Arranged bokeh grid of the custom PMP Viewer banner, title text, multichoice dropdown filter widgets, and data table.
    """
    df = create_mean_clim_divedown_df(mean_climate_dict, mips)
    source = ColumnDataSource(data=dict(df))
    filtered_data = df.loc[
        (df["Region"] == "global") & (df["Experiment"] == "historical")
    ]
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient="list"))
    image_columns = ["ANN", "DJF", "MAM", "JJA", "SON"]
    dtable = create_bokeh_table(
        df=df,
        filtered_source=filtered_source,
        image_columns=image_columns,
        season_column_names=True,
    )

    filter_columns = ["MIP", "Experiment", "Model", "Variable", "Region"]
    filter_widget_dict = create_bokeh_widgets(df, filter_columns)

    mip_dropdown = filter_widget_dict["dropdown0"]
    exp_dropdown = filter_widget_dict["dropdown1"]
    model_dropdown = filter_widget_dict["dropdown2"]
    var_dropdown = filter_widget_dict["dropdown3"]
    region_dropdown = filter_widget_dict["dropdown4"]

    dropdown_callback = CustomJS(
        args=dict(
            source=source,
            filtered_source=filtered_source,
            mip_dropdown=mip_dropdown,
            exp_dropdown=exp_dropdown,
            model_dropdown=model_dropdown,
            var_dropdown=var_dropdown,
            region_dropdown=region_dropdown,
        ),
        code="""
        const original_data = source.data;
        const filtered_data = { MIP: [], Experiment: [], Model: [], Variable: [], Description: [], Region: [], ANN: [], DJF: [], JJA: [], MAM: [], SON: [] };

        const selected_mips = mip_dropdown.value;
        const selected_exps = exp_dropdown.value;
        const selected_models = model_dropdown.value;
        const selected_vars = var_dropdown.value;
        const selected_regions = region_dropdown.value;

        for (let i = 0; i < original_data.Model.length; i++) {
            const in_mip = selected_mips.length === 0 || selected_mips.includes(original_data.MIP[i]);
            const in_exp = selected_exps.length === 0 || selected_exps.includes(original_data.Experiment[i]);
            const in_model = selected_models.length === 0 || selected_models.includes(original_data.Model[i]);
            const in_var = selected_vars.length === 0 || selected_vars.includes(original_data.Variable[i]);
            const in_region = selected_regions.length === 0 || selected_regions.includes(original_data.Region[i]);

            if (in_mip && in_exp && in_model && in_var && in_region) {
                filtered_data.MIP.push(original_data.MIP[i]);
                filtered_data.Experiment.push(original_data.Experiment[i]);
                filtered_data.Model.push(original_data.Model[i]);
                filtered_data.Variable.push(original_data.Variable[i]);
                filtered_data.Description.push(original_data.Description[i]);
                filtered_data.Region.push(original_data.Region[i]);
                filtered_data.ANN.push(original_data.ANN[i]);
                filtered_data.DJF.push(original_data.DJF[i]);
                filtered_data.JJA.push(original_data.JJA[i]);
                filtered_data.MAM.push(original_data.MAM[i]);
                filtered_data.SON.push(original_data.SON[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """,
    )

    banner = Div(
        text=f"""
        <title>Mean Climate Dive Down</title>
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css">
        <link rel="stylesheet" href="./assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
        <div class="banner">
            <div class="viewer">
                <p>
                    (Prototype) <br>
                    <b>MIPs:</b> {", ".join(mips)} <br>
                    <b>EXPs:</b> {", ".join(exps)} <br>
                    <b>Created:</b> {todays_date}
                </p>
                <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo">
                <h1>VIEWER</h1>
            </div>
        </div>
        """
    )

    title_text = Div(
        text="""
        <link rel='stylesheet' type='text/css' href='./assets/style.css'>
        <h1 style="padding-left: 20px;">PMP Mean Climate Dive Down Plots</h1>
        <p style="padding-left: 20px;">This webpage is optimized for browsers with over 1200 pixel width screen resolution.</p>
        <br>
        <h2 style="padding-left: 20px;">Filters</h2>
        """
    )

    mip_dropdown.js_on_change("value", dropdown_callback)
    exp_dropdown.js_on_change("value", dropdown_callback)
    model_dropdown.js_on_change("value", dropdown_callback)
    var_dropdown.js_on_change("value", dropdown_callback)
    region_dropdown.js_on_change("value", dropdown_callback)

    layout = column(
        row(banner),
        title_text,
        row(mip_dropdown, exp_dropdown, model_dropdown, var_dropdown, region_dropdown),
        dtable,
    )

    return layout


def create_mean_clim_portrait_layout(mips, exps, todays_date):
    """
    Creates a bokeh layout object for mean climate portrait plots.

    Parameters
    ----------
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).
    todays_date : str
        The current date and time the script is run (Format: %Y-%m-%d %H:%M:%S).

    Returns
    ----------
    bokeh layout
        Arranged bokeh grid of the custom PMP Viewer banner, title text, multichoice dropdown filter widgets, and data table.
    """
    df = create_mean_clim_portrait_df(mips, exps)
    source = ColumnDataSource(data=dict(df))
    filtered_data = df.loc[df["Experiment"] == "historical"]
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient="list"))
    image_columns = ["Plot"]
    dtable = create_bokeh_table(
        df=df, filtered_source=filtered_source, image_columns=image_columns
    )

    filter_columns = ["MIP", "Experiment", "Metric"]
    filter_widget_dict = create_bokeh_widgets(df, filter_columns)

    mip_dropdown = filter_widget_dict["dropdown0"]
    exp_dropdown = filter_widget_dict["dropdown1"]
    metric_dropdown = filter_widget_dict["dropdown2"]

    dropdown_callback = CustomJS(
        args=dict(
            source=source,
            filtered_source=filtered_source,
            mip_dropdown=mip_dropdown,
            exp_dropdown=exp_dropdown,
            metric_dropdown=metric_dropdown,
        ),
        code="""
        const original_data = source.data;
        const filtered_data = { MIP: [], Experiment: [], Metric: [], Plot: [], };

        const selected_mips = mip_dropdown.value;
        const selected_exps = exp_dropdown.value;
        const selected_metrics = metric_dropdown.value;

        for (let i = 0; i < original_data.MIP.length; i++) {
            const in_mip = selected_mips.length === 0 || selected_mips.includes(original_data.MIP[i]);
            const in_exp = selected_exps.length === 0 || selected_exps.includes(original_data.Experiment[i]);
            const in_metric = selected_metrics.length === 0 || selected_metrics.includes(original_data.Metric[i]);

            if (in_mip && in_exp && in_metric) {
                filtered_data.MIP.push(original_data.MIP[i]);
                filtered_data.Experiment.push(original_data.Experiment[i]);
                filtered_data.Metric.push(original_data.Metric[i]);
                filtered_data.Plot.push(original_data.Plot[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """,
    )

    banner = Div(
        text=f"""
        <title>Mean Climate Portrait Plot</title>
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css">
        <link rel="stylesheet" href="./assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
        <div class="banner">
            <div class="viewer">
                <p>
                    (Prototype) <br>
                    <b>MIPs:</b> {", ".join(mips)} <br>
                    <b>EXPs:</b> {", ".join(exps)} <br>
                    <b>Created:</b> {todays_date}
                </p>
                <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo">
                <h1>VIEWER</h1>
            </div>
        </div>
        """
    )

    title_text = Div(
        text="""
        <link rel='stylesheet' type='text/css' href='./assets/style.css'>
        <h1 style="padding-left: 20px;">PMP Mean Climate Portrait Plots</h1>
        <p style="padding-left: 20px;">This webpage is optimized for browsers with over 1200 pixel width screen resolution.</p>
        <br>
        <h2 style="padding-left: 20px;">Filters</h2>
        """
    )

    mip_dropdown.js_on_change("value", dropdown_callback)
    exp_dropdown.js_on_change("value", dropdown_callback)
    metric_dropdown.js_on_change("value", dropdown_callback)

    layout = column(
        row(banner),
        title_text,
        row(mip_dropdown, exp_dropdown, metric_dropdown),
        dtable,
    )
    return layout


def create_mov_layout(mov_dict, mips, exps, todays_date):
    """
    Creates a bokeh layout object for modes of variability dive down pages.

    Parameters
    ----------
    mov_dict : dict
        A dictionary of json URLs for each mip and exp available in the PMP archive for modes of variability.
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).
    todays_date : str
        The current date and time the script is run (Format: %Y-%m-%d %H:%M:%S).

    Returns
    ----------
    bokeh layout
        Arranged bokeh grid of the custom PMP Viewer banner, title text, multichoice dropdown filter widgets, and data table.
    """
    df = create_mov_df(mov_dict, mips)
    source = ColumnDataSource(data=dict(df))
    filtered_data = df
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient="list"))
    image_columns = ["Plot"]
    dtable = create_bokeh_table(
        df=df, filtered_source=filtered_source, image_columns=image_columns
    )

    filter_columns = ["MIP", "Model", "Mode", "Season", "Method"]
    filter_widget_dict = create_bokeh_widgets(df, filter_columns)

    mip_dropdown = filter_widget_dict["dropdown0"]
    model_dropdown = filter_widget_dict["dropdown1"]
    mode_dropdown = filter_widget_dict["dropdown2"]
    season_dropdown = filter_widget_dict["dropdown3"]
    method_dropdown = filter_widget_dict["dropdown4"]

    dropdown_callback = CustomJS(
        args=dict(
            source=source,
            filtered_source=filtered_source,
            mip_dropdown=mip_dropdown,
            model_dropdown=model_dropdown,
            mode_dropdown=mode_dropdown,
            season_dropdown=season_dropdown,
            method_dropdown=method_dropdown,
        ),
        code="""
        const original_data = source.data;
        const filtered_data = { MIP: [], Model: [], Mode: [], Season: [], Method: [], Variable: [], Reference: [], Plot: [], };

        const selected_mips = mip_dropdown.value;
        const selected_models = model_dropdown.value;
        const selected_modes = mode_dropdown.value;
        const selected_seasons = season_dropdown.value;
        const selected_methods = method_dropdown.value;

        for (let i = 0; i < original_data.MIP.length; i++) {
            const in_mip = selected_mips.length === 0 || selected_mips.includes(original_data.MIP[i]);
            const in_model = selected_models.length === 0 || selected_models.includes(original_data.Model[i]);
            const in_mode = selected_modes.length === 0 || selected_modes.includes(original_data.Mode[i]);
            const in_season = selected_seasons.length === 0 || selected_seasons.includes(original_data.Season[i]);
            const in_method = selected_methods.length === 0 || selected_methods.includes(original_data.Method[i]);

            if (in_mip && in_model && in_mode && in_season && in_method) {
                filtered_data.MIP.push(original_data.MIP[i]);
                filtered_data.Model.push(original_data.Model[i]);
                filtered_data.Mode.push(original_data.Mode[i]);
                filtered_data.Season.push(original_data.Season[i]);
                filtered_data.Method.push(original_data.Method[i]);
                filtered_data.Variable.push(original_data.Variable[i]);
                filtered_data.Reference.push(original_data.Reference[i]);
                filtered_data.Plot.push(original_data.Plot[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """,
    )

    banner = Div(
        text=f"""
        <title>Variability Modes</title>
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css">
        <link rel="stylesheet" href="./assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
        <div class="banner">
            <div class="viewer">
                <p>
                    (Prototype) <br>
                    <b>MIPs:</b> {", ".join(mips)} <br>
                    <b>EXPs:</b> {", ".join(exps)} <br>
                    <b>Created:</b> {todays_date}
                </p>
                <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo">
                <h1>VIEWER</h1>
            </div>
        </div>
        """
    )

    title_text = Div(
        text="""
        <link rel='stylesheet' type='text/css' href='./assets/style.css'>
        <h1 style="padding-left: 20px;">PMP Extratropical Modes of Variability Plots</h1>
        <p style="padding-left: 20px;">This webpage is optimized for browsers with over 1200 pixel width screen resolution.</p>
        <br>
        <h2 style="padding-left: 20px;">Filters</h2>
        """
    )

    mip_dropdown.js_on_change("value", dropdown_callback)
    model_dropdown.js_on_change("value", dropdown_callback)
    mode_dropdown.js_on_change("value", dropdown_callback)
    season_dropdown.js_on_change("value", dropdown_callback)
    method_dropdown.js_on_change("value", dropdown_callback)

    layout = column(
        row(banner),
        title_text,
        row(
            mip_dropdown,
            model_dropdown,
            mode_dropdown,
            season_dropdown,
            method_dropdown,
        ),
        dtable,
    )
    return layout


def create_enso_layout(enso_dict, mips, exps, todays_date):
    """
    Creates a bokeh layout object for ENSO dive down pages.

    Parameters
    ----------
    enso_dict : dict
        A dictionary of json URLs for each mip and exp available in the PMP archive for ENSO.
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).
    todays_date : str
        The current date and time the script is run (Format: %Y-%m-%d %H:%M:%S).

    Returns
    ----------
    bokeh layout
        Arranged bokeh grid of the custom PMP Viewer banner, title text, multichoice dropdown filter widgets, and data table.
    """
    df = create_enso_df(enso_dict, mips)
    source = ColumnDataSource(data=dict(df))
    filtered_data = df
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient="list"))
    image_columns = ["Plot"]

    dtable = create_bokeh_table(
        df=df, filtered_source=filtered_source, image_columns=image_columns
    )

    filter_columns = ["MIP", "Model", "Collection", "Metric"]
    filter_widget_dict = create_bokeh_widgets(df, filter_columns)

    mip_dropdown = filter_widget_dict["dropdown0"]
    model_dropdown = filter_widget_dict["dropdown1"]
    collection_dropdown = filter_widget_dict["dropdown2"]
    metric_dropdown = filter_widget_dict["dropdown3"]

    dropdown_callback = CustomJS(
        args=dict(
            source=source,
            filtered_source=filtered_source,
            mip_dropdown=mip_dropdown,
            model_dropdown=model_dropdown,
            collection_dropdown=collection_dropdown,
            metric_dropdown=metric_dropdown,
        ),
        code="""
        const original_data = source.data;
        const filtered_data = { MIP: [], Model: [], Collection: [], Metric: [], Value: [], Plot: [], };

        const selected_mips = mip_dropdown.value;
        const selected_models = model_dropdown.value;
        const selected_collections = collection_dropdown.value;
        const selected_metrics = metric_dropdown.value;

        for (let i = 0; i < original_data.MIP.length; i++) {
            const in_mip = selected_mips.length === 0 || selected_mips.includes(original_data.MIP[i]);
            const in_model = selected_models.length === 0 || selected_models.includes(original_data.Model[i]);
            const in_collection = selected_collections.length === 0 || selected_collections.includes(original_data.Collection[i]);
            const in_metric = selected_metrics.length === 0 || selected_metrics.includes(original_data.Metric[i]);

            if (in_mip && in_model && in_collection && in_metric) {
                filtered_data.MIP.push(original_data.MIP[i]);
                filtered_data.Model.push(original_data.Model[i]);
                filtered_data.Collection.push(original_data.Collection[i]);
                filtered_data.Metric.push(original_data.Metric[i]);
                filtered_data.Value.push(original_data.Value[i]);
                filtered_data.Plot.push(original_data.Plot[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """,
    )

    banner = Div(
        text=f"""
        <title>ENSO</title>
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css">
        <link rel="stylesheet" href="./assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
        <div class="banner">
            <div class="viewer">
                <p>
                    (Prototype) <br>
                    <b>MIPs:</b> {", ".join(mips)} <br>
                    <b>EXPs:</b> {", ".join(exps)} <br>
                    <b>Created:</b> {todays_date}
                </p>
                <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo">
                <h1>VIEWER</h1>
            </div>
        </div>
        """
    )

    title_text = Div(
        text="""
        <link rel='stylesheet' type='text/css' href='./assets/style.css'>
        <h1 style="padding-left: 20px;">El Niño-Southern Oscillation (ENSO) Plots</h1>
        <p style="padding-left: 20px;">This webpage is optimized for browsers with over 1200 pixel width screen resolution.</p>
        <br>
        <h2 style="padding-left: 20px;">Filters</h2>
        """
    )

    mip_dropdown.js_on_change("value", dropdown_callback)
    model_dropdown.js_on_change("value", dropdown_callback)
    collection_dropdown.js_on_change("value", dropdown_callback)
    metric_dropdown.js_on_change("value", dropdown_callback)

    layout = column(
        row(banner),
        title_text,
        row(mip_dropdown, model_dropdown, collection_dropdown, metric_dropdown),
        dtable,
    )
    return layout


# ------------------
# Layer II Functions
# ------------------
def create_bokeh_table(
    df,
    filtered_source,
    image_columns,
    width: Optional[float] = 1600,
    height: Optional[float] = 1200,
    row_height: Optional[float] = 35,
    season_column_names: bool = False,
    display_images: bool = False,
):
    """
    Creates a bokeh data table for the provided dataframe and formats Plot columns.

    Parameters
    ----------
    df : Pandas dataframe
        A dataframe with the columns and values to display in the data table.
    filtered_source : ColumnDataSource
        A bokeh ColumnDataSource object with any default filters applied (e.g., Region = 'global').
    image_columns : list
        A list of column(s) that contain links to images/plot pages.
    width : float
        Desired width of data table.
    height : float
        Desired height of table.
    row_height : float
        Desired height of each row in the table.
    season_column_names : bool=False
        If true, image columns will be formatted for seasons (e.g., values read "DJF", "MAM", etc. instead of "View Plot").
    display_images : bool=False
        If true, image column will be formatted to display a thumbnail of the image instead of text.

    Returns
    ----------
    bokeh data table
        A bokeh data table object that can be displayed in a grid layout.
    """
    image_templates = {}
    image_formatters = {}

    if season_column_names:
        for s in image_columns:
            image_templates[
                f"{s}_template"
            ] = f"""
            <div style="position: relative; font-size:16px;">
                <a href="<%= {s} %>" target="_blank">{s}</a>
            </div>
            """
            image_formatters[f"{s}_formatter"] = HTMLTemplateFormatter(
                template=image_templates[f"{s}_template"]
            )
    elif display_images:
        for s in image_columns:
            image_templates[
                f"{s}_template"
            ] = """
            <div style="position: relative;">
                <a href="<%= value %>" target="_blank"><img src="<%= value %>" alt="image_preview" height=300></a>
            </div>
            """
            image_formatters[f"{s}_formatter"] = HTMLTemplateFormatter(
                template=image_templates[f"{s}_template"]
            )
    else:
        for col in image_columns:
            image_templates[
                f"{col}_template"
            ] = """
            <div style="position: relative; font-size:16px;">
                <a href="<%= value %>" target="_blank">View Plot</a>
            </div>
            """
            image_formatters[f"{col}_formatter"] = HTMLTemplateFormatter(
                template=image_templates[f"{col}_template"]
            )

    text_only_formatter = HTMLTemplateFormatter(
        template='<span style="font-size:16px;"> <%= value %> </span>'
    )

    column_names = df.columns.values
    bokeh_columns = []
    for col in column_names:
        if col in image_columns:
            column = TableColumn(
                field=col, title=col, formatter=image_formatters[f"{col}_formatter"]
            )
            bokeh_columns.append(column)
        else:
            column = TableColumn(field=col, title=col, formatter=text_only_formatter)
            bokeh_columns.append(column)

    dtable = DataTable(
        source=filtered_source,
        columns=bokeh_columns,
        width=width,
        height=height,
        row_height=row_height,
        index_position=None,
        # css_classes=["custom-table"]
        stylesheets=[
            """
            :host {
                padding: 20px;
            }

            :host .slick-header-columns.slick-header-columns-left {
                background-color: #0066b3;
                color: white;
                font-size: 16px;
            }

            :host .slick-header-column:hover {
                background-color: #daeffe;
                color: #0066b3;
                font-size: 16px;
            }

            :host .ui-widget-content.slick-row.even {
                text-align: left;
                padding-top: 6px;
            }

            :host .ui-widget-content.slick-row.odd {
                text-align: left;
                padding-top: 6px;
            }

            """
        ],
    )

    return dtable


def create_bokeh_widgets(df, filter_columns):
    """
    Creates bokeh MultiChoice widgets with dropdown lists for the specified data.

    Parameters
    ----------
    df : Pandas dataframe
        A dataframe with the columns and values to display in the data table.
    filter_columns : list
        A list of the columns to create MultiChoice filters for.

    Returns
    ----------
    dict
        A dictionary of a dictionary of bokeh MultiChoice widgets for a bokeh grid layout.
    """
    filter_widget_dict = {}

    for fc, filter_column_name in enumerate(filter_columns):
        if filter_column_name == "Region":
            filter_widget_dict["dropdown" + str(fc)] = MultiChoice(
                options=sorted(list(df[filter_column_name].unique())),
                title="Select " + filter_column_name,
                value=["global"],
                height=90,
                width=300,
                sizing_mode="fixed",
            )
        elif filter_column_name == "Experiment":
            filter_widget_dict["dropdown" + str(fc)] = MultiChoice(
                options=sorted(list(df[filter_column_name].unique())),
                title="Select " + filter_column_name,
                value=["historical"],
                height=90,
                width=300,
                sizing_mode="fixed",
            )
        elif filter_column_name == "MIP":
            filter_widget_dict["dropdown" + str(fc)] = MultiChoice(
                options=sorted(list(df[filter_column_name].unique())),
                title="Select " + filter_column_name,
                value=[],
                height=90,
                width=300,
                sizing_mode="fixed",
                stylesheets=[
                    """
                    :host .bk-input-group{
                        padding-left: 20px;}
                    """
                ],
            )
        else:
            filter_widget_dict["dropdown" + str(fc)] = MultiChoice(
                options=sorted(list(df[filter_column_name].dropna().unique())),
                title="Select " + filter_column_name,
                value=[],
                height=90,
                width=300,
                sizing_mode="fixed",
            )

    return filter_widget_dict


def create_mean_clim_divedown_df(mean_clim_dict, mips):
    """
    Creates a pandas dataframe with links to each season mean climate dive down image from the PMP Database Archive.

    Parameters
    ----------
    mean_clim_dict : dict
         A dictionary of json URLs for each mip and exp available in the PMP archive for mean climate.
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).

    Returns
    ----------
    Pandas dataframe
        A dataframe of mean climate dive down info and plot links to be converted to a bokeh data table.
    """
    (
        exps,
        cmip6_models,
        cmip5_models,
        all_models,
        all_vars,
        regions,
        seasons,
    ) = retrieve_lists(mean_clim_dict, "mean_climate", mips)

    multi_index = pd.MultiIndex.from_product(
        [mips, exps, all_models, all_vars, regions],
        names=["MIP", "Experiment", "Model", "Variable", "Region"],
    )
    df = pd.DataFrame(index=multi_index).reset_index()
    df = add_var_long_name(df)
    df = df[["MIP", "Experiment", "Model", "Variable", "Description", "Region"]]

    cmip5_df = df.loc[(df["Model"].isin(cmip5_models)) & (df["MIP"] == "cmip5")]
    cmip6_df = df.loc[(df["Model"].isin(cmip6_models)) & (df["MIP"] == "cmip6")]

    df = pd.concat([cmip5_df, cmip6_df])
    df.reset_index(drop=True, inplace=True)

    img_url_head = (
        "https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate"
    )

    seasons = ["ANN", "DJF", "MAM", "JJA", "SON"]
    for s in seasons:
        df[s.upper()] = df.apply(
            lambda row: (
                f"{img_url_head}/{row['MIP']}/{row['Experiment']}/clim/v20210811/{row['Variable']}/{row['Region']}/{row['Variable']}_{row['MIP']}_{row['Experiment']}_{row['Model']}_{s.lower()}_global.png"
                if row["MIP"] == "cmip6"
                else f"{img_url_head}/{row['MIP']}/{row['Experiment']}/clim/v20200505/{row['Variable']}/{row['Variable']}_{row['MIP']}_{row['Experiment']}_{row['Model']}_{s.lower()}.png"
                if row["MIP"] == "cmip5"
                else None
            ),
            axis=1,
        )

    return df


def create_mean_clim_portrait_df(mips, exps):
    """
    Creates a pandas dataframe with links to interactive mean climate portrait plots on the PCMDI website.

    Parameters
    ----------
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).

    Returns
    ----------
    Pandas dataframe
        A dataframe of mean climate portrait plot info and links to be converted to a bokeh data table.
    """
    metrics = ["rms_xy", "rmsc_xy", "bias_xy", "mae_xy", "cor_xy"]

    multi_index = pd.MultiIndex.from_product(
        [mips, exps, metrics], names=["MIP", "Experiment", "Metric"]
    )
    df = pd.DataFrame(index=multi_index).reset_index()
    df = df[["MIP", "Experiment", "Metric"]]

    url_head = "https://pcmdi.llnl.gov/pmp-preliminary-results/interactive_plot/portrait_plot/mean_clim/cmip6/historical/v20240430"
    df["Plot"] = df.apply(
        lambda row: f"{url_head}/mean_clim_portrait_plot_4seasons_{row['MIP']}_{row['Experiment']}_{row['Metric']}_v20240430.html",
        axis=1,
    )

    return df


def create_mov_df(mov_dict, mips):
    """
    Creates a pandas dataframe with links to Modes of Variability dynamically generated dive down pages on the PCMDI website.

    Parameters
    ----------
    mov_dict : dict
         A dictionary of json URLs for each mip and exp available in the PMP archive for Modes of Variability.
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).

    Returns
    ----------
    Pandas dataframe
        A dataframe of Modes of Variability dive down info and links to be converted to a bokeh data table.
    """
    (
        exps,
        cmip6_models,
        cmip5_models,
        all_models,
        modes,
        regions,
        all_seasons,
    ) = retrieve_lists(mov_dict, "variability_modes", mips=mips)
    seasons = []
    for season in all_seasons:
        if season != "ANN":
            seasons.append(season)

    all_modes = []
    for mode in modes:
        all_modes.append(mode.split("/")[0])

    # metrics = ['rmse', 'rmsc', 'amplitude']
    methods = ["cbf", "eof"]

    results_dict = {}
    for mip in mips:
        results_dict[mip] = {}
        results_dict[mip] = database_metrics(
            mip=mip,
            model=None,
            exp="historical",
            metrics=["variability_modes"],
            model_member_list_only=True,
        )

    multi_index = pd.MultiIndex.from_product(
        [mips, all_models, all_modes, seasons, methods],
        names=["MIP", "Model", "Mode", "Season", "Method"],
    )
    df = pd.DataFrame(index=multi_index).reset_index()
    df = df[["MIP", "Model", "Mode", "Season", "Method"]]

    ts_modes = ["AMO", "NPGO", "PDO"]
    monthly_modes = ["NPGO", "PDO"]
    yearly_modes = ["AMO"]
    df.loc[df["Mode"].isin(monthly_modes), "Season"] = "monthly"
    df.loc[df["Mode"].isin(yearly_modes), "Season"] = "yearly"
    df = df.drop_duplicates()

    df.loc[df["Mode"].isin(ts_modes), "Variable"] = "ts"
    df.loc[~df["Mode"].isin(ts_modes), "Variable"] = "psl"
    df.loc[df["Mode"].isin(ts_modes), "Reference"] = "HadISSTv1.1"
    df.loc[~df["Mode"].isin(ts_modes), "Reference"] = "NOAA-CIRES_20CR"

    df.reset_index(drop=True, inplace=True)

    cmip5_df = df.loc[(df["Model"].isin(cmip5_models)) & (df["MIP"] == "cmip5")]
    cmip6_df = df.loc[(df["Model"].isin(cmip6_models)) & (df["MIP"] == "cmip6")]

    df = pd.concat([cmip5_df, cmip6_df])
    df.reset_index(drop=True, inplace=True)

    url_head = "https://pcmdi.llnl.gov/pmp-preliminary-results/interactive_plot/variability_modes/portrait_plot/dive_down.html?"

    df["Runs"] = df.apply(
        lambda row: (
            ", ".join(
                list(
                    results_dict[row["MIP"]]["variability_modes"][
                        "var_mode_NAM_EOF1_stat_cmip6_historical_mo_atm_allModels_allRuns_1900-2005"
                    ]["RESULTS"][row["Model"]].keys()
                )
            )
            if row["MIP"] == "cmip6"
            and results_dict[row["MIP"]]["variability_modes"][
                "var_mode_NAM_EOF1_stat_cmip6_historical_mo_atm_allModels_allRuns_1900-2005"
            ]["RESULTS"][row["Model"]]
            is not None
            else ", ".join(
                list(
                    results_dict[row["MIP"]]["variability_modes"][
                        "var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_allModels_allRuns_1900-2005"
                    ]["RESULTS"][row["Model"]].keys()
                )
            )
            if row["MIP"] == "cmip5"
            and results_dict[row["MIP"]]["variability_modes"][
                "var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_allModels_allRuns_1900-2005"
            ]["RESULTS"][row["Model"]]
            is not None
            else None
        ),
        axis=1,
    )

    df["Periods"] = df.apply(
        lambda row: (
            ", ".join(
                list(
                    ["1900-2005"]
                    * len(
                        results_dict[row["MIP"]]["variability_modes"][
                            "var_mode_NAM_EOF1_stat_cmip6_historical_mo_atm_allModels_allRuns_1900-2005"
                        ]["RESULTS"][row["Model"]].keys()
                    )
                )
            )
            if row["MIP"] == "cmip6"
            and results_dict[row["MIP"]]["variability_modes"][
                "var_mode_NAM_EOF1_stat_cmip6_historical_mo_atm_allModels_allRuns_1900-2005"
            ]["RESULTS"][row["Model"]]
            is not None
            else ", ".join(
                list(
                    ["1900-2005"]
                    * len(
                        results_dict[row["MIP"]]["variability_modes"][
                            "var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_allModels_allRuns_1900-2005"
                        ]["RESULTS"][row["Model"]].keys()
                    )
                )
            )
            if row["MIP"] == "cmip5"
            and results_dict[row["MIP"]]["variability_modes"][
                "var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_allModels_allRuns_1900-2005"
            ]["RESULTS"][row["Model"]]
            is not None
            else None
        ),
        axis=1,
    )

    df["Plot"] = df.apply(
        lambda row: (
            f"{url_head}mip={row['MIP']}&exp=historical&ver=v20220825&mode={row['Mode']}&ref={row['Reference']}&var={row['Variable']}&method={row['Method']}&season={row['Season']}&model={row['Model']}&runs={row['Runs']}&periods={row['Periods']}"
            if row["MIP"] == "cmip6"
            else f"{url_head}mip={row['MIP']}&exp=historical&ver=v20200116&mode={row['Mode']}&ref={row['Reference']}&var={row['Variable']}&method={row['Method']}&season={row['Season']}&model={row['Model']}&runs={row['Runs']}&periods={row['Periods']}"
            if row["MIP"] == "cmip5"
            else None
        ),
        axis=1,
    )

    df = df[
        ["MIP", "Model", "Mode", "Season", "Method", "Variable", "Reference", "Plot"]
    ]

    return df


def create_enso_df(enso_dict, mips):
    """
    Creates a pandas dataframe with links to ENSO dynamically generated dive down pages on the PCMDI website.

    Parameters
    ----------
    mov_dict : dict
         A dictionary of json URLs for each mip and exp available in the PMP archive for ENSO.
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).

    Returns
    ----------
    Pandas dataframe
        A dataframe of ENSO dive down info and links to be converted to a bokeh data table.
    """
    (
        exps,
        cmip6_models,
        cmip5_models,
        all_models,
        collections,
        regions,
        seasons,
    ) = retrieve_lists(enso_dict, "enso_metric", mips=mips)

    results_dict = {}
    for mip in mips:
        results_dict[mip] = {}
        results_dict[mip] = database_metrics(
            mip=mip, model=None, exp="historical", metrics=["enso_metric"]
        )

    cmip5_perf_models = list(
        results_dict["cmip5"]["enso_metric"]["ENSO_perf"]["RESULTS"]["model"].keys()
    )
    cmip6_perf_models = list(
        results_dict["cmip6"]["enso_metric"]["ENSO_perf"]["RESULTS"]["model"].keys()
    )

    cmip5_tel_models = list(
        results_dict["cmip5"]["enso_metric"]["ENSO_tel"]["RESULTS"]["model"].keys()
    )
    cmip6_tel_models = list(
        results_dict["cmip6"]["enso_metric"]["ENSO_tel"]["RESULTS"]["model"].keys()
    )

    cmip5_proc_models = list(
        results_dict["cmip5"]["enso_metric"]["ENSO_proc"]["RESULTS"]["model"].keys()
    )
    cmip6_proc_models = list(
        results_dict["cmip6"]["enso_metric"]["ENSO_proc"]["RESULTS"]["model"].keys()
    )

    perf_cmip5_vars = list(
        results_dict["cmip5"]["enso_metric"]["ENSO_perf"]["RESULTS"]["model"][
            "ACCESS1-0"
        ]["r1i1p1"]["value"].keys()
    )
    tel_cmip5_vars = list(
        results_dict["cmip5"]["enso_metric"]["ENSO_tel"]["RESULTS"]["model"][
            "ACCESS1-0"
        ]["r1i1p1"]["value"].keys()
    )
    proc_cmip5_vars = list(
        results_dict["cmip5"]["enso_metric"]["ENSO_proc"]["RESULTS"]["model"][
            "ACCESS1-0"
        ]["r1i1p1"]["value"].keys()
    )

    perf_cmip6_vars = list(
        results_dict["cmip6"]["enso_metric"]["ENSO_perf"]["RESULTS"]["model"][
            "ACCESS-CM2"
        ]["r1i1p1f1"]["value"].keys()
    )
    tel_cmip6_vars = list(
        results_dict["cmip6"]["enso_metric"]["ENSO_tel"]["RESULTS"]["model"][
            "ACCESS-CM2"
        ]["r1i1p1f1"]["value"].keys()
    )
    proc_cmip6_vars = list(
        results_dict["cmip6"]["enso_metric"]["ENSO_proc"]["RESULTS"]["model"][
            "ACCESS-CM2"
        ]["r1i1p1f1"]["value"].keys()
    )

    cmip5_perf_index = pd.MultiIndex.from_product(
        [["cmip5"], cmip5_perf_models, ["ENSO_perf"], perf_cmip5_vars],
        names=["MIP", "Model", "Collection", "metric_code"],
    )
    cmip5_perf_df = pd.DataFrame(index=cmip5_perf_index).reset_index()
    cmip5_tel_index = pd.MultiIndex.from_product(
        [["cmip5"], cmip5_tel_models, ["ENSO_tel"], tel_cmip5_vars],
        names=["MIP", "Model", "Collection", "metric_code"],
    )
    cmip5_tel_df = pd.DataFrame(index=cmip5_tel_index).reset_index()
    cmip5_proc_index = pd.MultiIndex.from_product(
        [["cmip5"], cmip5_proc_models, ["ENSO_proc"], proc_cmip5_vars],
        names=["MIP", "Model", "Collection", "metric_code"],
    )
    cmip5_proc_df = pd.DataFrame(index=cmip5_proc_index).reset_index()

    cmip6_perf_index = pd.MultiIndex.from_product(
        [["cmip6"], cmip6_perf_models, ["ENSO_perf"], perf_cmip6_vars],
        names=["MIP", "Model", "Collection", "metric_code"],
    )
    cmip6_perf_df = pd.DataFrame(index=cmip6_perf_index).reset_index()
    cmip6_tel_index = pd.MultiIndex.from_product(
        [["cmip6"], cmip6_tel_models, ["ENSO_tel"], tel_cmip6_vars],
        names=["MIP", "Model", "Collection", "metric_code"],
    )
    cmip6_tel_df = pd.DataFrame(index=cmip6_tel_index).reset_index()
    cmip6_proc_index = pd.MultiIndex.from_product(
        [["cmip6"], cmip6_proc_models, ["ENSO_proc"], proc_cmip6_vars],
        names=["MIP", "Model", "Collection", "metric_code"],
    )
    cmip6_proc_df = pd.DataFrame(index=cmip6_proc_index).reset_index()

    df = pd.concat(
        [
            cmip5_perf_df,
            cmip5_tel_df,
            cmip5_proc_df,
            cmip6_perf_df,
            cmip6_tel_df,
            cmip6_proc_df,
        ]
    )
    df.reset_index(drop=True, inplace=True)

    met_names = {
        "BiasPrLatRmse": "double_ITCZ_bias",
        "BiasPrLonRmse": "eq_PR_bias",
        "BiasSstLonRmse": "eq_SST_bias",
        "BiasTauxLonRmse": "eq_Taux_bias",
        "SeasonalPrLatRmse": "double_ITCZ_sea_cycle",
        "SeasonalPrLonRmse": "eq_PR_sea_cycle",
        "SeasonalSstLonRmse": "eq_SST_sea_cycle",
        "SeasonalTauxLonRmse": "eq_Taux_sea_cycle",
        "EnsoSstLonRmse": "ENSO_pattern",
        "EnsoSstTsRmse": "ENSO_lifecycle",
        "EnsoAmpl": "ENSO_amplitude",
        "EnsoSeasonality": "ENSO_seasonality",
        "EnsoSstSkew": "ENSO_asymmetry",
        "EnsoDuration": "ENSO_duration",
        "EnsoSstDiversity": "ENSO_diversity",
        "EnsoSstDiversity_1": "ENSO_diversity",
        "EnsoSstDiversity_2": "ENSO_diversity",
        "EnsoPrMapDjfRmse": "DJF_PR_teleconnection",
        "EnsoPrMapJjaRmse": "JJA_PR_teleconnection",
        "EnsoSstMapDjfRmse": "DJF_TS_teleconnection",
        "EnsoSstMapJjaRmse": "JJA_TS_teleconnection",
        "EnsoFbSstTaux": "SST-Taux_feedback",
        "EnsoFbTauxSsh": "Taux-SSH_feedback",
        "EnsoFbSshSst": "SSH-SST_feedback",
        "EnsoFbSstThf": "SST-NHF_feedback",
        "EnsodSstOce": "ocean_driven_SST",
        "EnsodSstOce_1": "ocean_driven_SST",
        "EnsodSstOce_2": "ocean_driven_SST",
    }

    df["Metric"] = df["metric_code"].map(met_names)
    df_mapped = df[~df["Metric"].isna()]

    ref_info_dict = find_enso_ref()

    df_mapped["Reference"] = df_mapped.apply(
        lambda row: (
            ref_info_dict[row["Collection"]][row["MIP"].upper()][row["metric_code"]]
            if row["metric_code"]
            in (ref_info_dict[row["Collection"]][row["MIP"].upper()].keys())
            else "Tropflux_GPCPv2.3"  # NEED TO CONFIRM THIS IS THE ONLY CASE WITH ISSUES (E.G., EnsoPrMapDjfCorr doesn't have a mapping ref in the info dict)
        ),
        axis=1,
    )

    df_mapped["first_run"] = df_mapped.apply(
        lambda row: (
            sort_human(
                list(
                    results_dict[row["MIP"]]["enso_metric"][row["Collection"]][
                        "RESULTS"
                    ]["model"][row["Model"]].keys()
                )
            )[0]
        ),
        axis=1,
    )

    df_mapped["Value"] = df_mapped.apply(
        lambda row: (
            round(
                float(
                    results_dict[row["MIP"]]["enso_metric"][row["Collection"]][
                        "RESULTS"
                    ]["model"][row["Model"]][row["first_run"]]["value"][
                        row["metric_code"]
                    ][
                        "metric"
                    ][
                        row["Reference"]
                    ][
                        "value"
                    ]
                ),
                3,
            )
            if row["metric_code"]
            in (
                results_dict[row["MIP"]]["enso_metric"][row["Collection"]]["RESULTS"][
                    "model"
                ][row["Model"]][row["first_run"]]["value"].keys()
            )
            and results_dict[row["MIP"]]["enso_metric"][row["Collection"]]["RESULTS"][
                "model"
            ][row["Model"]][row["first_run"]]["value"][row["metric_code"]]["metric"][
                row["Reference"]
            ][
                "value"
            ]
            is not None
            else None
        ),
        axis=1,
    )

    url_head = "https://pcmdi.llnl.gov/pmp-preliminary-results/interactive_plot/portrait_plot/enso_metric/dynamic_html/EnsoDiveDown.html?"
    df_mapped["Plot"] = df_mapped.apply(
        lambda row: (
            f"{url_head}mip={row['MIP']}&model={row['Model']}&exp=historical&run=r1i1p1f1&metric={row['metric_code']}&metric_dd={row['metric_code']}&MC={row['Collection']}&metric_name={row['Metric']}&nvalue=&avalue{row['Value']}=&ver=v20201122"
            if row["MIP"] == "cmip6"
            else f"{url_head}mip={row['MIP']}&model={row['Model']}&exp=historical&run=r1i1p1&metric={row['metric_code']}&metric_dd={row['metric_code']}&MC={row['Collection']}&metric_name={row['Metric']}&nvalue=&avalue={row['Value']}&ver=v20201122"
        ),
        axis=1,
    )

    df_mapped = df_mapped[["MIP", "Model", "Collection", "Metric", "Value", "Plot"]]

    return df_mapped


# -------------------
# Layer III Functions
# -------------------
def create_viewer_dict(metrics, mips, exps):  # need to add version numbers
    """
    Constructs a dictionary from input lists.

    Parameters
    ----------
    metrics : list
        List of metrics (e.g., ['mean_climate', 'variability_modes', 'enso_metric']).
    mips : list
        The model intercomparison projects (e.g, ['cmip5', 'cmip6']).
    exps : list
        The experiments (e.g., ['historical', 'amip']).

    Returns
    ----------
    dict
        A dictionary of URLs to json files saved on the PMP Database Archive.
    """
    viewer_dict = {}

    for metric in metrics:
        viewer_dict[metric] = {}
        for mip in mips:
            viewer_dict[metric][mip] = {}
            for exp in exps:
                try:
                    viewer_dict[metric][mip][exp] = find_pmp_archive_json_urls(
                        metric, mip, exp
                    )
                except Exception:
                    print(f"skipping Failed to fetch URL: {metric}, {mip}, {exp}")

    return viewer_dict


def retrieve_lists(metrics_dict, metric_name, mips):
    """
    Uses PMP Database API to retrieve json data from the PMP database archive.

    Parameters
    ----------
    metrics_dict : dict
        A dictionary containing the json URLs for desired retrieval.
    metric_name : str
        Name metric will be given in the dictionary (e.g., "mean_climate", "mov", "enso").

    Returns
    ----------
    lists
        Seven lists based on available data in the PMP Database Archive are returned for easy construction of dataframes for the data table (e.g., exps, cmip6_models, cmip5_models, all_models, all_vars, regions, seasons).
    """
    # Get all models
    cmip6_models_temp = []
    cmip5_models_temp = []

    cmip6_models = []
    cmip5_models = []
    all_models = []

    exps = list(metrics_dict[mips[0]].keys())

    for mip in mips:
        if mip == "cmip6":
            for exp in exps:
                json_data = load_json_from_url(metrics_dict["cmip6"][exp][0])
                cmip6_models_temp.append(list(json_data["RESULTS"].keys()))
            for m6 in cmip6_models_temp:
                cmip6_models.extend(m6)
            cmip6_models = np.unique(cmip6_models)
            cmip6_models.sort()
        if mip == "cmip5":
            for exp in exps:
                json_data = load_json_from_url(metrics_dict["cmip5"][exp][0])
                cmip5_models_temp.append(list(json_data["RESULTS"].keys()))
            for m5 in cmip5_models_temp:
                cmip5_models.extend(m5)
            cmip5_models = np.unique(cmip5_models)
            cmip5_models.sort()

    all_models = np.concatenate((cmip6_models, cmip5_models))

    all_models = np.unique(all_models)
    all_models.sort()

    # Get var names
    vars = []
    all_vars = []
    for mip in list(metrics_dict.keys()):
        for exp in list(metrics_dict[mip].keys()):
            try:
                results_dict = database_metrics(
                    mip=mip, model=all_models[0], exp=exp, metrics=[metric_name]
                )
                vars.append(list(results_dict[metric_name].keys()))
            except Exception:
                print(f"skipping Failed to fetch URL: {mip}, {all_models[0]}, {exp}")

    for v in vars:
        all_vars.extend(v)

    all_vars = np.unique(all_vars)
    all_vars.sort()

    regions = ["global", "NHEX", "SHEX", "TROPICS"]
    seasons = ["ANN", "DJF", "MAM", "JJA", "SON"]

    return exps, cmip6_models, cmip5_models, all_models, all_vars, regions, seasons


def add_var_long_name(df):
    """
    Uses 'long_name' column in the CMIP6 Amon table to add a variable description to the table.

    Parameters
    ----------
    df : pandas dataframe
        A dataframe to add the description field to.

    Returns
    ----------
    pandas dataframe
        The same dataframe with added "description" column.
    """
    with open("./assets/CMIP6_Amon.json", "r") as file:
        cmor_table = json.load(file)

    var_to_long_name = {
        var: details.get("long_name", "Unknown")
        for var, details in cmor_table.get("variable_entry", {}).items()
    }

    df["Description"] = df["Variable"].apply(
        lambda var: var_to_long_name.get(extract_base_var(var), "NaN")
    )
    return df


def extract_base_var(var_name):
    """
    Extracts the base name of the variable.

    Parameters
    ----------
    var_name : str
        A string variable name as it appears in the json dictionary (e.g., 'ua-200').

    Example
    ----------
    For variables with different layers, use the base name to match to a name in the AMON table. (e.g., For ua-200 use ua)

    Returns
    ----------
    str
        The corresponding value as it appears in the AMON table.
    """
    return var_name.split("-")[0]


def find_enso_ref():
    """
    Uses the PMP ENSO lib API to retrieve the name of the reference dataset for various ENSO metrics.

    Returns
    ----------
    dict
        A dictionary of ENSO reference information downloaded from the PCMDI Archive github.
    """
    db_url_head = "https://github.com/PCMDI/pcmdi_metrics_results_archive/tree/main/metrics_results/enso_metric"

    dirs_to_downlaod = [
        "cmip5/historical/v20210104/ENSO_perf",
        "cmip5/historical/v20210104/ENSO_tel",
        "cmip5/historical/v20210104/ENSO_proc",
        "cmip6/historical/v20210620/ENSO_perf",
        "cmip6/historical/v20210620/ENSO_tel",
        "cmip6/historical/v20210620/ENSO_proc",
        "obs2obs",
    ]

    path_json = "json_files"

    for directiry in dirs_to_downlaod:
        github_directory_url = os.path.join(db_url_head, directiry)
        download_files_from_github(github_directory_url, path_json)

    list_project = ["CMIP5", "CMIP6"]
    list_obs = ["20CRv2", "NCEP2", "ERA-Interim"]

    metrics_collections = ["ENSO_perf", "ENSO_tel", "ENSO_proc"]
    mips = ["CMIP5", "CMIP6", "obs2obs"]

    dict_json_path = dict()
    for mip in mips:
        dict_json_path[mip] = dict()
        for metrics_collection in metrics_collections:
            dict_json_path[mip][metrics_collection] = glob(
                os.path.join(path_json, f"{mip.lower()}*{metrics_collection}_*.json")
            )[0]

    ref_info_dict = json_dict_to_numpy_array_list(
        metric_collections=metrics_collections,
        list_project=list_project,
        list_obs=list_obs,
        dict_json_path=dict_json_path,
        reduced_set=True,
        met_order=None,
        mod_order=None,
    )[-1]

    return ref_info_dict
