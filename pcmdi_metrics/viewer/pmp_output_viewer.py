# - Generate an html file of compiled PMP results using Bokeh.
# - Author: Kristin Chang (2024.12)
# - Last Update: 2024.12

import os
from typing import Optional, Dict, Union

from bokeh.models import ColumnDataSource, DataTable, TableColumn, MultiChoice, CustomJS, HTMLTemplateFormatter
from bokeh.layouts import column
from bokeh.io import output_file, save
import pandas as pd
import glob
import json

from pcmdi_metrics.graphics import download_archived_results
from pcmdi_metrics.graphics import Metrics

def view_pmp_output(
        dir_path: Optional[str] = None,
        season_map: Optional[Dict[str, Dict[str, Union[int, float, str]]]] = None,
        compare_cmip6: bool = False
):
    """
    Generates an html file of compiled PMP results using Bokeh. 

    Parameters
    ----------
    dir_path (str, optional): 
    season_map (dict, option): 
    compare_cmip6 (bool): 
    summaries (list): A list of options specifying which output results to include.
        Valid options include:
        - 'mean_climate' 
    """
    
    mean_clim_dive_down(dir_path=dir_path, season_map=season_map, compare_cmip6=compare_cmip6)
        
    home_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PMP Output Viewer PROTOTYPE</title>
    </head>
    <body>
        <h1>Welcome to the POV PROTOTYPE page</h1>
        <p>Goal: Generate a PMP output viewer that offers a HTML page showing PMP output image files in an organized way.<p>
        <br><br><br>
        <h3>Mean Climate:</h3>
        <a href="./mean_clim_results.html" target="_blank">Dive Down Plots</a><br>
    </body>
    </html>
    """
    with open("pmp_output_viewer.html", "w") as pov_file:
        pov_file.write(home_content)

    cwd = os.getcwd()
    return print(f"POV created in {cwd}")

def mean_clim_dive_down(dir_path, season_map=None, compare_cmip6=False):
    
    def create_layout():
    
        def add_var_long_name(df):
            with open('./CMIP6_Amon.json', 'r') as file:
                cmor_table = json.load(file)

            var_to_long_name = {
                var: details.get('long_name', 'Unknown')
                for var, details in cmor_table.get('variable_entry', {}).items()
            }

            def extract_base_var(var_name):
                return var_name.split('-')[0]

            df['Description'] = df['Variable'].apply(lambda var: var_to_long_name.get(extract_base_var(var), 'NaN'))
            return df
        if dir_path:
            def create_user_df(dir_path, season_map=None):
                data = {}
                season_map = season_map or {} # Default to empty dict if none

                for var_folder, _, files in os.walk(dir_path):
                    # extract variable name from subdirectory
                    variable = os.path.basename(var_folder)

                    for file in files:
                        if file.endswith(('.png')):
                            # extract file components based on underscores
                            parts = file.split('_')
                            if len(parts) >= 8:
                                model = parts[1]
                                region = parts[5]
                                season = parts[6]
                                mip = 'cmip6' # FIX LATER

                                # rename season if mapping provided
                                season = season_map.get(season, season)
                            else:
                                model, region, season = None, None, None
                            
                            # construct image file path
                            file_path = os.path.join(dir_path, var_folder, file)

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
    
        if compare_cmip6:
            season_map = {'AC':'ANN'}
            if dir_path:
                user_df = create_user_df(dir_path=dir_path, season_map=season_map).sort_values(['MIP', 'Model', 'Variable', 'Region'])
            else:
                user_df = pd.DataFrame()
            def create_cmip6_df():
                # download cmip6 data using pmp
                cmip6_dir = './pov_cmip6_mean_clim_json_files'
                os.makedirs(cmip6_dir, exist_ok=True)
                #try:
                #    os.mkdir(cmip6_dir)
                #except FileExistsError:
                #    raise FileExistsError(f"Error: The directory '{cmip6_dir}' already exists!")
                
                vars = ['pr', 'prw', 'psl', 'rlds', 'rltcre', 'rlus', 'rlut', 'rlutcs', 'rsds', 'rsdscs', 'rsdt', 'rstcre', 'rsut', 'rsutcs', 'sfcWind', 
                'ta-200', 'ta-850', 'tas', 'tauu', 'ts', 'ua-200', 'ua-850', 'va-200', 'va-850', 'zg-500']
                mip = "cmip6"
                exp = "historical"
                data_version = "v20230823"
                for var in vars:
                    path = "metrics_results/mean_climate/"+mip+"/"+exp+"/"+data_version+"/"+var+"."+mip+"."+exp+".regrid2.2p5x2p5."+data_version+".json"
                    download_archived_results(path, cmip6_dir)

                json_list = sorted(glob.glob(os.path.join(cmip6_dir, '*.cmip6.' + exp + '*' + data_version + '.json')))
                library_cmip6 = Metrics(json_list, mip="cmip6")
                
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
        
            cmip6_df = create_cmip6_df().sort_values(['MIP', 'Model', 'Variable', 'Region'])
            cmip6_df = add_var_long_name(cmip6_df)
            df = pd.concat([user_df, cmip6_df])
        else:
            season_map = {'AC':'ANN'}
            user_df = create_user_df(dir_path, season_map=season_map).sort_values(['MIP', 'Model', 'Variable', 'Region'])
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
            <a href="<%= {s} %>" target="_blank" style="position: relative;">
                {s}
            </a>
            """
            
            image_formatters[f"{s}_formatter"] = HTMLTemplateFormatter(template=image_templates[f"{s}_template"])

        # Table setup
        columns = [
            TableColumn(field="MIP", title="MIP"),
            TableColumn(field="Model", title="Model"),
            TableColumn(field="Variable", title="Variable"),
            TableColumn(field="Description", title="Description"),
            TableColumn(field="Region", title="Region"),
            TableColumn(field="ANN", title="ANN", formatter=image_formatters["ANN_formatter"]),
            TableColumn(field="DJF", title="DJF", formatter=image_formatters["DJF_formatter"]),
            TableColumn(field="JJA", title="JJA", formatter=image_formatters["JJA_formatter"]),
            TableColumn(field="MAM", title="MAM", formatter=image_formatters["MAM_formatter"]),
            TableColumn(field="SON", title="SON", formatter=image_formatters["SON_formatter"])
        ]

        dtable = DataTable(source=filtered_source, columns=columns, width=1450, height=650)

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

        mip_dropdown.js_on_change('value', dropdown_callback)
        model_dropdown.js_on_change('value', dropdown_callback)
        var_dropdown.js_on_change('value', dropdown_callback)
        region_dropdown.js_on_change('value', dropdown_callback)

        return column(mip_dropdown, model_dropdown, var_dropdown, region_dropdown, dtable)
    
    layout = create_layout()

    output_file("./mean_clim_results.html")
    return save(layout)