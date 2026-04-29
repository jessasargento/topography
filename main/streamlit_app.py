import geopandas as gpd
import folium
import mapclassify
from matplotlib import pyplot as plt
import os

# Build path relative to this script's location
base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'comarea', 'ComArea_ACS14.geojson')

file = gpd.read_file(file_path)
file.head()