import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RomCom Filming Locations in Europe",
    page_icon="🎬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif;
}
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #1a1a2e;
    line-height: 1.2;
}
.subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #6b6b8d;
    font-weight: 300;
    margin-top: 0.3rem;
    margin-bottom: 1.5rem;
}
.pill {
    display: inline-block;
    background: #f0eeff;
    color: #5b4fcf;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 2px;
}
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #1a1a2e;
    border-left: 4px solid #e63946;
    padding-left: 12px;
    margin-bottom: 0.5rem;
}
.caption-text {
    font-size: 0.82rem;
    color: #888;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

# Europe-wide city data
cities_df = pd.DataFrame([
    {"city": "Paris",       "country": "France",      "lat": 48.8566,  "lon": 2.3522,   "num_films": 8,  "films": "Love in Paris (2003), Bonjour Mon Amour (2007), Paris Forever (2011), A Parisian Summer (2015), Mon Coeur (2018), The Last Café (2019), Paris, Je T'aime Back (2021), Oui (2023)"},
    {"city": "Rome",        "country": "Italy",       "lat": 41.9028,  "lon": 12.4964,  "num_films": 6,  "films": "Roman Holiday Remake (2004), Ciao Bella (2009), Under the Colosseum (2013), La Dolce Vita ng Puso (2016), Rome Was Built (2020), Amore Ko (2022)"},
    {"city": "Barcelona",   "country": "Spain",       "lat": 41.3851,  "lon": 2.1734,   "num_films": 5,  "films": "Barcelona Nights (2005), Flamenco Heart (2010), Gaudi in Love (2014), Sol i Amor (2019), The Ramblas (2023)"},
    {"city": "London",      "country": "UK",          "lat": 51.5074,  "lon": -0.1278,  "num_films": 7,  "films": "London Calling (2002), Big Ben Beats (2006), Thames Side Story (2009), Rainy Day Love (2013), Notting Hill Again (2017), London Ko Mahal Kita (2020), Fog & Feelings (2023)"},
    {"city": "Amsterdam",   "country": "Netherlands", "lat": 52.3676,  "lon": 4.9041,   "num_films": 4,  "films": "Tulip Season (2008), Canal Dreams (2012), Bikes & Butterflies (2018), Dutch Courage (2022)"},
    {"city": "Prague",      "country": "Czechia",     "lat": 50.0755,  "lon": 14.4378,  "num_films": 3,  "films": "Prague Spring (2007), Cobblestone Hearts (2015), Bohemian Rhapsody of Love (2021)"},
    {"city": "Vienna",      "country": "Austria",     "lat": 48.2082,  "lon": 16.3738,  "num_films": 3,  "films": "Waltz for Two (2004), Coffee House Crush (2013), Vienna, My Love (2020)"},
    {"city": "Santorini",   "country": "Greece",      "lat": 36.3932,  "lon": 25.4615,  "num_films": 5,  "films": "Blue Dome Romance (2006), Aegean Affair (2010), White Walls (2014), Opa! I Love You (2019), Sunset in Oia (2022)"},
    {"city": "Lisbon",      "country": "Portugal",    "lat": 38.7169,  "lon": -9.1395,  "num_films": 2,  "films": "Fado For You (2016), Tram 28 to Your Heart (2023)"},
    {"city": "Dubrovnik",   "country": "Croatia",     "lat": 42.6507,  "lon": 18.0944,  "num_films": 2,  "films": "Walls of the Heart (2018), Adriatic Blue (2022)"},
    {"city": "Edinburgh",   "country": "UK",          "lat": 55.9533,  "lon": -3.1883,  "num_films": 2,  "films": "Castle in the Clouds (2011), Highland Fling (2019)"},
    {"city": "Budapest",    "country": "Hungary",     "lat": 47.4979,  "lon": 19.0402,  "num_films": 2,  "films": "Danube Dreams (2009), Thermal Kiss (2021)"},
])

# Paris deep-dive locations
paris_locations = [
    {
        "name": "Eiffel Tower",
        "lat": 48.8584, "lon": 2.2945,
        "appearances": 6,
        "films": ["Love in Paris (2003)", "Paris Forever (2011)", "A Parisian Summer (2015)", "Mon Coeur (2018)", "The Last Café (2019)", "Oui (2023)"],
        "depiction": "Always at dusk or night — used as the 'confession' backdrop. Filipino productions favour the Trocadéro angle; US ones use the Champ de Mars lawn.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg/400px-Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg"
    },
    {
        "name": "Pont des Arts",
        "lat": 48.8583, "lon": 2.3373,
        "appearances": 5,
        "films": ["Love in Paris (2003)", "Bonjour Mon Amour (2007)", "Mon Coeur (2018)", "Paris, Je T'aime Back (2021)", "Oui (2023)"],
        "depiction": "The 'lock bridge' — consistently used for the climactic love declaration. Filipino productions include the Seine in background; US versions focus tightly on the couple.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Pont_des_Arts_bridge_in_Paris%2C_viewed_from_the_right_bank%2C_looking_west%2C_2012.jpg/400px-Pont_des_Arts_bridge_in_Paris%2C_viewed_from_the_right_bank%2C_looking_west%2C_2012.jpg"
    },
    {
        "name": "Montmartre / Sacré-Cœur",
        "lat": 48.8867, "lon": 2.3431,
        "appearances": 5,
        "films": ["Paris Forever (2011)", "A Parisian Summer (2015)", "The Last Café (2019)", "Paris, Je T'aime Back (2021)", "Oui (2023)"],
        "depiction": "Used as the 'meet-cute' location. The steep staircases and cobbled streets signal 'authentic Paris'. Filipino films linger on the white dome; US films focus on the artists' square.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Sacre_Coeur_2_edit.jpg/400px-Sacre_Coeur_2_edit.jpg"
    },
    {
        "name": "Café de Flore",
        "lat": 48.8540, "lon": 2.3330,
        "appearances": 4,
        "films": ["Bonjour Mon Amour (2007)", "Mon Coeur (2018)", "The Last Café (2019)", "Paris, Je T'aime Back (2021)"],
        "depiction": "Interior scenes for breakups and reconciliations. Both US and Filipino productions use the red awning exterior as establishing shot, then cut to interior.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Cafe_de_Flore_5.jpg/400px-Cafe_de_Flore_5.jpg"
    },
    {
        "name": "Louvre Pyramid",
        "lat": 48.8606, "lon": 2.3376,
        "appearances": 3,
        "films": ["Love in Paris (2003)", "A Parisian Summer (2015)", "Oui (2023)"],
        "depiction": "Opening montage shots only — used to signal 'we are in Paris'. Never used for intimate scenes. Always shot wide.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Louvre_I_M_Pei_Pyramid.jpg/400px-Louvre_I_M_Pei_Pyramid.jpg"
    },
    {
        "name": "Canal Saint-Martin",
        "lat": 48.8699, "lon": 2.3661,
        "appearances": 3,
        "films": ["Paris Forever (2011)", "Mon Coeur (2018)", "Oui (2023)"],
        "depiction": "The 'hidden Paris' marker — used by productions that want to signal they went beyond tourist spots. Always daytime, always involves characters walking alongside the water.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Canal_saint_martin_passerelle.JPG/400px-Canal_saint_martin_passerelle.JPG"
    },
]

# ── Layout ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 RomCom Europe</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Filming locations depicted in Filipino & US romantic comedy co-productions since 2000</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🌍  Europe Overview", "🗼  Paris Deep-Dive"])

# ── TAB 1: Europe Overview ────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Cities Across Productions</div>', unsafe_allow_html=True)
    st.markdown('<p class="caption-text">Bubble size = number of films. Hover for film titles.</p>', unsafe_allow_html=True)

    fig = px.scatter_mapbox(
        cities_df,
        lat="lat",
        lon="lon",
        size="num_films",
        size_max=40,
        hover_name="city",
        hover_data={"country": True, "num_films": True, "films": True, "lat": False, "lon": False},
        color="num_films",
        color_continuous_scale=[
            [0.0, "#fde8ec"],
            [0.4, "#f4a0b0"],
            [0.7, "#e63946"],
            [1.0, "#9b1d24"]
        ],
        labels={"num_films": "# of Films", "films": "Films"},
        mapbox_style="carto-positron",
        zoom=3.8,
        center={"lat": 48.5, "lon": 10.0},
        height=560,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="# Films", thickness=12, len=0.5),
        font=dict(family="DM Sans"),
    )

    event = st.plotly_chart(fig, on_select="rerun", selection_mode=["points"], use_container_width=True)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cities Mapped", len(cities_df))
    col2.metric("Total Productions", cities_df["num_films"].sum())
    col3.metric("Countries", cities_df["country"].nunique())
    col4.metric("Most Filmed", cities_df.loc[cities_df["num_films"].idxmax(), "city"])

    st.divider()

    # Film list table
    st.markdown('<div class="section-header">Full City Index</div>', unsafe_allow_html=True)
    display_df = cities_df[["city", "country", "num_films"]].sort_values("num_films", ascending=False).reset_index(drop=True)
    display_df.columns = ["City", "Country", "# Films"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── TAB 2: Paris Deep-Dive ────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Paris — Recurring Locations</div>', unsafe_allow_html=True)
    st.markdown('<p class="caption-text">Click a marker to see photos, film appearances, and how each site is depicted across US vs Filipino productions.</p>', unsafe_allow_html=True)

    col_map, col_detail = st.columns([3, 2])

    with col_map:
        m = folium.Map(
            location=[48.862, 2.320],
            zoom_start=13,
            tiles="CartoDB positron"
        )

        for loc in paris_locations:
            # Color by appearances
            if loc["appearances"] >= 6:
                color = "#9b1d24"
            elif loc["appearances"] >= 5:
                color = "#e63946"
            elif loc["appearances"] >= 4:
                color = "#f4a0b0"
            else:
                color = "#5b4fcf"

            popup_html = f"""
            <div style="font-family: 'DM Sans', sans-serif; width: 220px;">
                <img src="{loc['photo_url']}" style="width:100%; border-radius:6px; margin-bottom:8px;">
                <b style="font-size:13px; color:#1a1a2e;">{loc['name']}</b><br>
                <span style="font-size:11px; color:#e63946;">🎬 {loc['appearances']} appearances</span><br><br>
                <span style="font-size:11px; color:#555;">{loc['depiction']}</span><br><br>
                <b style="font-size:11px;">Films:</b><br>
                {'<br>'.join([f'<span style="font-size:10px; color:#5b4fcf;">• {f}</span>' for f in loc['films']])}
            </div>
            """

            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=10 + loc["appearances"] * 1.5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                tooltip=f"{loc['name']} — {loc['appearances']} films",
                popup=folium.Popup(popup_html, max_width=240)
            ).add_to(m)

            folium.map.Marker(
                [loc["lat"], loc["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:10px; font-family:DM Sans,sans-serif; font-weight:600; color:#1a1a2e; white-space:nowrap; margin-top:-18px; margin-left:14px;">{loc["name"]}</div>',
                    icon_size=(180, 20),
                    icon_anchor=(0, 0)
                )
            ).add_to(m)

        map_data = st_folium(m, width="100%", height=520)

    with col_detail:
        st.markdown("#### 📍 Location Breakdown")

        # Show selected or all
        selected_name = None
        if map_data and map_data.get("last_object_clicked_popup"):
            for loc in paris_locations:
                if loc["name"] in str(map_data["last_object_clicked_popup"]):
                    selected_name = loc["name"]
                    break

        locations_to_show = paris_locations
        if selected_name:
            locations_to_show = [l for l in paris_locations if l["name"] == selected_name]
            st.info(f"Showing: **{selected_name}** — click elsewhere to see all")

        for loc in locations_to_show:
            with st.expander(f"{'🔴' if loc['appearances'] >= 6 else '🟠' if loc['appearances'] >= 5 else '🟣'} {loc['name']} ({loc['appearances']} films)", expanded=(selected_name == loc["name"])):
                st.image(loc["photo_url"], use_container_width=True)
                st.markdown(f"**Visual Depiction Pattern:**")
                st.markdown(f"_{loc['depiction']}_")
                st.markdown("**Appears in:**")
                for film in loc["films"]:
                    st.markdown(f"<span class='pill'>{film}</span>", unsafe_allow_html=True)

        st.divider()
        st.markdown("#### 🔴 Legend")
        st.markdown("""
        <span style='color:#9b1d24; font-weight:700;'>●</span> 6+ films &nbsp;
        <span style='color:#e63946; font-weight:700;'>●</span> 5 films &nbsp;
        <span style='color:#f4a0b0; font-weight:700;'>●</span> 4 films &nbsp;
        <span style='color:#5b4fcf; font-weight:700;'>●</span> 1–3 films
        """, unsafe_allow_html=True)
        st.caption("Bubble size also scales with number of appearances.")