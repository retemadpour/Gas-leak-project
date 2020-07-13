import dash
import dash_core_components as dcc
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

import os

from itertools import combinations
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn import manifold
from scipy.stats import pearsonr, spearmanr
import numpy as np
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, meta_tags=[
    {"content": "width=device-width, initial-scale=1.0"}
], external_stylesheets=external_stylesheets)


mapbox_access_token = 'pk.eyJ1IjoibWlzaGtpY2UiLCJhIjoiY2s5MG94bWRoMDQxdjNmcHI1aWI1YnFkYyJ9.eFsHqEMYY7qxa0Pb9USCtQ'
mapbox_style = "mapbox://styles/mishkice/ckbjhq6w50hlc1io4cnqg7svc"

# Load data
dir_path = os.path.dirname(os.path.realpath(__file__))
df = pd.read_csv(
    dir_path + '\data\processed\important_(used_in_app)\Merged_asc_fdny_data.csv')
df = df.dropna()
centers_df = pd.read_csv(
    dir_path + '\data\processed\important_(used_in_app)\geoid_with_centers.csv')

# bins
BINS = [
    "0-0.0015",
    "0.00151-0.003",
    "0.0031-0.0045",
    "0.00451-0.006",
    "0.0061-0.0075",
    "0.00751-0.009",
    "0.0091-10"
]

# colors
DEFAULT_COLORSCALE = [
    "#eff3ff",
    "#c6dbef",
    "#9ecae1",
    "#6baed6",
    "#4292c6",
    "#2171b5",
    "#084594"
]

DEFAULT_OPACITY = 0.8


colors = {
    'background': '#F8F8F8',
    'text': '#000000',
    'text2': '#000000',
    'border': '#000000',
    'chart': ['#27496d', '#00909e', '#4d4c7d']
}

# function to assign colors to markers by boroughs


'''def find_colorscale_by_boro(df):
    color_by_boro = ['#6a2c70' if row['boro'] == 'manhattan' else '#b83b5e' if row['boro'] == 'brooklyn' else '#f08a5d' if row['boro'] ==
                     'queens' else '#f9ed69' if row['boro'] == 'staten island' else '#3ec1d3' for index, row in df.iterrows()]
    return color_by_boro'''
colorscale_by_boro = ['#e41a1c',
                      '#377eb8',
                      '#4daf4a',
                      '#984ea3',
                      '#ff7f00']


