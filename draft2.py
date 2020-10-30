import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import re


import numpy as np
import pandas as pd


# prevent triggering of pandas chained assignment warning
pd.options.mode.chained_assignment = None

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, meta_tags=[
    {"content": "width=device-width, initial-scale=1.0"}
])


# mapbox access info
mapbox_access_token = 'pk.eyJ1IjoibWlzaGtpY2UiLCJhIjoiY2s5MG94bWRoMDQxdjNmcHI1aWI1YnFkYyJ9.eFsHqEMYY7qxa0Pb9USCtQ'
mapbox_style = "mapbox://styles/mishkice/ckbjhq6w50hlc1io4cnqg7svc"


# Load and prepare data:
#
# - read files with fdny and asc data (df), monthly data (months_df), and properties use data (property_use_df);
# - convert data to numeric type;
# - merge each of them with geo data (centers_df) to get coordinates of tract centers to use in map;

base = "https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/geolayers/"
base2 = "https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/ct_geolayers/"

df = pd.read_csv(
    'C:\\Users\\mskac\\machineLearning\\GasLeakConEd\\data\\processed\\important_(used_in_app)\\Merged_asc_fdny_data.csv')
#df.rename(columns={
#          'housholders_grandparents_responsible_for_grandchildren%': '%housh_grandp_resp_for_grandch'}, inplace=True)  # fixme
df = df.dropna()
#df = df.drop(['occupied_housing_units%'], axis=1)  # fixme
columns_original = df.columns
for column in columns_original:
    df[column] = pd.to_numeric(df[column])



centers_df = pd.read_csv(
    'https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/processed/important_(used_in_app)/geoid_with_centers.csv')

df = df.merge(centers_df, on='geoid')
df['hover'] = df['hover']+'<br>#Gas leaks per person: ' + \
    df['gas_leaks_per_person'].round(6).astype(str)+'<br>Avg. built year: ' + \
    df['avg_year_built'].round(5).astype(str)
df = df.drop(['Unnamed: 0_x','Unnamed: 0_y','polygon'], axis = 1)

months_df = pd.read_csv(
    'C:\\Users\\mskac\\machineLearning\\GasLeakConEd\\data\\processed\\important_(used_in_app)\\Merged_asc_fdny_data_months.csv')
months_centers_df = months_df.merge(centers_df, on='geoid')

nation_df = pd.read_csv('C:\\Users\\mskac\\machineLearning\\GasLeakConEd\\data\\processed\\important_(used_in_app)\\nationalities_data.csv')
nation_df_all = pd.read_csv('C:\\Users\\mskac\\machineLearning\\GasLeakConEd\\data\\processed\\important_(used_in_app)\\nationalities_data_all.csv')
for column in nation_df.columns:
    nation_df[column] = pd.to_numeric(nation_df[column])
    nation_df_all[column] = pd.to_numeric(nation_df_all[column])

df_all_years = pd.read_csv(
    'C:\\Users\\mskac\\machineLearning\\GasLeakConEd\\data\\processed\\important_(used_in_app)\\Merged_asc_fdny_data_all_years.csv')
df_all_years = df_all_years.dropna()
df_all_years = df_all_years.merge(centers_df, on='geoid')
df_all_years = df_all_years.drop(['Unnamed: 0_x','Unnamed: 0_y','polygon'], axis = 1)
df_all_years['hover'] = df_all_years['hover']+'<br>#Gas leaks per person: ' + \
    df_all_years['gas_leaks_per_person'].round(6).astype(str)+'<br>Avg. built year: ' + \
    df_all_years['avg_year_built'].round(5).astype(str)



# dictionary where keys are ntas and values are lists of geoids in each of the ntas
nta_geoid_dict = {}
for index, row in centers_df.iterrows():
    if row['nta'] not in nta_geoid_dict:
        nta_geoid_dict[row['nta']] = [row['geoid']]
    else:
        nta_geoid_dict[row['nta']].append(row['geoid'])


