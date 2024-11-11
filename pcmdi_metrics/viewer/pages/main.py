# pages/page1.py
from dash import html

def layout():
    return html.Div([
        html.H1('PMP Output Viewer'),
        html.P(['This is a work in progress ', html.B('PROTOTYPE'), ' of the PMP output viewer that offers an HTML page showing PMP output image files in an organized way.']),
        html.A('Mean Climate', href='/mean_clim_results')
    ])
