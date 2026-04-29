import geopandas as gpd
import folium
import mapclassify
from matploblib import pyplot as plt


file = gpd.read_file('comarea\ComArea_ACS14.shp')

file.head()