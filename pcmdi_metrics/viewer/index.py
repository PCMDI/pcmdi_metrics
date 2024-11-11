from dash import Dash, html, dcc, Input, Output
from app import app
import pages.main as page1
import pages.mean_clim_results as page2
import argparse
import os
from flask import send_from_directory

parser = argparse.ArgumentParser(description="Run multi-page Dash app with a specified directory path.")
parser.add_argument("dir_path", type=str, help="Path to the directory containing data")
args = parser.parse_args()
dir_path = args.dir_path

# Verify the directory exists
if not os.path.isdir(dir_path):
    print(f"Error: The directory '{dir_path}' does not exist.")
    exit(1)

# Define the static route to serve images
@app.server.route("/images/<path:filename>")
def serve_image(filename):
    # Use the directory_path as the base directory for the static route
    return send_from_directory(dir_path, filename)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == '/main':
        return page1.layout()
    elif pathname == '/mean_clim_results':
        return page2.layout(dir_path)
    else:
        return html.Div([
            html.H1('404 Not Found'),
            html.P('The page you are looking for does not exist.'),
            html.A('Go back to main', href='/main')
        ], style={'textAlign': 'center'})

# Register page-specific callbacks (if any)
#page1.callbacks(app, dir_path)
page2.callbacks(app, dir_path)

if __name__ == '__main__':
    app.run_server(debug=True)