# bins for choropleth map
BINS = [
    "0-0.0015",
    "0.00151-0.003",
    "0.0031-0.0045",
    "0.00451-0.006",
    "0.0061-0.0075",
    "0.00751-0.009",
    "0.0091-10",
    "park_cemetery"
]
BINS_ABS = [
    "0-10",
    "11-20",
    "21-30",
    "31-40",
    "41-50",
    "51-70",
    "71-200",
    "park_cemetery"
]
# colors for choropleth map
DEFAULT_COLORSCALE = [
    "#eff3ff",
    "#c6dbef",
    "#9ecae1",
    "#6baed6",
    "#4292c6", 
    "#2171b5",
    "#084594",
    "#cbffcb"
]

# fixme
colors = {
    'background': '#F5F5F5',
    'background2': '#d3d3d3',
    'text': '#000000',
    'text2': '#000000',
    'border': '#000000',
    'chart': ['#27496d', '#00909e', '#4d4c7d']
}

colorscale_by_boro = ['#e41a1c',
                      '#377eb8',
                      '#4daf4a',
                      '#984ea3',
                      '#ff7f00']
##############################################################################################
# page layout
##############################################################################################
app.layout = html.Div(
    html.Div([

        # Hidden divs inside the app that stores the selected areas on the map and passes it into
        # the map callback so those areas are colored
        html.Div(id='selected_geoids', style={'display':'none'}),
        html.Div(id='selected_geoids_no_parcoord', style={'display':'none'}),
        html.Div(id='par_coord_range', style={'display': 'none'}),
        

        # row1 with the header
        html.Div([
            html.H1(
                children='NYC Gas Leaks Information',
                 className='eleven columns'),
            html.Button('Reset', id='reset_btn', n_clicks=0, style={'backgroundColor':'#f59999'}),

        ], style={
            'textAlign': 'center',
            'color': colors['text'],
            'paddingTop':'1%',
            'paddingBottom': '1%'
        }, className='row'),

        # row3 with the dropdowns
        html.Div([
            # row3: dropdown to choose neighborhoods
            html.Div([
                dcc.Dropdown(
                    id='dropdown_nta',
                    options=[
                        {'label': i, 'value': i} for i in np.append('all', centers_df['nta'].unique())
                    ],
                    multi=True,
                    placeholder='Choose neighborhoods')
            ],
                className='six columns',
                style={'display': 'inline-block'}),

            
            html.Div([
                dcc.RadioItems(
                    id = 'radio_btn',
                    options=[
                        {'label': 'Gas Leaks per Person', 'value': 'gas_leaks_per_person'},
                        {'label': 'Gas Leaks (abs.)', 'value': 'gas_leaks'}
                    ],
                    value='gas_leaks_per_person',
                    labelStyle={'display': 'inline-block', 'margin-left':'10px'}
                )  
            ],
                className='six columns',
                style={'display': 'inline-block', })
        ],
            className='row'),

        # row4 with a timeline slider, toggle and an input field for outliers
        html.Div([

            # row4: range slider to choose year
            html.Div([
                dcc.Slider(
                    id="timeline",
                    min=2013,
                    max=2019,
                    step=1,
                    marks={2013: '2013', 2014: '2014', 2015: '2015',
                           2016: '2016', 2017: '2017', 2018: '2018 (Jan-Jun)', 2019: 'all'},
                    value=2018,
                    included=False
                )
            ],
                className='six columns',
                style={'float': 'left'}
            ),

            # row4: toggle to hide outliers
            html.Div([
                daq.BooleanSwitch(
                    id='outliers_toggle',
                    on=True,
                    label='Hide outliers, set limit of gas_leaks/person to',
                    labelPosition='right',
                    color='#2a9df4'
                )
            ],
                className='three columns',
                style={'float': 'left'}
            ),

            # row4: input field for upper limit on gas_leaks_per_person
            html.Div([
                dcc.Input(
                    id='limit_outliers_field',
                    type='number',
                    value=0.04,
                    min=0,
                    max=1,
                    step=0.01
                )
            ],
                className='one column',
                style={'float': 'left', 'margin': 0, 'padding': 0}
            )
        ],
            className='row'),

        # row5 with a map, a timeline by month, and a Pearson correlation heatmap
        html.Div([
            # row5:  map
            html.Div([
                dcc.Graph(
                    id='map_graph',
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
                                maxzoom = 15,
                                minzoom = 5
                            ),
                            autosize=False,
                        ),
                    ),
                )
            ],
                className='six columns',
                style={'display': 'inline-block'}),

            html.Div([
                # row5: pearson coeff. heatmap
                html.Div([
                    dcc.Graph(
                        id='pearson_heatmap'
                    )], className='row'),

                    # row9 with the heatmap (nationalities)
                html.Div([
                    dcc.Graph(
                        id='pearson_heatmap_nation'
                    )
                ],
                className='row')

            ],
                className='six columns',
                style={'display': 'inline-block'})
        ],
            className='row'),

        # row6 with parallel coord
        html.Div([
            dcc.Graph(
                id='para_coor'
            )
        ],
            className='row'),

        # row5: timeline of gas leaks per person
                html.Div([
                    dcc.Graph(
                        id='timeline_by_month'
                    )], className='row'),

        # row7: dropdown to choose attributes
        html.Div([

            html.Label([
                    "Attributes for scatter plot: ",
                    dcc.Dropdown(
                        id="dropdown_attr",
                        options=[
                            {
                                'label': i.replace('_', ' ').capitalize(), 'value': i 
                            } for i in columns_original if i not in ['gas_leaks','gas_leaks_per_person','geoid', 'incident_year','Unnamed: 0']
                        ],
                        value=['lonely_housholder%', 'not_us_citizen%'],
                        multi=True,
                        placeholder="Select attributes",
                        style={'display': 'inline-block', 'width': '100%'}
                    )
                ],
                    className='six columns',
                    style={'display': 'inline-block'})
            ],
        className='row'),

        # row8 with the scatterplots
        html.Div([
            dcc.Graph(
                id='scatter_matrix'
            )
        ],
            className='row')
        
        
    ],
        style={'backgroundColor': colors['background']})
)

