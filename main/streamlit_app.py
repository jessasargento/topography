import geopandas as gpd
import folium
import mapclassify
from matplotlib import pyplot as plt


file = gpd.read_file('comarea/ComArea_ACS14.geojson')

file.head()