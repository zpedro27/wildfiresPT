import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np
from dash import Dash, dcc, html, Input, Output


app = Dash(__name__)


# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div(
    style={'backgroundColor': '#111111'},
    children=[   
        html.H1("Incêndios em Portugal", style={'text-align': 'center', 'color': 'white'}),

        dcc.Slider(id='slider', 
                   min=2000, 
                   max=2020, 
                   step=1, value=2010,
                   marks={x: str(x) if x%5==0 else "" for x in range(2000, 2021, 1)},
                   tooltip={"placement": "bottom", "always_visible": True}),
        
        html.Br(),

        


        html.Div([
            html.Div(id='title', children=[], style={'text-align': 'center', 'color': '#FA5835'}),
            html.Div(className='spacer'),
            dcc.Graph(id='map', figure={}, style={"width": "50%"}),
            html.Div(className='spacer'),
            dcc.Graph(id='barplot', figure={}, style={"width": "50%"}),
            ], style={'display': 'flex'}),

        html.Br(),

        html.Div([
            html.Div(id='title2', children=[], style={'text-align': 'center', 'color': '#FA5835'}),
#            html.Br(),
            dcc.Graph(id='scatterplot_inc', figure={}, style={"width": "33%"}),
            html.Div(className='spacer'),
            dcc.Graph(id='scatterplot_met', figure={}, style={"width": "33%"}),
            html.Div(className='spacer'),
            dcc.Graph(id='scatterplot_frac', figure={}, style={"width": "33%"}),
            ], style={'display': 'flex'})

])

# # ------------------------------------------------------------------------------
# # Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='title', component_property='children'),
     Output(component_id='title2', component_property='children'),
     Output(component_id='map', component_property='figure'),
     Output(component_id='scatterplot_inc', component_property='figure'),
     Output(component_id='scatterplot_met', component_property='figure'),
     Output(component_id='barplot', component_property='figure'),
     Output(component_id='scatterplot_frac', component_property='figure'),
     ],
    [Input(component_id='slider', component_property='value'),
     ]
)

def update_graph(value):

    container = "Incêndios em {}".format(int(value))
    container2 = "Overall trends"

    ## Query results from DB
    conn = sqlite3.connect("incendios_PT.db")
    c = conn.cursor()
    df_occ = pd.read_sql_query("SELECT * FROM incendios WHERE \"Ano\"={};".format(int(value)), conn).replace(np.nan, "NaN")
    df_stats = pd.read_sql_query("SELECT * FROM incendios_stats;", conn)
    df_meteo = pd.read_sql_query("SELECT * FROM meteo_stats;", conn)
    df_meteo.Prec_mm = df_meteo.Prec_mm .astype(float)

    df_occ.loc[df_occ.TipoCausa.isin(["NaN", "Desconhecida"]), "TipoCausa"] = "NaN/Desconh."
    df_occ_agg = df_occ.groupby("TipoCausa").sum().reset_index()


    df_occ_all = pd.read_sql_query("SELECT \"Ano\", \"TipoCausa\", SUM(\"AreaTotal_ha\") as TotalBurnt FROM incendios GROUP BY \"Ano\", \"TipoCausa\";", conn).replace(np.nan, "NaN")
    df_occ_all.loc[df_occ_all.TipoCausa.isin(["NaN", "Desconhecida"]), "TipoCausa"] = "NaN/Desconh."
    df_occ_all["norm_Area"] = df_occ_all.groupby("Ano").transform(lambda x: (x / x.sum() * 100))["TotalBurnt"]
    conn.close()


    # Plot map:
    fig = px.scatter_mapbox(
        df_occ, 
        lat="Latitude", 
        lon="Longitude", 
        hover_name="Codigo_SGIF", 
        size="AreaTotal_ha",
        hover_data=["Local", "TipoCausa"],
        color="TipoCausa",
        color_discrete_sequence=["gray", "yellow", "red", "orange", "white"], 
        zoom=5, 
        #height=500,
        opacity=0.7,
        template='plotly_dark',)
    fig.update_layout(mapbox_style="carto-darkmatter")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Plot total burnt area:
    fig2 = px.scatter(data_frame=df_stats.loc[df_stats.ano>2000], 
                      x="ano", 
                      y="supArdida_ha",
                      hover_name="ano",
                      template='plotly_dark',
                      )
    fig2.add_vrect(x0=int(value)-0.5, x1=int(value)+0.5)
    #fig2.add_traces(px.scatter(data_frame=df_stats.loc[df_stats.ano==value], x="ano", y="supArdida_ha").update_traces(marker_size=15, marker_color="red").data )

    # Plot pluviosity:
    fig3 = px.scatter(data_frame=df_meteo.loc[df_meteo.ano>2000],  
                      x="ano", 
                      y="Prec_mm",
                      hover_name="ano",
                      template='plotly_dark',
                      )
    fig3.add_vrect(x0=int(value)-0.5, x1=int(value)+0.5)
    #fig3.add_traces(px.scatter(data_frame=df_meteo.loc[df_meteo.ano==value], x="ano", y="Prec_mm").update_traces(marker_size=15, marker_color="red").data )

    # Plot total burnt area:
    fig4 = px.bar(data_frame=df_occ_agg.sort_values(by="AreaTotal_ha"), 
                      x="TipoCausa", 
                      y="AreaTotal_ha",
                      #hover_name="ano",
                      template='plotly_dark',
                      )

    # Plot fraction2:
    fig5 = px.bar(data_frame=df_occ_all, 
                      x="Ano", 
                      y="norm_Area",
                      color="TipoCausa",
                      #hover_name="ano",
                      template='plotly_dark',
                      #fill='tonexty'
                      )
    fig5.add_vrect(x0=int(value)-0.5, x1=int(value)+0.5)


    return container, container2, fig, fig2, fig3, fig4, fig5


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)