# page layout
app.layout = html.Div(
    html.Div([

        # row with the header
        html.Div([
            html.H1(
                children='NYC Gas Leaks Information',
                style={
                    'textAlign': 'center',
                    'color': colors['text'],
                    'paddingTop':'1%',
                    'paddingBottom': '3%'
                })
        ], className='row'),

        # row 1 with the dropdowns
        html.Div([
            # dropdown to choose neighborhoods
            html.Div([
                dcc.Dropdown(
                    id='dropdownNta',
                    options=[
                        {
                            'label': i, 'value': i
                        } for i in centers_df['nta'].unique()
                    ],
                    multi=True,
                    placeholder='Choose neighborhoods')
            ],
                className='six columns',
                style={'display': 'inline-block'}),

            # dropdown to choose attributes
            html.Div([
                dcc.Dropdown(
                    id="dropdownAttr",
                    options=[
                        {
                            'label': i, 'value': i
                        } for i in df.columns[3:] if (i != 'median_houshold_income') & (i != 'gas_leaks_per_person')
                    ],
                    value=['avg_houshold_size',
                           'median_age', 'lonely_housholder_over65%'],
                    multi=True,
                    placeholder="Select attributes",
                    style={'display': 'inline-block', 'width': '100%'},
                )
            ],
                className='six columns',
                style={'display': 'inline-block'}),

        ],
            className='row'),

        html.Div([

            # range slider to choose year
            html.Div([
                dcc.Slider(
                    id="timeline",
                    min=2013,
                    max=2018,
                    step=1,
                    marks={2013: '2013', 2014: '2014', 2015: '2015',
                           2016: '2016', 2017: '2017', 2018: '2018'},
                    value=2018,
                    included=False
                )
            ],
                className='six columns',
                style={'float': 'left'}
            ),

            # dropdown to choose type of graph
            html.Div([
                dcc.Dropdown(
                    id="dropdownGraph",
                    options=[
                        {
                            "label": "Scatter matrix (pairwise comparison)",
                            "value": "scatter",
                        },
                        {
                            "label": "PCA",
                            "value": "pca",
                        },
                        {
                            "label": "ISOMAP",
                            "value": "isomap",
                        }
                    ],
                    value='scatter',
                    multi=False,
                    placeholder="Select type of graph",
                    style={'width': '100%'},
                )
            ],
                className='six columns',
                style={'float': 'right'}
            )

        ],
            className='row'),


        # row with a map and a matrix
        html.Div([
            # map
            html.Div([
                dcc.Graph(
                    id='mapGraph',
                    figure=dict(

                        layout=dict(
                            mapbox=dict(
                                layers=[],
                                accesstoken=mapbox_access_token,
                                style=mapbox_style,
                                center=dict(
                                    lat=40.7342,
                                    lon=-73.91251
                                ),
                                pitch=0,
                                zoom=10,
                            ),
                            autosize=False,
                        ),
                    ),
                )
            ],
                className='six columns',
                style={'display': 'inline-block'}),

            # matrix
            html.Div([
                dcc.Graph(
                    id='scatter_matrix'
                )
            ],
                className='six columns',
                style={'display': 'inline-block'})
        ],
            className='row'),

        # row with parallel coordinates
        html.Div([
            dcc.Graph(
                id='para_coor'
            )
        ],
            className='row'),

    ],
        style={'backgroundColor': colors['background']})
)


# callbacks

######################################################################################################################
# timeline callback
######################################################################################################################
'''
@ app.callback(
    Output("data_frame", "data"),
    [Input("timeline", "value")],
)
def choose_years(choice_years):

    df = df[(df.incident_date_time.str[6:10] >= choice_years[0]) &
            (df.incident_date_time.str[6:10] <= choice_years[1])]
    return df'''

######################################################################################################################
# map callback
######################################################################################################################


@ app.callback(
    Output("mapGraph", "figure"),
    [Input("timeline", "value"),
     Input("dropdownNta", "value")],
    [State("mapGraph", "figure")],
)
def display_map(year, choiceMap, figure):

    df_selected = df[df.incident_year == year]

    df_selected = df_selected.merge(centers_df, on='geoid')
    df_selected['hover'] = df_selected['hover']+'<br>#Gas leaks per person: ' + \
        df_selected['gas_leaks_per_person'].round(6).astype(str)

    annotations = [
        dict(
            showarrow=False,
            align="right",
            text="gas leaks per person",
            font=dict(color="#000000"),
            bgcolor=colors['background'],
            x=0.95,
            y=0.95,
        )
    ]

    bins = BINS
    colorscale = DEFAULT_COLORSCALE
    latitude = df_selected["centerLat"]
    longitude = df_selected["centerLong"]
    hover_text = df_selected["hover"]
    base = "https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/geolayers/"

    cm = dict(zip(bins, colorscale))
    data = [
        dict(
            lat=latitude,
            lon=longitude,
            text=hover_text,
            type="scattermapbox",
            hoverinfo="text",
            marker=dict(size=5, color="black", opacity=0),
        )
    ]

    for i, bin in enumerate(reversed(bins)):
        color = cm[bin]
        annotations.append(
            dict(
                arrowcolor=color,
                text=bin,
                x=0.95,
                y=0.85 - (i / 20),
                ax=-60,
                ay=0,
                arrowwidth=5,
                arrowhead=0,
                bgcolor="#F8F8F8",
                font=dict(color='#000000'),
            )
        )

    if "layout" in figure:
        lat = figure["layout"]["mapbox"]["center"]["lat"]
        lon = figure["layout"]["mapbox"]["center"]["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]
    else:
        lat = (40.7342,)
        lon = (-73.91251,)
        zoom = 10

    layout = dict(
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            center=dict(lat=lat, lon=lon),
            zoom=zoom,
        ),
        height=900,
        transition={'duration': 500},
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        annotations=annotations,
        dragmode="lasso"
    )

    for bin in bins:

        geo_layer = dict(
            sourcetype="geojson",
            source=base + str(year)+'_' + bin + ".geojson",
            type="fill",

            color=cm[bin],
            opacity=DEFAULT_OPACITY,
            # CHANGE THIS
            fill=dict(outlinecolor="#afafaf"),
        )
        layout["mapbox"]["layers"].append(geo_layer)

    fig = dict(data=data, layout=layout)

    return fig

