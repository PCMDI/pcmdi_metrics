# pages/page2.py
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import os
import re

def create_table(dir_path):
    # Create table from directory path
    data = []
    pattern = r"^[^_]+_([^_]+)_.*\.png$" #regex pattern to extract model name between first and second underscores
    var_folders = [f.name for f in os.scandir(dir_path) if f.is_dir()]
    seasons = {
        "AC": "_AC_",
        "DJF": "_DJF_",
        "JJA": "_JJA_",
        "MAM": "_MAM_",
        "SON": "_SON_"
    }

    for var_folder in var_folders:
        var_folder_path = os.path.join(dir_path, var_folder)
        image_data = {} #dictionary for images stored by model

        for file in os.scandir(var_folder_path):
            if file.is_file():
                match = re.match(pattern, file.name)
                if match:
                    model = match.group(1)

                    if model not in image_data: #initialize model entry if it doesn't exist
                        image_data[model] = {"Variable": var_folder, "AC": None, "DJF": None, "JJA": None, "MAM": None, "SON": None,}
                    
                    for image_type, season in seasons.items():
                        if season in file.name:
                            image_data[model][image_type] = f"/images/{var_folder}/{file.name}"
                            break #to stop checking other key strings for this file
        
        # Add model images to data
        for model, images in image_data.items():
            data.append({
                "Model": model,
                "Variable": images["Variable"],
                "AC": images["AC"],
                "DJF": images["DJF"],
                "JJA": images["JJA"],
                "MAM": images["MAM"],
                "SON": images["SON"]
            })

    df = pd.DataFrame(data)
    return df

def layout(dir_path):
    df = create_table(dir_path)
    df = df[['Model', 'Variable', 'AC', 'DJF', 'JJA', 'MAM', 'SON']].sort_values('Model')
    for col in ['AC', 'DJF', 'JJA', 'MAM', 'SON']:
        df[col] = df[col].apply(lambda x: f"[{col}]({x})" if x else None)
 
    return html.Div([
        html.H1('Mean Climate Results Page'),
        html.A('Return', href='/main'),
        html.Br(), html.Br(),
        dcc.Dropdown(
            id='model-dropdown',
            options=[{'label': model, 'value': model} for model in df['Model'].unique()],
            placeholder="Filter by model name",
            clearable=True
        ),
        dcc.Dropdown(
            id='var-dropdown',
            options=[{'label': variable, 'value': variable} for variable in df['Variable'].unique()],
            placeholder="Filter by variable",
            clearable=True
        ),
        html.Div(id='mean-clim-results'),
        html.Br(), html.Br(),
        dash_table.DataTable(
            id='vars-table',
            columns=[{"name":col, "id":col, "presentation": "markdown"} for col in df.columns],
            data=df.to_dict('records'),
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={'fontWeight': 'bold'},
            sort_action="native"
        )
    ])

def callbacks(app, dir_path):
    df = create_table(dir_path)
    df = df[['Model', 'Variable', 'AC', 'DJF', 'JJA', 'MAM', 'SON']].sort_values('Model')
    for col in ['AC', 'DJF', 'JJA', 'MAM', 'SON']:
        df[col] = df[col].apply(lambda x: f"[{col}]({x})" if x else None)
    
    @app.callback(
        Output('vars-table', 'data'),
        [Input('model-dropdown', 'value'),
        Input('var-dropdown', 'value')]
    )
    def update_table(selected_model, selected_var):
        filtered_df = df.copy()
        if selected_model:
            filtered_df = filtered_df[filtered_df['Model']==selected_model]
        else:
            filtered_df = filtered_df
    
        if selected_var:
            filtered_df = filtered_df[filtered_df['Variable']==selected_var]
        else:
            filtered_df = filtered_df

        return filtered_df.to_dict("records")