# takes a hex representation of a color (string) and returns an RGB (tuple)
def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = hex_color * 2
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


####################################################################################
# callbacks
####################################################################################


# if year is selected or a reset btn was pressed, reset dropdown
@app.callback(
    Output('dropdown_nta', 'value'),
    [
        Input('timeline', 'value'),
        Input('reset_btn', 'n_clicks')
    ]
)
def reset_dd(year, clicks):
    return None

# visibility of outliers limit 
@app.callback(
    Output('limit_outliers_field', 'style'),
    [
        Input('outliers_toggle', 'on')
    ])

def activate_input(is_on):
    if is_on:
        return {'display': 'block'}
    else:
        return {'display': 'none'}


# filter data by selected location:
# - inputs: map, dropdown, scatterplot, par.coordinates;
# - recognize which input triggered the callback;
# - filter by that input;
# - return list of selected geoids
@app.callback(
    Output('selected_geoids', 'children'),
    [
        Input('selected_geoids_no_parcoord', 'children'),
        Input('par_coord_range', 'children')
    ])

def selected_areas(selected_geoids, selected_pc):

    ctx = dash.callback_context
    if not ctx.triggered:
        return []
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'par_coord_range':
        return selected_pc
    else:
        return selected_geoids


@app.callback(
    Output('selected_geoids_no_parcoord', 'children'),
    [
        Input('map_graph', 'selectedData'),
        Input('dropdown_nta', 'value'),
        Input('scatter_matrix', 'selectedData')
    ])

def selected_areas(selected_map, selected_dd, selected_scatter):

    ctx = dash.callback_context
    if not ctx.triggered:
        return []
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'dropdown_nta':
        if (selected_dd and'all' in selected_dd) or not selected_dd:
            return []
        else:
            return df[df['nta'].isin(selected_dd)]['geoid'].to_list()

    if trigger_id == 'scatter_matrix':
        points = selected_scatter["points"]
        return np.unique([str(point["text"].split("<br>")[2]) for point in points])
    
    if trigger_id == 'map_graph':
        points = selected_map['points']
        return np.unique([str(point["text"].split("<br>")[2]) for point in points])

