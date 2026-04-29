pip install streamlit-folium
import folium
from streamlit_folium import st_folium, folium_static
m = folium.Map(location=[df.latitude.mean(), df.longitude.mean()], 
                 zoom_start=3, control_scale=True)

#Loop through each row in the dataframe
for i,row in df.iterrows():
    #Setup the content of the popup
    iframe = folium.IFrame('Well Name:' + str(row["Well Name"]))

    #Initialise the popup using the iframe
    popup = folium.Popup(iframe, min_width=300, max_width=300)

    #Add each row to the map
    folium.Marker(location=[row['latitude'],row['longitude']],
                  popup = popup, c=row['Well Name']).add_to(m)

st_data = st_folium(m, width=700)
folium_static(m, width=700)
