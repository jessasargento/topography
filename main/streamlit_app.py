import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import json

# Load Europe GeoJSON
with urlopen('https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson') as response:
    europe = json.load(response)

# Sample data - GDP per capita by country
df = pd.DataFrame({
    'country': ['Germany', 'France', 'Italy', 'Spain', 'Poland',
                'Netherlands', 'Belgium', 'Sweden', 'Norway', 'Denmark',
                'Finland', 'Portugal', 'Greece', 'Austria', 'Switzerland'],
    'gdp_per_capita': [48000, 43000, 35000, 30000, 18000,
                       57000, 47000, 55000, 82000, 62000,
                       49000, 24000, 20000, 52000, 87000]
})

fig = px.choropleth(
    df,
    geojson=europe,
    locations='country',
    featureidkey='properties.NAME',   # key inside the GeoJSON
    color='gdp_per_capita',
    color_continuous_scale='Viridis',
    labels={'gdp_per_capita': 'GDP per Capita (USD)'},
    title='Europe GDP per Capita'
)

fig.update_geos(
    fitbounds="locations",  # auto-zoom to Europe
    visible=False
)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

event = st.plotly_chart(fig, on_select="rerun", selection_mode=["points", "box", "lasso"])
event