# retrieve selected lines (geoids) on the parallel coordinates graph
@app.callback(
    Output('par_coord_range', 'children'),
    [
        Input('para_coor', 'restyleData'),
        Input('para_coor', 'figure'),
        Input('selected_geoids_no_parcoord', 'children'),
        Input('timeline', 'value'),
        Input('outliers_toggle', 'on'),
        Input('limit_outliers_field', 'value')
    ]
)

def get_selected_parcoord(restyleData, figure, geoids, year, toggle, limit):
    ranges = []
    all_geoids = []

    if year != 2019:
        dff = df[df['incident_year']==year]
    else:
        dff = df_all_years
    
    if toggle:
        dff = dff[dff['gas_leaks_per_person'] < limit]

    if len(geoids)>0:
        dff = dff[dff['geoid'].isin(geoids)]

    dim = 0
    split = []
    if restyleData:
        for key, val in restyleData[0].items():
            split = re.split(r'\[|\]', key)
    

    if restyleData and len(split)>2:
        dim = int(split[1])
        label = figure['data'][0]['dimensions'][dim]['label']
        
        # list of lists
        if 'constraintrange' in figure['data'][0]['dimensions'][dim]:
            ranges = figure['data'][0]['dimensions'][dim]['constraintrange']
            all_geoids = []
            # select geoids with gas_leaks in the selected intervals
            if isinstance(ranges[0], list):
                for range in ranges:
                    selected_dff = dff[dff[label.replace(' ', '_')].between(
                        range[0], range[1], inclusive=True)]
                    geoids = selected_dff['geoid']
                    all_geoids.extend(geoids)
            else:
                selected_dff = dff[dff[label.replace(' ', '_')].between(
                    ranges[0], ranges[1], inclusive=True)]
                geoids = selected_dff['geoid']
                all_geoids.extend(geoids)

    return all_geoids

# update map depending on chosen year;
# red color areas selected on par.coord/scatterplot/dropdown/map
@app.callback(
    Output("map_graph", "figure"),
    [
        Input("timeline", "value"),
        Input('selected_geoids', 'children'),
        Input('radio_btn', 'value')],
    [
        State("map_graph", "figure")
    ]
)
def display_map(year, geoids_to_color,abs_rel, figure):

    if year != 2019:
        data_ = df[df['incident_year']==year]
    else:
        data_ = df_all_years

    text_ann = ''
    if abs_rel == 'gas_leaks':
        text_ann = 'gas leaks (abs)'
        bins = BINS_ABS
        base_temp = base+'abs/'
    else:
        text_ann = 'gas leaks per person'
        bins = BINS
        base_temp = base + 'rel/'

    annotations = [
        dict(
            showarrow=False,
            align="right",
            text=text_ann,
            font=dict(color="#000000"),
            bgcolor=colors['background'],
            x=0.95,
            y=0.95,
        )
    ]

    
    colorscale = DEFAULT_COLORSCALE
    latitude = data_["centerLat"]
    longitude = data_["centerLong"]
    hover_text = data_["hover"]

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
        maxzoom = 15,
        minzoom = 5
    else:
        lat = (40.7342,)
        lon = (-73.91251,)
        zoom = 10
        maxzoom = 15,
        minzoom = 5

    layout = dict(
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            center=dict(lat=lat, lon=lon),
            zoom=zoom,
            maxzoom = 15,
            minzoom = 5
        ),
        height=900,
        transition={'duration': 500},
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        annotations=annotations,
        dragmode="lasso"
    )

    for bin in bins:
        if year == 2019:
            year_str = 'all'
        else:
            year_str = str(year)
        geo_layer = dict(
            sourcetype="geojson",
            source=base_temp + year_str+'_' + bin + ".geojson",
            type="fill",

            color=cm[bin],
            opacity=0.8,
            # CHANGE THIS
            fill=dict(outlinecolor="#afafaf"),
        )
        layout["mapbox"]["layers"].append(geo_layer)

    for geoid in geoids_to_color:
        geo_layer = dict(
            sourcetype="geojson",
            source=base2 + str(geoid) + ".geojson",
            type="fill",

            color='#F74DFF',
            opacity=0.4,
            # CHANGE THIS
            fill=dict(outlinecolor="#afafaf"),
        )
        layout["mapbox"]["layers"].append(geo_layer)

    fig = dict(data=data, layout=layout)

    return fig

