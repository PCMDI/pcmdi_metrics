# - Generate an html file of compiled PMP graphics using Bokeh.
# - Author: Kristin Chang (2024.12)
# - Last Update: 2024.12

import os
import shutil
from typing import Optional, Dict, Union

from bokeh.models import ColumnDataSource, DataTable, TableColumn, MultiChoice, CustomJS, HTMLTemplateFormatter, Tooltip
from bokeh.models.dom import HTML
from bokeh.models import Div
from bokeh import events
from bokeh.layouts import column, row
from bokeh.io import output_file, save
import pandas as pd
import numpy as np
import glob
import json

from pcmdi_metrics.graphics import download_archived_results
from pcmdi_metrics.graphics import Metrics

def view_pmp_output(
        mean_clim_divedown_path: Optional[str] = None,
        mean_clim_divedown_thumbnail: Optional[str] = None,
        mean_clim_portrait_path: Optional[str] = None,
        mean_clim_portrait_thumbnail: Optional[str] = None,
        mov_path: Optional[str] = None,
        mov_thumbnail: Optional[str] = None,
        enso_path: Optional[str] = None,
        enso_thumbnail: Optional[str] = None,
        version: str = "v20241101",
        season_map: Dict[str, Dict[str, Union[int, float, str]]] = {'AC':'ANN'},
        compare_cmip6: bool = False
):
    """
    Generates an html file of compiled PMP graphics using Bokeh. 

    Parameters
    ----------
    graphics_path : str, optional
        A string for the directory path where graphics are saved. Default is None.
    version : str
        A string for the version number of the images. # NEED TO CONFIRM
    season_map : dict
        A dictionary to map different season abbreviations. Default maps PMP acronym for Annual Climatology to E3SM acronym: {'AC':'ANN'}. 
    compare_cmip6 : bool, optional
        If True, the viewer will include cmip6 results. Default is False.

    Returns
    ----------
    webpage : html files
        Multiple html files with pmp_output_viewer.html as the home page. One html file is generated per plot subfolder in graphics_path with valid png images.
        Example directory path: graphics > mean_climate > e3sm > amip > v20241101 >portrait_plot
            Example return: Two html files; pmp_output_viewer.html and mean_climate_portrait_plot_results.html
    
    Example
    ----------
    >>>from pmp_output_viewer import view_pmp_output

    Notes
    ----------
    - Function(s) support limited variations of names for each summary:
        - Mean Climate : ['mean_climate', 'mean_clim', 'climate_mean', 'clim_mean']
        - Modes of Variability: ['modes_of_variability', 'variability_modes', 'modes_of_var', 'var_modes', 'mov', 'MOV']
    
    """
    viewer_dir = os.getcwd()
    # ----------
    # Check if directory path provided is a valid directory
    # ----------
    if not os.path.isdir(mean_clim_divedown_path):
        raise ValueError(f"The provided path '{mean_clim_divedown_path}' is not a valid directory.")

    if not os.path.isdir(mov_path):
        raise ValueError(f"The provided path '{mov_path}' is not a valid directory.")    
    
    # ----------
    # Create home page
    # ----------

    # CSS styles
    css_styles = """
    body {
        font-family: "Roboto", sans-serif;
        display: block;
        align-items: center;
        margin: 0;
        text-align: center;
    }
    .container {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        font-size: 48px;
        font-weight: black;
        margin-bottom: 20px;
        width: 100%;
    }
    .subtitle {
        text-align: center;
        font-size: 22px;
        font-weight: normal;
        margin-bottom: 20px;
    }
    table {
        width: 1200px;
        table-layout: fixed;
        border-collapse: collapse;
        margin: 20px auto;
    }
    table th, td {
        border: 1px solid #ddd;
        padding: 10px;
    }
    td:first-child {
        width: 25%;
    }
    table a {
    font-size: 22px;
    }

    preview img {
        height: 400px;
        width: auto;
    }

    a {
        font-size: 16px;
    }

    /* Style table cells */
    .data-table table {
        font-size: 16px !important;
    }

    /* Style table headers */
    .data-table .slick-header-columns {
        font-size: 16px !important;
        font-weight: bold;
    }

    /* Adjust header spacing */
    .data-table .slick-header-column {
        padding: 5px;
    }

    """
    home_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PMP Output Viewer</title>
        <div class="container">
            <img src="./PCMDILogoText_1365x520px_300dpi.png" alt="PCMDI_logo" width="250px" style="margin-right: 850px; margin-top:20px;">
            <img src="./PMPLogo_500x421px_72dpi.png" alt="PMP_logo" width="100px">    
        </div>
        <div class="header">PMP Output Viewer</div>
        <div class="subtitle">(Prototype)</div>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400&display=swap" rel="stylesheet">
        <style>
            {css_styles}
        </style>
    </head>
    <body>
    """
    # Run corresponding functions to generate individual plot pages
    mean_clim_divedown_summaries, mean_clim_divedown_version_path, mean_clim_divedown_plot_paths = navigate_graphics_dir(dir_path=mean_clim_divedown_path, version=version)

    for mean_clim_divedown_plot_path in mean_clim_divedown_plot_paths:
        if check_png_files(mean_clim_divedown_plot_path):
            mean_clim_divedown_summary_name = mean_clim_divedown_plot_path.split('/')[-5] 
            mean_clim_divedown_plot_name = os.path.basename(mean_clim_divedown_plot_path)
            layout = create_mean_clim_divedown_layout(plot_path=mean_clim_divedown_plot_path, season_map=season_map, compare_cmip6=compare_cmip6)
            output_file(f"./{mean_clim_divedown_summary_name}_{mean_clim_divedown_plot_name}_results.html")
            save(layout)
    
    if mean_clim_portrait_path:
        mean_clim_portrait_summaries, mean_clim_portrait_version_path, mean_clim_portrait_plot_paths = navigate_graphics_dir(dir_path=mean_clim_portrait_path, version=version)

        for mean_clim_portrait_plot_path in mean_clim_portrait_plot_paths:
            if check_png_files(mean_clim_portrait_plot_path):
                mean_clim_portrait_summary_name = mean_clim_portrait_plot_path.split('/')[-5]
                mean_clim_portrait_plot_name = os.path.basename(mean_clim_portrait_plot_path)
                layout = create_mean_clim_portrait_layout(plot_path=mean_clim_portrait_plot_path)
                output_file(f"./{mean_clim_portrait_summary_name}_{mean_clim_portrait_plot_name}_results.html")
                save(layout)
    
    # Adding MOV
    if mov_path:
        mov_summaries, mov_version_path, mov_plot_paths = navigate_graphics_dir(dir_path=mov_path, version=version)
        
        source_dir = mov_version_path[0]
        destination_dir = os.path.join(mov_version_path[0], 'pmp_viewer_all_modes')
        os.makedirs(destination_dir, exist_ok=True)
        
        for mov_plot_path in mov_plot_paths:
            if check_png_files(mov_plot_path):
                mov_summary_name = mov_plot_path.split('/')[-5]
                mov_plot_name = os.path.basename(mov_plot_path)
                # walk through source directory
                for root, _, files in os.walk(mov_plot_path):
                    for file in files:
                        source_path = os.path.join(root, file) # full path of the file
                        destination_path = os.path.join(destination_dir, file)
                        # copy to new directory
                        shutil.copy2(source_path, destination_path)

        layout = create_mov_layout(destination_dir)
        output_file(f"./{mov_summaries[0]}_results.html")
        save(layout)
    
    # Adding ENSO
    if enso_path:
        enso_summaries, enso_version_path, enso_plot_paths = navigate_graphics_dir(dir_path=enso_path, version=version)

        source_dir = enso_version_path[0]
        destination_dir = os.path.join(enso_version_path[0], 'pmp_viewer_all_enso')
        os.makedirs(destination_dir, exist_ok=True)

        for enso_plot_path in enso_plot_paths:
            if check_png_files(enso_plot_path):
                for root, _, files in os.walk(enso_plot_path):
                    collection_name = os.path.basename(root) # add the collection name to each file name
                    for file in files:
                        source_path = os.path.join(root, file)
                        #new_filename = f"{collection_name}_{file}"
                        #destination_path = os.path.join(destination_dir, new_filename)
                        shutil.copy2(source_path, destination_dir)

        layout = create_enso_layout(destination_dir)
        output_file(f"./{enso_summaries[0]}_results.html")
        save(layout)
    
    # Construct Main page
    home_content += f'<table><tr><td><a href="mean_climate_dive_down_results.html">Mean Climate Dive Down</a></td>\n'
    if mean_clim_divedown_thumbnail:
        home_content += f'<td><preview><a href="mean_climate_dive_down_results.html"><img src="{mean_clim_divedown_thumbnail}" alt="plot_preview"></a></preview></td></tr>\n'
    else:
        plot_path = mean_clim_divedown_plot_paths[0]
        files = glob.glob(plot_path + '/*.png')
        first_image = files[0]
        home_content += f'<td><preview><a href="mean_climate_dive_down_results.html"><img src="{first_image}" alt="plot_preview"></a></preview></td></tr>\n'

    if mean_clim_portrait_path:
        home_content += f'<tr><td><a href="mean_climate_portrait_4seasons_results.html">Mean Climate Portrait Plot</a></td>\n'
        if mean_clim_portrait_thumbnail:
            home_content += f'<td><preview><a href="mean_climate_portrait_4seasons_results.html"><img src="{mean_clim_portrait_thumbnail}" alt="plot_preview"></a></preview></td></tr>\n'
        else:
            plot_path = mean_clim_portrait_plot_paths[0]
            files = glob.glob(plot_path + '/*.png')
            first_image = files[0]
            home_content += f'<td><preview><a href="mean_climate_portrait_4seasons_results.html"><img src="{first_image}" alt="plot_preview"></a></preview></td></tr>\n'

    if mov_path:
        home_content += f'<tr><td><a href="variability_modes_results.html">Modes of Variability</a></td>\n'
        if mov_thumbnail:
            home_content += f'<td><preview><a href="variability_modes_results.html"><img src="{mov_thumbnail}" alt="plot_preview"></a></preview></td></tr>\n'
        else:
            plot_path = mov_plot_paths[0]
            files = glob.glob(plot_path + '/*.png')
            first_image = files[0]
            home_content += f'<td><preview><a href="variability_modes_results.html"><img src="{first_image}" alt="plot_preview"></a></preview></td></tr>\n'

    if enso_path:
        home_content += f'<tr><td><a href="enso_metric_results.html">ENSO</a></td>\n'
        if enso_thumbnail:
            home_content += f'<td><a href="enso_metric_results.html"><img src="{enso_thumbnail}" alt="plot_preview"></a></td></tr>\n'
        else:
            plot_path = enso_plot_paths[0]
            files = glob.glob(plot_path + '/*.png')
            first_image = files[0]
            home_content += f'<td><a href="enso_metric_results.html"><img src="{first_image}" alt="plot_preview"></a></td></tr>\n'

    # close html tags
    home_content += """
    </tr>
    </table>
    </div>
    </body>
    </html>
    """
    
    # save home page as html
    with open("pmp_output_viewer.html", "w") as pov_file:
        pov_file.write(home_content)

    cwd = os.getcwd()
    return print(f"POV created in {cwd}")

# ----------
# Support functions
# ----------

def navigate_graphics_dir(dir_path, version):
    """
    Navigates summary folder to png files.

    Parameters
    ----------
    graphics_path : str, optional
        A string for the directory path where graphics are saved. Default is None.
    version : str
        A string for the version number of the images. # NEED TO CONFIRM

    Returns
    ----------
    Two arrays
        One contains the names of summary folders. One contains the paths to the folder containing png files.
    
    Example
    ----------
    summary folder > e3sm > amip > version > plot type > png files
    plot_path: summary/e3sm/amip/version/dive_down
    """
   
    summaries = [name for name in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, name))]
    summary_paths = []
    e3sm_paths = []
    amip_paths = []
    version_paths = []
    plot_paths = []

    for summary in summaries:
        summary_path = os.path.join(dir_path, summary)
        summary_paths.append(summary_path)

    for summary_path in summary_paths:
        e3sm_path = os.path.join(summary_path, 'e3sm')
        e3sm_paths.append(e3sm_path)

    for e3sm_path in e3sm_paths:
        amip_path = os.path.join(e3sm_path, 'amip')
        amip_paths.append(amip_path)

    for amip_path in amip_paths:
        version_path = os.path.join(amip_path, version)
        version_paths.append(version_path)

    for version_path in version_paths:
        plot_dirs = [os.path.join(version_path, plot_folder)
        for plot_folder in os.listdir(version_path)
        if os.path.isdir(os.path.join(version_path, plot_folder))]
        plot_paths.extend(plot_dirs)

    return summaries, version_paths, plot_paths

# checks if png files are available
def check_png_files(path):
    # check if the folder contains png files
    for filename in os.listdir(path):
        if filename.lower().endswith('.png'):
            return True
    return False

def add_var_long_name(df):
    """
    Uses 'long_name' column in the CMIP6 Amon table to add a variable description to the table.

    Parameters
    ----------
    df : pandas dataframe
        dataframe to add the description field to.
    """
    with open('./CMIP6_Amon.json', 'r') as file:
        cmor_table = json.load(file)

    var_to_long_name = {
        var: details.get('long_name', 'Unknown')
        for var, details in cmor_table.get('variable_entry', {}).items()
    }
    
    df['Description'] = df['Variable'].apply(lambda var: var_to_long_name.get(extract_base_var(var), 'NaN'))
    return df

def extract_base_var(var_name):
    """
    Extracts the base name of the variable.

    Example
    ----------
    For variables with different layers, use the base name to match to a name in the AMON table. (e.g., For ua-200 use ua)

    Returns
    ----------
    Pandas dataframe with a new column 'Description'.
    """
    return var_name.split('-')[0]

def create_mean_clim_divedown_user_df(plot_path, season_map={'AC':'ANN'}):
    """
    Create a dataframe from the provided directory path. (User model)

    Parameters
    ----------
    plot_path : str, optional
        A string for the directory path where graphics are saved. Default is None.
    season_map : dict
        A dictionary to map different season abbreviations. Default maps pmp acronym for Annual Climatology to E3SM acronym: {'AC':'ANN'}.
    
    Returns
    ----------
    pandas dataframe
        A table with columns: mip, model, variable, description, region, ANN, DJF, JJA, MAM, SON
    """
    data = {}
    season_map = season_map or {} # Default to empty dict if none

    for this_path, this_dir, files in os.walk(plot_path):
        for file in files:
            if file.endswith(('png')):
                # extract file components based on underscores
                parts = file.split('_')
                if len(parts) >= 8:
                    variable = parts[0]
                    model = parts[1]
                    region = parts[5]
                    season = parts[6]
                    mip = 'cmip6' # FIX LATER

                    # rename season if mapping provided
                    season = season_map.get(season, season)
                else:
                    model, region, season = None, None, None

                # construct image file path
                file_path = os.path.join(plot_path, file)

                # use unique key to group data
                key = (variable, model, region)

                # initialize row if not already present
                if key not in data:
                    data[key] = {
                        'MIP': mip,
                        'Model': model,
                        'Variable': variable,
                        'Region': region,
                    }

                # Add each season column with the image path
                data[key][season] = file_path

    df = pd.DataFrame.from_dict(data, orient='index')
    df.reset_index(drop=True, inplace=True)
    df = add_var_long_name(df)

    return df

def create_cmip6_df(mip='cmip6', exp='historical', data_version='v20230823'):
    """
    Create results using cmip6 data.

    Parameters
    ----------
    mip : str, optional
        String for MIP. Default is cmip6.
    exp : str, optional
        String for experiment (?). Default is historical.
    data_version : str, optional
        String for data version. Default is most recent available v20230823.

    Returns
    ----------
    pandas dataframe
        A table with columns: mip, model, variable, description, region, ANN, DJF, JJA, MAM, SON
    """
    # download cmip6 data using pmp
    cmip6_dir = './pov_cmip6_mean_clim_json_files'
    os.makedirs(cmip6_dir, exist_ok=True)
    #try:
    #    os.mkdir(cmip6_dir)
    #except FileExistsError:
    #    raise FileExistsError(f"Error: The directory '{cmip6_dir}' already exists!")
    
    vars = ['pr', 'prw', 'psl', 'rlds', 'rltcre', 'rlus', 'rlut', 'rlutcs', 'rsds', 'rsdscs', 'rsdt', 'rstcre', 'rsut', 'rsutcs', 'sfcWind', 
    'ta-200', 'ta-850', 'tas', 'tauu', 'ts', 'ua-200', 'ua-850', 'va-200', 'va-850', 'zg-500']
    mip = mip
    exp = exp
    data_version = data_version
    for var in vars:
        path = "metrics_results/mean_climate/"+mip+"/"+exp+"/"+data_version+"/"+var+"."+mip+"."+exp+".regrid2.2p5x2p5."+data_version+".json"
        download_archived_results(path, cmip6_dir)

    json_list = sorted(glob.glob(os.path.join(cmip6_dir, '*.' + mip + '.' + exp + '*' + data_version + '.json')))
    library_cmip6 = Metrics(json_list, mip=mip)
    
    # construct df from json data
    seasons = ['djf', 'jja', 'mam', 'son']
    regions = ['global', 'NHEX', 'SHEX', 'TROPICS']
    region_dfs = []
    for r in regions:
        region_df = library_cmip6.df_dict['bias_xy']['djf'][r]
        region_df = region_df.drop(columns=['mip', 'model_run'])
        id_vars = ['model', 'run']
        value_vars = [col for col in region_df.columns if col not in id_vars]
        region_df = pd.melt(region_df, id_vars = id_vars, value_vars = value_vars, var_name = "Variable", value_name='value').drop(columns=['value'])
        region_df['Region'] = r

        region_dfs.append(region_df)
    
    season_df = pd.concat(region_dfs).drop_duplicates()
    img_url = "https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/amip/clim/v20241029"
    for s in seasons:
        season_df[s.upper()] = season_df.apply(lambda row: f"{img_url}/{row['Variable']}/{row['Variable']}_{row['model']}_{row['run']}_interpolated_regrid2_{row['Region']}_{s.upper()}_v20241029.png", axis=1)
    
    season_df['ANN'] = season_df.apply(lambda row: f"{img_url}/{row['Variable']}/{row['Variable']}_{row['model']}_{row['run']}_interpolated_regrid2_{row['Region']}_AC_v20241029.png", axis=1)
    season_df = season_df.drop(columns = ['run'])
    season_df = season_df.rename(columns={'model': 'Model'})
    season_df['MIP'] = mip
    
    cmip6_df = season_df
    
    return cmip6_df

def create_mean_clim_divedown_layout(plot_path, season_map={'AC':'ANN'}, compare_cmip6=False):
    """
    Creates results page with bokeh filters and table.

    Parameters
    ----------
    plot_path : str, optional
        A string for the directory path where graphics are saved. Default is None.
    season_map : dict
        A dictionary to map different season abbreviations. Default maps pmp acronym for Annual Climatology to E3SM acronym: {'AC':'ANN'}. 
    compare_cmip6 : bool, optional
        If True, the viewer will include cmip6 results. Default is False.

    Returns
    ----------
    bokeh layout object

    """
    if plot_path:
        user_df = create_mean_clim_divedown_user_df(plot_path=plot_path, season_map=season_map).sort_values(['MIP', 'Model', 'Variable', 'Region'])
    else:
        user_df = pd.DataFrame()
        
    if compare_cmip6:
        cmip6_df = create_cmip6_df().sort_values(['MIP', 'Model', 'Variable', 'Region'])
        cmip6_df = add_var_long_name(cmip6_df)
        df = pd.concat([user_df, cmip6_df])
    else:
        df = user_df

    source = ColumnDataSource(data=dict(df))
    filtered_data = df.loc[df['Region']=='global']
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient="list"))

    # HTML Template for image links
    image_templates = {}
    image_formatters = {}
    seasons = ['ANN', 'DJF', 'JJA', 'MAM', 'SON']
    for s in seasons:
        image_templates[f"{s}_template"] = f"""
        <div style="position: relative; font-size:16px;">
            <a href="<%= {s} %>" target="_blank">{s}</a>
        </div>
        """
        # <a href="<%= {s} %>" target="_blank">{s}</a>
        image_formatters[f"{s}_formatter"] = HTMLTemplateFormatter(template=image_templates[f"{s}_template"])

        # hover_preview = Tooltip(content=HTML("<div class=""tooltip"" style=""visibility: hidden; position: absolute; z-index: 10; top: -150px; left: 20px; background-color: white; border: 1px solid black; padding: 5px;""><img src=""<%= {s} %>"" style=""width: 150px; height: auto;""/></div>"))
    
    # Custom JS for hover tooltip
    tooltip_callback = CustomJS(
        args=dict(source=source),
        code="""
        const element = this.parentElement;
        const tooltip = element.querySelector('.tooltip);
        element.addEventListener('mouseover', function() {
            tooltip.style.visibility = 'visible';
        });
        element.addEventListener('mouseout', function () {
            tooltip.style.visibility = 'hidden';
        });
        """
    )

    # hover_preview.js_on_event(events.MouseEnter, hover_preview, tooltip_callback)

    text_only_formatter = HTMLTemplateFormatter(template='<span style="font-size:16px;"> <%= value %> </span>')

    # Table setup
    columns = [
        TableColumn(field="MIP", title="MIP", formatter=text_only_formatter),
        TableColumn(field="Model", title="Model", formatter=text_only_formatter),
        TableColumn(field="Variable", title="Variable", formatter=text_only_formatter),
        TableColumn(field="Description", title="Description", formatter=text_only_formatter),
        TableColumn(field="Region", title="Region", formatter=text_only_formatter),
        TableColumn(field="ANN", title="ANN", formatter=image_formatters["ANN_formatter"]),
        TableColumn(field="DJF", title="DJF", formatter=image_formatters["DJF_formatter"]),
        TableColumn(field="JJA", title="JJA", formatter=image_formatters["JJA_formatter"]),
        TableColumn(field="MAM", title="MAM", formatter=image_formatters["MAM_formatter"]),
        TableColumn(field="SON", title="SON", formatter=image_formatters["SON_formatter"])
    ]

    dtable = DataTable(source=filtered_source, columns=columns, width=1600, height=1200, row_height=30)

    # Filter widgets
    mip_dropdown = MultiChoice(
        options=list(df['MIP'].unique()),
        title="Select MIP",
        value=[]
    )

    model_dropdown = MultiChoice(
        options=list(df['Model'].unique()), 
        title="Select Model",
        value=[]
    )

    var_dropdown = MultiChoice(
        options=list(df['Variable'].unique()),
        title="Select Variable",
        value=[]
    )

    region_dropdown = MultiChoice(
        options=list(df['Region'].unique()),
        title="Select Region", 
        value=['global']
    )

    # JS Callback to filter df
    dropdown_callback = CustomJS(
        args=dict(source=source, filtered_source=filtered_source, mip_dropdown=mip_dropdown, model_dropdown=model_dropdown, var_dropdown=var_dropdown, region_dropdown=region_dropdown),
        code="""
        const original_data = source.data;
        const filtered_data = { MIP: [], Model: [], Variable: [], Description: [], Region: [], ANN: [], DJF: [], JJA: [], MAM: [], SON: [] };

        const selected_mips = mip_dropdown.value;
        const selected_models = model_dropdown.value;
        const selected_vars = var_dropdown.value;
        const selected_regions = region_dropdown.value;

        for (let i = 0; i < original_data.Model.length; i++) {
            const in_mip = selected_mips.length === 0 || selected_mips.includes(original_data.MIP[i]);
            const in_model = selected_models.length === 0 || selected_models.includes(original_data.Model[i]);
            const in_var = selected_vars.length === 0 || selected_vars.includes(original_data.Variable[i]);
            const in_region = selected_regions.length === 0 || selected_regions.includes(original_data.Region[i]);

            if (in_mip && in_model && in_var && in_region) {
                filtered_data.MIP.push(original_data.MIP[i]);
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
        """
    )
    title_text = Div(text="""
                     <br>
                     <h1> PMP Mean Climate Dive Down Plots </h1>
                     <br>
                     <h2>Filters</h2>
    """)

    mip_dropdown.js_on_change('value', dropdown_callback)
    model_dropdown.js_on_change('value', dropdown_callback)
    var_dropdown.js_on_change('value', dropdown_callback)
    region_dropdown.js_on_change('value', dropdown_callback)

    layout = column(title_text, row(mip_dropdown, model_dropdown, var_dropdown, region_dropdown), dtable)
    return layout

def create_mean_clim_portrait_df(plot_path):
    data = {}

    for this_path, this_dir, files in os.walk(plot_path):
        for file in files:
            if file.endswith(('png')):
                parts = file.split('_')
                if len(parts) >= 8:
                    variable = parts[0]
                    model = parts[1]
                    region = parts[5]
                else:
                    variable, model, region = None, None, None
                
                file_path = os.path.join(plot_path, file)

                key = (variable, model, region)

                if key not in data:
                    data[key] = {
                        'Model': model,
                        'Variable': variable,
                        'Region': region,
                        'Preview': file_path
                    }
    df = pd.DataFrame.from_dict(data, orient='index')
    df.reset_index(drop=True, inplace=True)
    
    return df

def create_mean_clim_portrait_layout(plot_path):
    if plot_path:
        user_df = create_mean_clim_portrait_df(plot_path=plot_path)
    else:
        user_df = pd.DataFrame()

    df = user_df

    source = ColumnDataSource(data=dict(df))
    filtered_data = df
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient='list'))

    image_template = f"""
        <div style="position: relative;">
            <a href="<%= Preview %>" target="_blank"><img src="<%= Preview %>" alt="preview" height=300></a>
        </div>
        """
    image_formatter = HTMLTemplateFormatter(template=image_template)
    text_only_formatter = HTMLTemplateFormatter(template='<span style="font-size:16px;"> <%= value %> </span>')


    columns=[
        TableColumn(field="Model", title="Model", formatter=text_only_formatter),
        TableColumn(field="Variable", title="Variable", formatter=text_only_formatter),
        TableColumn(field="Region", title="Region", formatter=text_only_formatter),
        TableColumn(field="Preview", title="Preview", formatter=image_formatter, width=700)
    ]

    dtable = DataTable(source=filtered_source, columns=columns, width=1600, height=1200, row_height=320)

    model_dropdown = MultiChoice(
        options=list(df['Model'].unique()),
        title="Select Model",
        value=[]
    )

    var_dropdown = MultiChoice(
        options=list(df['Variable'].unique()),
        title="Select Variable",
        value=[]
    )

    region_dropdown = MultiChoice(
        options=list(df['Region'].unique()),
        title="Select Region",
        value=[]
    )

    portrait_dropdown_callback = CustomJS(
        args=dict(source=source, filtered_source=filtered_source, model_dropdown=model_dropdown, var_dropdown=var_dropdown, region_dropdown=region_dropdown),
        code="""
        const original_data = source.data;
        const filtered_data = { Model: [], Variable: [], Region: [], Preview: []};

        const selected_models = model_dropdown.value;
        const selected_vars = var_dropdown.value;
        const selected_regions = region_dropdown.value;

        for (let i = 0; i < original_data.Model.length; i++) {
        const in_model = selected_models.length === 0 || selected_models.includes(original_data.Model[i]);
            const in_var = selected_vars.length === 0 || selected_vars.includes(original_data.Variable[i]);
            const in_region = selected_regions.length === 0 || selected_regions.includes(original_data.Region[i]);

            if (in_model && in_var && in_region) {
                filtered_data.Model.push(original_data.Model[i]);
                filtered_data.Variable.push(original_data.Variable[i]);
                filtered_data.Region.push(original_data.Region[i]);
                filtered_data.Preview.push(original_data.Preview[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """
    )

    title_text = Div(text="""
                     <br>
                     <h1> PMP Mean Climate Portrait Plots </h1>
                     <br>
                     <h2>Filters</h2>
    """)

    model_dropdown.js_on_change('value', portrait_dropdown_callback)
    var_dropdown.js_on_change('value', portrait_dropdown_callback)
    region_dropdown.js_on_change('value', portrait_dropdown_callback)

    layout = column(title_text,row(model_dropdown, var_dropdown, region_dropdown), dtable)
    return layout

def create_mov_df(mov_all_modes_path):
    
    data = {}

    for this_path, this_dir, files in os.walk(mov_all_modes_path):
        for file in files:
            if file.endswith(('png')):
                parts = file.split('_')
                if len(parts) >= 8:
                    mode = parts[0]
                    variable = parts[1]
                    season = parts[3]
                    method = parts[11]
                else:
                    mode, variable, season, method = None, None, None, None

                file_path = os.path.join(mov_all_modes_path, file)

                key = (mode, variable, season, method)

                if key not in data:
                    data[key] = {
                        'Mode': mode,
                        'Variable': variable,
                        'Season': season,
                        'Method': method
                    }

                data[key]['Preview'] = file_path
    
    df = pd.DataFrame.from_dict(data, orient='index')
    df.reset_index(drop=True, inplace=True)
    df = add_var_long_name(df)

    return df

def create_mov_layout(mov_all_modes_path):
    if mov_all_modes_path:
        user_df = create_mov_df(mov_all_modes_path=mov_all_modes_path).sort_values(['Mode', 'Variable', 'Season', 'Method'])
    else:
        user_df = pd.DataFrame()
    
    df = user_df

    source = ColumnDataSource(data=dict(df))
    filtered_data = df
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient='list'))

    image_template = f"""
        <div style="position: relative;">
            <a href="<%= Preview %>" target="_blank"><img src="<%= Preview %>" alt="preview" height=300></a>
        </div>
        """
    image_formatter = HTMLTemplateFormatter(template=image_template)

    text_only_formatter = HTMLTemplateFormatter(template='<span style="font-size:16px;"> <%= value %> </span>')

    columns = [
        TableColumn(field="Mode", title="Mode", formatter=text_only_formatter),
        TableColumn(field="Variable", title="Variable", formatter=text_only_formatter),
        TableColumn(field="Description", title="Description", formatter=text_only_formatter),
        TableColumn(field="Season", title="Season", formatter=text_only_formatter),
        TableColumn(field="Method", title="Method", formatter=text_only_formatter),
        TableColumn(field="Preview", title="Preview", formatter=image_formatter, width=450)
    ]

    dtable = DataTable(source=filtered_source, columns=columns, width=1600, height=1200, row_height=320)

    mode_dropdown = MultiChoice(
        options=list(df['Mode'].unique()),
        title="Select Mode",
        value=[]
    )

    var_dropdown = MultiChoice(
        options=list(df['Variable'].unique()),
        title="Select Variable",
        value=[]
    )

    season_dropdown = MultiChoice(
        options=list(df['Season'].unique()),
        title="Select Season",
        value=[]
    )

    method_dropdown = MultiChoice(
        options=list(df['Method'].unique()),
        title="Select Method",
        value=[]
    )

    mov_dropdown_callback = CustomJS(
        args=dict(source=source, filtered_source=filtered_source, mode_dropdown=mode_dropdown, var_dropdown=var_dropdown, season_dropdown=season_dropdown, method_dropdown=method_dropdown),
        code="""
        const original_data = source.data;
        const filtered_data = { Mode: [], Variable: [], Description: [], Season: [], Method: [], Preview: []};

        const selected_modes = mode_dropdown.value;
        const selected_vars = var_dropdown.value;
        const selected_seasons = season_dropdown.value;
        const selected_methods = method_dropdown.value;

        for (let i = 0; i < original_data.Season.length; i++) {
            const in_mode = selected_modes.length === 0 || selected_modes.includes(original_data.Mode[i]);
            const in_var = selected_vars.length === 0 || selected_vars.includes(original_data.Variable[i]);
            const in_season = selected_seasons.length === 0 || selected_seasons.includes(original_data.Season[i]);
            const in_method = selected_methods.length === 0 || selected_methods.includes(original_data.Method[i]);

            if (in_mode && in_var && in_season && in_method) {
                filtered_data.Mode.push(original_data.Mode[i]);
                filtered_data.Variable.push(original_data.Variable[i]);
                filtered_data.Description.push(original_data.Description[i]);
                filtered_data.Season.push(original_data.Season[i]);
                filtered_data.Method.push(original_data.Method[i]);
                filtered_data.Preview.push(original_data.Preview[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """
    )

    title_text = Div(text="""
                     <br>
                     <h1> PMP Modes of Variability Metrics</h1>
                     <br>
                     <h2>Filters</h2>
    """)

    mode_dropdown.js_on_change('value', mov_dropdown_callback)
    var_dropdown.js_on_change('value', mov_dropdown_callback)
    season_dropdown.js_on_change('value', mov_dropdown_callback)
    method_dropdown.js_on_change('value', mov_dropdown_callback)

    layout = column(title_text, row(mode_dropdown, var_dropdown, season_dropdown, method_dropdown), dtable)
    return layout

def create_enso_df(all_enso_path):

    data = {}

    for this_path, this_dir, files in os.walk(all_enso_path):
        for file in files:
            if file.endswith(('png')):
                parts = file.split('_')
                # e3sm_historical_ENSO_perf_v3-LR_0051_BiasPrLatRmse_diagnostic_divedown01.png
                if len(parts) >= 8:
                    collection = parts[2] + '_' + parts[3]
                    metric = parts[6]
                    model = parts[4]
                    plot = parts[8].split('.')[0]
                else:
                    collection, metric, model = None, None, None
                
                file_path = os.path.join(all_enso_path, file)

                key = (collection, metric, model)

                if key not in data:
                    data[key] = {
                        'Collection': collection,
                        'Metric' : metric,
                        'Model' : model
                    }
                
                data[key][plot] = file_path

    df = pd.DataFrame.from_dict(data, orient='index')
    df.reset_index(drop=True, inplace=True)

    return df

def create_enso_layout(all_enso_path):
    if all_enso_path:
        user_df = create_enso_df(all_enso_path=all_enso_path).sort_values(['Collection', 'Metric'])
    else:
        user_df = pd.DataFrame()
    
    df = user_df

    source = ColumnDataSource(data=dict(df))
    filtered_data = df
    filtered_source = ColumnDataSource(data=filtered_data.to_dict(orient='list'))

    image_templates={}
    image_formatters={}
    plots = ['divedown01', 'divedown02', 'divedown03', 'divedown04', 'divedown05']
    #for p in plots:
    #    image_templates[f"{p}_template"] = f"""
    #    <div style="position: relative;">
    #        <a href="<%= {p} %>" target="_blank">{p}</a>
    #    </div>
    #    """
    #    image_formatters[f"{p}_formatter"] = HTMLTemplateFormatter(template=image_templates[f"{p}_template"])

    #no_image_template = """
    #<span style="color: gray;">No image available</span>
    #"""
    #valid_link_template = """
    #<a href="<%= value %>" target="_blank">View Plot</a>
    #"""
    
    #no_image_formatter = HTMLTemplateFormatter(template=no_image_template)
    #valid_link_formatter = HTMLTemplateFormatter(template=valid_link_template)

    # Assign the correct formatter for each column   
    #for p in plots:
        # Replace NaN values with 'No image available'
    #    df[p] = df[p].fillna("No plot available")
        
        # Apply formatter based on each cell's value
        #image_formatters[f'{p}_formatter'] = image_formatters[f"{p}_formatter"] = valid_link_formatter if df[p].iloc[0] != "No plot available" else no_image_formatter
    
    image_or_text_formatter = HTMLTemplateFormatter(template="""
        <% if (value && value !== "No plot available") { %>
            <span style="font-size:16px;">
            <a href="<%= value %>" target="_blank">View plot</a>
            </span>
        <% } else { %>
            <span style="color: gray; font-size:16px;">--</span>
        <% } %>
    """)
    text_only_formatter = HTMLTemplateFormatter(template='<span style="font-size:16px;"> <%= value %> </span>')

    columns = [
        TableColumn(field="Collection", title="Collection", formatter=text_only_formatter),
        TableColumn(field="Metric", title="Metric", formatter=text_only_formatter),
        TableColumn(field="Model", title="Model", formatter=text_only_formatter),
        TableColumn(field="divedown01", title="diagnostic01", formatter=image_or_text_formatter),
        TableColumn(field="divedown02", title="diagnostic02", formatter=image_or_text_formatter),
        TableColumn(field="divedown03", title="diagnostic03", formatter=image_or_text_formatter),
        TableColumn(field="divedown04", title="diagnostic04", formatter=image_or_text_formatter),
        TableColumn(field="divedown05", title="diagnostic05", formatter=image_or_text_formatter)
    ]

    dtable = DataTable(source=filtered_source, columns=columns, width=1600, height=1200, row_height=30)

    # Page text
    title = Div(text="""
                <br>
                <h1>PMP ENSO Diagnostics and Metrics</h1>
                <br>
                <h2>Filters</h2>
                """)
    # Filters
    collection_dropdown = MultiChoice(
        options=list(df['Collection'].unique()),
        title="Select Collection",
        value=[],
        css_classes=["multichoice"]
    )

    metric_dropdown = MultiChoice(
        options=list(df['Metric'].unique()), 
        title="Select Metric",
        value=[]
    )

    model_dropdown = MultiChoice(
        options=list(df['Model'].unique()), 
        title="Select Model",
        value=[]
    )
    css = """
    <style>
    /* Change the font size of the MultiChoice title */
    multichoice .bk-input-group label {
        font-size: 16px !important;
    }
    </style>
    """
    css_div = Div(text=css)
    # JS Callback
    enso_callback = CustomJS(
        args=dict(source=source, filtered_source=filtered_source, collection_dropdown=collection_dropdown, metric_dropdown=metric_dropdown, model_dropdown=model_dropdown),
        code="""
        const original_data = source.data;
        const filtered_data = { Collection: [], Metric: [], Model: [], divedown01: [], divedown02: [], divedown03: [], divedown04: [], divedown05: []}
        
        const selected_collections = collection_dropdown.value;
        const selected_metrics = metric_dropdown.value;
        const selected_models = model_dropdown.value;

        for (let i = 0; i < original_data.Model.length; i++) {
            const in_collection = selected_collections.length === 0 || selected_collections.includes(original_data.Collection[i]);
            const in_metric = selected_metrics.length === 0 || selected_metrics.includes(original_data.Metric[i]);
            const in_model = selected_models.length === 0 || selected_models.includes(original_data.Model[i]);
        
            if (in_collection && in_metric && in_model) {
                filtered_data.Collection.push(original_data.Collection[i]);
                filtered_data.Metric.push(original_data.Metric[i]);
                filtered_data.Model.push(original_data.Model[i]);
                filtered_data.divedown01.push(original_data.divedown01[i]);
                filtered_data.divedown02.push(original_data.divedown02[i]);
                filtered_data.divedown03.push(original_data.divedown03[i]);
                filtered_data.divedown04.push(original_data.divedown04[i]);
                filtered_data.divedown05.push(original_data.divedown05[i]);
            }
        }

        filtered_source.data = Object.assign({}, filtered_data);
        filtered_source.change.emit();
        """
    )

    collection_dropdown.js_on_change('value', enso_callback)   
    metric_dropdown.js_on_change('value', enso_callback)
    model_dropdown.js_on_change('value', enso_callback)

    layout = column(css_div, title, row(collection_dropdown, metric_dropdown, model_dropdown), dtable)
    return layout       