######################################################################################################################
# callbacks to reset dropdown/map selection
######################################################################################################################


@app.callback(
    Output('dropdownNta', 'value'),
    [
        Input('mapGraph', 'selectedData')
    ])
def reset_dropdown_selected(selectedAreaMap):
    if selectedAreaMap is not None:
        return None


'''@app.callback(
    Output('mapGraph', 'selectedData'),
    [
        Input('dropdownNta', 'value')
    ])
def reset_map_selected(selectedDropdown):
    if selectedDropdown is not None:
        return None
'''
######################################################################################################################
# scattermatrix callback
######################################################################################################################


@app.callback(
    [
        Output('scatter_matrix', 'figure'),
        Output('para_coor', 'figure')
    ],
    [Input("timeline", "value"),
        Input('mapGraph', 'selectedData'),
        Input('dropdownNta', 'value'),
        Input('dropdownAttr', 'value')
     ])
def display_selected_data(year, selectedAreaMap, selectedAreaDropdown, selectedAttr):

    num_of_attributes = len(selectedAttr)
    df_selected = df[(df.incident_year == year)]

    df_selected = df_selected.merge(centers_df, on='geoid')
    title_part = ' census tracts'
    key = 'geoid'

    font_ann = dict(
        size=10,
        color=colors['text']
    )

    if selectedAreaDropdown is not None:

        df_selected = df_selected[df_selected['nta'].isin(
            selectedAreaDropdown)]
    elif selectedAreaMap is not None:
        points = selectedAreaMap["points"]
        area_names = [str(point["text"].split("<br>")[2])
                      for point in points]
        df_selected = df_selected[df_selected[key].isin(area_names)]

    arr = [str(r) for r in df.columns[3:] if r != 'median_houshold_income']
    para = px.parallel_coordinates(df_selected, color="geoid",
                                   dimensions=arr,
                                   color_continuous_scale=px.colors.diverging.Tealrose,
                                   color_continuous_midpoint=2
                                   )

    # scatterplots
    fig = make_subplots(rows=len(selectedAttr), cols=1, subplot_titles=[
        'Gas Leaks per Person VS ' + attr.replace('_', ' ').capitalize() for attr in selectedAttr
    ])

    show_legend = True
    for i in range(len(selectedAttr)):

        for ind, b in enumerate(df_selected['boro'].unique()):
            if i > 0:
                show_legend = False
            fig.add_trace(
                go.Scatter(x=df_selected[df_selected['boro'] == b]['gas_leaks_per_person'],
                           y=df_selected[df_selected['boro']
                                         == b][selectedAttr[i]],
                           mode='markers',
                           marker_color=colorscale_by_boro[ind],
                           showlegend=show_legend,
                           name=b),

                row=i+1, col=1
            )

    fig.update_traces(mode='markers', marker_line_width=0.5, marker_size=5)
    fig.update_layout(font=dict(color=colors['text2'], size=12),
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      height=900,
                      title_text="Comparison of Gas Leak#/person to Other Attributes")
    return fig, para


if __name__ == '__main__':
   # app.config['suppress_callback_exceptions'] = True
    app.run_server(debug=True)