# update para_coord based on selected areas, outliers limit, and selected date
@app.callback(
        Output('para_coor', 'figure'),
    [
        Input("selected_geoids_no_parcoord", "children"),
        Input('timeline', 'value'),
        Input('outliers_toggle', 'on'),
        Input('limit_outliers_field', 'value')
    ])

def build_parallel_coord(filtered_geoids, year, toggle, limit):
    
    if year != 2019:
        filtered_data = df[df['incident_year']==year]
    else:
        filtered_data = df_all_years
    if toggle:
        filtered_data = filtered_data[filtered_data['gas_leaks_per_person'] < limit]

    if len(filtered_geoids)>0:
        filtered_data = filtered_data[filtered_data['geoid'].isin(filtered_geoids)]
    # array of attributes
    arr1 = [str(r) for r in columns_original if r not in ['gas_leaks','gas_leaks_per_person','geoid', 'incident_year','Unnamed: 0']]
    arr1 = sorted(arr1)
    arr = ['gas_leaks_per_person', 'gas_leaks']
    arr.extend(arr1)

    dim = [dict(range=[filtered_data[attr].min(), filtered_data[attr].max()],
                label=attr.replace('_', ' '), values=filtered_data[attr]) for attr in arr]
    
    fig = go.Figure(data=go.Parcoords(
        line=dict(
            color=filtered_data['gas_leaks_per_person'],
            colorscale=px.colors.sequential.tempo,
            showscale=True
            ), 
        meta=dict(colorbar=dict(title="gas leaks/person")),
        dimensions=dim,
        labelangle=10))

    fig.update_layout(
        height=500,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background2'],

    )
    return fig


# update scatterplot based on selected date, locations, and outliers
@app.callback(
    Output('scatter_matrix', 'figure'),
    [
        Input("selected_geoids", "children"),
        Input('dropdown_attr', 'value'),
        Input('timeline', 'value'),
        Input('outliers_toggle', 'on'),
        Input('limit_outliers_field', 'value'),
        Input('radio_btn', 'value')
    ])
def build_parallel_coord(filtered_geoids, selected_attr, year, toggle, limit, abs_rel):

    if year != 2019:
        filtered_data = df[df['incident_year']==year]
        year_title = str(year)
    else:
        filtered_data = df_all_years
        year_title = '2013-2018'
    
    if toggle:
        filtered_data = filtered_data[filtered_data['gas_leaks_per_person'] < limit]


    fig = make_subplots(rows=len(selected_attr), cols=1, subplot_titles=[
        abs_rel.replace('_',' ').capitalize() + ' VS ' + attr.replace('_', ' ').capitalize() for attr in selected_attr])

    if len(filtered_geoids)>0:
        filtered_data = filtered_data[filtered_data['geoid'].isin(filtered_geoids)]
    if abs_rel == 'gas_leaks_per_person':
        temp_title = "<b>Comparison of Gas Leak#/person to Other Attributes" + year_title
    else:
        temp_title = "<b>Comparison of Gas Leaks to Other Attributes" + year_title
    
    # show_legend = True
    for i in range(len(selected_attr)):

        for ind, b in enumerate(filtered_data['boro'].unique()):
            temp = filtered_data[filtered_data['boro'] == b]
            # if i > 0:
            #     show_legend = False
            fig.add_trace(
                go.Scatter(y=temp[abs_rel],
                           x=temp[selected_attr[i]],
                           mode='markers',
                           marker_color=f"rgba{(*hex_to_rgb(colorscale_by_boro[ind]), 0.6)}",
                           showlegend=True,
                           name=b,
                           text=temp['hover']),

                row=i+1, col=1
            )
            fig.update_xaxes(title_text=selected_attr[i], row=i+1, col=1)
            fig.update_yaxes(title_text=abs_rel.replace('_', ' '), row=i+1, col=1)

    fig.update_traces(mode='markers', marker_line_width=0.2, marker_size=3.5)
    fig.update_layout(font=dict(color=colors['text2'], size=12),
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      height=900,
                      dragmode='select',
                      title={
        'text': temp_title + '</b>',
        'x': 0.5,
        'xanchor': 'center'})

    return fig


# update pearson corr. coeff. heatmap based on selected location and outliers
@app.callback(
    [
        Output('pearson_heatmap', 'figure'),
        Output('pearson_heatmap_nation', 'figure')
    ],
    [
        Input('selected_geoids', 'children'),
        Input('outliers_toggle', 'on'),
        Input('limit_outliers_field', 'value'),
        Input('radio_btn', 'value')
    ])
def display_selected_data(selected_geoids, hideOutliers, limit, abs_rel):

    df_selected = df
    df_selected_all = df_all_years
    df_nation = nation_df
    df_nation_all = nation_df_all

    if hideOutliers:
        df_selected = df_selected[df_selected['gas_leaks_per_person'] < limit]
        df_selected_all = df_selected_all[df_selected_all['gas_leaks_per_person'] < limit]
        df_nation = df_nation[df_nation['gas_leaks_per_person'] < limit]
        df_nation_all = df_nation_all[df_nation_all['gas_leaks_per_person']< limit]
        

    df_selected = df_selected[df_selected['nta'].str[:6] != 'park-c']
    df_selected_all = df_selected_all[df_selected_all['nta'].str[:6] != 'park-c']

    if len(selected_geoids)>0:
        df_selected = df_selected[df_selected['geoid'].isin(selected_geoids)]
        df_selected_all = df_selected_all[df_selected_all['geoid'].isin(selected_geoids)]
        df_nation = df_nation[df_nation['geoid'].isin(selected_geoids)]
        df_nation_all = df_nation_all[df_nation_all['geoid'].isin(selected_geoids)]

    if abs_rel == 'gas_leaks':
        skip = 'gas_leaks_per_person'
    else:
        skip = 'gas_leaks'
    
    df_pearson = df_selected.drop(
        ['geoid',  'centerLong', 'centerLat', 'total_housing_units',skip, 'area','boro', 'nta', 'hover'], axis=1)
    df_pearson_all = df_selected_all.drop(
        ['geoid', 'centerLong', 'centerLat','total_housing_units', skip, 'area','boro', 'nta', 'hover'], axis=1)
    
    
    df_nation['gas_leaks_per_person'] = df_nation['gas_leaks']/df_nation['total_population']
    df_nation_all['gas_leaks_per_person'] = df_nation_all['gas_leaks']/df_nation_all['total_population']
    


    df_pearson_nation = df_nation.drop(
        ['geoid', 'Unnamed: 0', skip], axis=1)
    df_pearson_nation_all = df_nation_all.drop(['geoid', 'Unnamed: 0', skip], axis=1)

    for column in df_pearson_nation.columns[:-3]:
        df_pearson_nation[column] = df_pearson_nation[column]/df_pearson_nation['total_population']
    for column in df_pearson_nation_all.columns[:-3]:
        df_pearson_nation_all[column] = df_pearson_nation_all[column]/df_pearson_nation_all['total_population']
    

    df_pearson_nation = df_pearson_nation.drop(['total_population'], axis=1)
    df_pearson_nation_all = df_pearson_nation_all.drop(['total_population'], axis=1)

    columns_nation = [column for column in df_pearson_nation.columns if column not in [ 'gas_leaks','gas_leaks_per_person']]
    columns_nation.insert(0, abs_rel)
    df_pearson_nation = df_pearson_nation[columns_nation]
    columns_nation.remove('incident_year')
    df_pearson_nation_all = df_pearson_nation_all[columns_nation]

    pearsoncorr_nation_all = df_pearson_nation_all.corr(method='pearson')
    pearson_nation_gas_leaks_all = pearsoncorr_nation_all[abs_rel]
    attributes_nation = [col for col in pearsoncorr_nation_all.columns if (col != 'gas_leaks_per_person' and col!= 'gas_leaks')]
    matrix_nation = [[] for _ in range(len(attributes_nation))]
    years = [year for year in range(2013, 2019)]

    for year in years:
        df_pearson_nation_year = df_pearson_nation[df_pearson_nation['incident_year'] == year]
        df_pearson_nation_year = df_pearson_nation_year.drop(columns={'incident_year'})
        pearsoncorr_nation = df_pearson_nation_year.corr(method='pearson')
        pearson_nation_gas_leaks = pearsoncorr_nation[abs_rel]
        for i in range(len(attributes_nation)):
            matrix_nation[i].append(pearson_nation_gas_leaks[i+1])
    for i in range(len(attributes_nation)):
        matrix_nation[i].append(pearson_nation_gas_leaks_all[i+1])

    years.append('all')

    pearson_nation_df = pd.DataFrame(matrix_nation, columns=years, index=attributes_nation)
    sorted_pearson_nation_df = pearson_nation_df.sort_values(by=['all'], ascending = 'False')

    #### working, but confusing, has to be fix
    columns = [column for column in df_pearson.columns if column not in [ 'gas_leaks','gas_leaks_per_person', 'incident_year']]
    columns.insert(0, abs_rel)
    df_pearson_all = df_pearson_all[columns]
    columns.append('incident_year')
    df_pearson = df_pearson[columns]

    pearsoncorr_all = df_pearson_all.corr(method='pearson')
    pearson_gas_leaks_all = pearsoncorr_all[abs_rel]

    attributes = [col.replace('_', ' ').capitalize()
                  for col in pearsoncorr_all.columns if (col != 'gas_leaks_per_person' and col!= 'gas_leaks')]


    matrix = [[] for _ in range(len(attributes))]
    years = [year for year in range(2013, 2019)]
    for year in years:
        df_pearson_year = df_pearson[df_pearson['incident_year'] == year]
        df_pearson_year = df_pearson_year.drop(columns={'incident_year'})
        pearsoncorr = df_pearson_year.corr(method='pearson')
        pearson_gas_leaks = pearsoncorr[abs_rel]
        for i in range(len(attributes)):
            matrix[i].append(pearson_gas_leaks[i+1])
    for i in range(len(attributes)):
        matrix[i].append(pearson_gas_leaks_all[i+1])

    years.append('all')
    pearson_df = pd.DataFrame(matrix, columns=years, index=attributes)
    sorted_pearson_df = pearson_df.sort_values(by=['all'], ascending = 'False')

    heatmap = go.Figure(
        data=go.Heatmap(
            z=sorted_pearson_df,
            x=years,
            #y=attributes[1:],
            y=sorted_pearson_df.index.values.tolist() ,
            colorscale='RdBu',
            colorbar=dict(title='Pearson coef.'),
            xgap=20,
            zmax=0.8,
            zmin=-0.8,
            zmid=0))

    heatmap.update_layout(
        xaxis={'type': 'category'},
        title={
            'text': '<b>Pearson correlation coefficient by year ('+ abs_rel.replace('_', ' ').capitalize() + ')</b>',
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        height=480,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        autosize=True)

    heatmap_nation = go.Figure(
        data=go.Heatmap(
            z=sorted_pearson_nation_df,
            x=years,
            #y=attributes[1:],
            y=sorted_pearson_nation_df.index.values.tolist() ,
            colorscale='RdBu',
            colorbar=dict(title='Pearson coef.'),
            xgap=10,
            zmax=0.8,
            zmin=-0.8,
            zmid=0))

    heatmap_nation.update_layout(
        xaxis={'type': 'category'},
        title={
            'text': '<b>Pearson correlation coefficient by year ('+ abs_rel.replace('_', ' ').capitalize() + ')</b>',
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        height=480,
        width = 800,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        autosize=True)
    return heatmap, heatmap_nation


# update monthly representation of #gas_leaks/person based on selected locations and outliers limits
@app.callback(
    Output('timeline_by_month', 'figure'),
    [
        Input('selected_geoids', 'children'), 
        Input('outliers_toggle', 'on'),
        Input('limit_outliers_field', 'value'),
        Input('radio_btn', 'value')
    ])
def display_selected_data(selected_geoids, hideOutliers, limit, abs_rel):

    months_data = months_centers_df
    if len(selected_geoids)>0:
        months_data = months_data[months_data['geoid'].isin(selected_geoids)]
    

    if hideOutliers:
        df_selected = months_data[months_data['gas_leaks_per_person'] < limit]
    else:
        df_selected = months_data

    df_selected = df_selected[df_selected['nta'].str[:6] != 'park-c']
    df_selected = df_selected.groupby(['incident_year', 'incident_month', 'geoid']).agg(
        {'gas_leaks': 'sum', 'total_population': 'sum'}).reset_index()
    df_selected['gas_leaks_per_person'] = df_selected['gas_leaks']/df_selected['total_population']

    # some of the values are inf, as we divide by population, and population is 0 in some areas (like parks)
    df_selected = df_selected[df_selected['gas_leaks_per_person'] < 1]

    fig = go.Figure()
    months = [month for month in range(1, 13)]
    months_str = ['Jan', 'Feb', 'Mar', 'Apr', "May",
                  'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    if abs_rel == 'gas_leaks_per_person':
        temp = "<b># Gas Leaks per Person (Monthly, for a Given Area)</b>"
        temp2 = ' (10<sup>-3</sup> gl/p)'
        power = 700
    else:
        temp = "<b># Gas Leaks (Monthly, for a Given Area)</b>"
        power = 1
        temp2 = ' '

    # add monthly gas_leaks per person for each year
    for year in range(2013, 2018):

        df_year = df_selected[df_selected['incident_year'] == year].groupby(['incident_month']).agg(
            {'gas_leaks': 'sum', 'total_population': 'sum'}).reset_index()
        df_year['gas_leaks_per_person'] = df_year['gas_leaks']/df_year['total_population']*power # avoid tiny numbers and mu

        # some areas had no gas leaks during some months, so fill it with zeros
        for i in range(12):
            if i+1 not in df_year['incident_month']:
                df_year = df_year.append(
                    {'incident_month': i+1, abs_rel: 0}, ignore_index=True)

        gas_leaks = [df_year.iloc[i][abs_rel]
                     for i in range(12)]

        fig.add_trace(go.Scatter(x=months_str, y=gas_leaks,
                                 line=dict(width=0.5),
                                 mode='lines+markers',
                                 name=str(year)))

    # add monthly gas_leaks_per_person consolidated for all years 2013-2017 - trend. (2018 doesn't have information about all months)
    temp_df = df_selected.groupby(['incident_month']).agg(
        {'gas_leaks': 'sum', 'total_population': 'sum'}).reset_index()
    temp_df['gas_leaks_per_person'] = temp_df['gas_leaks']/temp_df['total_population']*power # avoid tiny numbers and mu

    # some areas had no gas leaks during some months, so fill it with zeros
    for i in range(12):
        if i+1 not in temp_df['incident_month']:
            temp_df = temp_df.append(
                {'incident_month': i+1, abs_rel: 0}, ignore_index=True)

    gas_leaks = [temp_df.iloc[i][abs_rel] for i in range(12)]

    fig.add_trace(go.Scatter(x=months_str, y=gas_leaks,
                             line=dict(color='black', width=2),
                             mode='lines+markers',
                             name='2013-2017'))
    
    fig.update_layout(xaxis_title='Month',
                      yaxis_title=abs_rel.replace('_', ' ').capitalize()+ temp2,
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      title={
                          'text': temp,
                          'x': 0.5,
                          'xanchor': 'center'}
                      )
    return fig


if __name__ == '__main__':
   # app.config['suppress_callback_exceptions'] = True
    app.run_server(debug=True)