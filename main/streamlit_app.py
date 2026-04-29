import os
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RomCom Filming Locations in Europe",
    page_icon="🎬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif; }
.main-title { font-family: 'Playfair Display', serif; font-size: 2.6rem; font-weight: 700; color: #1a1a2e; line-height: 1.2; }
.subtitle { font-family: 'DM Sans', sans-serif; font-size: 1rem; color: #6b6b8d; font-weight: 300; margin-top: 0.3rem; margin-bottom: 1.5rem; }
.pill { display: inline-block; background: #f0eeff; color: #5b4fcf; border-radius: 20px; padding: 3px 12px; font-size: 0.78rem; font-weight: 500; margin: 2px; }
.section-header { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a1a2e; border-left: 4px solid #e63946; padding-left: 12px; margin-bottom: 0.5rem; }
.caption-text { font-size: 0.82rem; color: #888; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ── Load data from CSV ────────────────────────────────────────────────────────
base_dir = os.path.dirname(__file__)

@st.cache_data
def load_cities():
    path = os.path.join(base_dir, 'data', 'cities.csv')
    return pd.read_csv(path)

@st.cache_data
def load_paris():
    path = os.path.join(base_dir, 'data', 'paris_locations.csv')
    df = pd.read_csv(path)
    df['films_list'] = df['films'].apply(lambda x: [f.strip() for f in x.split(',')])
    return df

cities_df = load_cities()
paris_df  = load_paris()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 RomCom Europe</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Filming locations depicted in Filipino & US romantic comedy co-productions since 2000</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🌍  Europe Overview", "🗼  Paris Deep-Dive"])

# ── TAB 1: Europe Overview ────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Cities Across Productions</div>', unsafe_allow_html=True)
    st.markdown('<p class="caption-text">Bubble size = number of films. Hover for film titles.</p>', unsafe_allow_html=True)

    fig = px.scatter_mapbox(
        cities_df,
        lat="lat", lon="lon",
        size="num_films",
        size_max=40,
        hover_name="city",
        hover_data={"country": True, "num_films": True, "films": True, "lat": False, "lon": False},
        color="num_films",
        color_continuous_scale=[[0.0, "#fde8ec"], [0.4, "#f4a0b0"], [0.7, "#e63946"], [1.0, "#9b1d24"]],
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

    st.plotly_chart(fig, on_select="rerun", selection_mode=["points"], use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cities Mapped", len(cities_df))
    col2.metric("Total Productions", cities_df["num_films"].sum())
    col3.metric("Countries", cities_df["country"].nunique())
    col4.metric("Most Filmed", cities_df.loc[cities_df["num_films"].idxmax(), "city"])

    st.divider()

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
        m = folium.Map(location=[48.862, 2.320], zoom_start=13, tiles="CartoDB positron")

        for _, loc in paris_df.iterrows():
            appearances = loc["appearances"]
            if appearances >= 6:
                color = "#9b1d24"
            elif appearances >= 5:
                color = "#e63946"
            elif appearances >= 4:
                color = "#f4a0b0"
            else:
                color = "#5b4fcf"

            films_html = ''.join([
                f'<span style="font-size:10px; color:#5b4fcf;">• {f.strip()}</span><br>'
                for f in loc["films"].split(',')
            ])

            popup_html = f"""
            <div style="font-family: 'DM Sans', sans-serif; width: 220px;">
                <img src="{loc['photo_url']}" style="width:100%; border-radius:6px; margin-bottom:8px;">
                <b style="font-size:13px; color:#1a1a2e;">{loc['name']}</b><br>
                <span style="font-size:11px; color:#e63946;">🎬 {appearances} appearances</span><br><br>
                <span style="font-size:11px; color:#555;">{loc['depiction']}</span><br><br>
                <b style="font-size:11px;">Films:</b><br>{films_html}
            </div>
            """

            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=10 + appearances * 1.5,
                color=color, fill=True, fill_color=color, fill_opacity=0.75,
                tooltip=f"{loc['name']} — {appearances} films",
                popup=folium.Popup(popup_html, max_width=240)
            ).add_to(m)

            folium.map.Marker(
                [loc["lat"], loc["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:10px; font-family:DM Sans,sans-serif; font-weight:600; color:#1a1a2e; white-space:nowrap; margin-top:-18px; margin-left:14px;">{loc["name"]}</div>',
                    icon_size=(180, 20), icon_anchor=(0, 0)
                )
            ).add_to(m)

        map_data = st_folium(m, width="100%", height=520)

    with col_detail:
        st.markdown("#### 📍 Location Breakdown")

        selected_name = None
        if map_data and map_data.get("last_object_clicked_popup"):
            for _, loc in paris_df.iterrows():
                if loc["name"] in str(map_data["last_object_clicked_popup"]):
                    selected_name = loc["name"]
                    break

        rows_to_show = paris_df if selected_name is None else paris_df[paris_df["name"] == selected_name]
        if selected_name:
            st.info(f"Showing: **{selected_name}** — click elsewhere to see all")

        for _, loc in rows_to_show.iterrows():
            appearances = loc["appearances"]
            emoji = "🔴" if appearances >= 6 else "🟠" if appearances >= 5 else "🟣"
            with st.expander(f"{emoji} {loc['name']} ({appearances} films)", expanded=(selected_name == loc["name"])):
                st.image(loc["photo_url"], use_container_width=True)
                st.markdown("**Visual Depiction Pattern:**")
                st.markdown(f"_{loc['depiction']}_")
                st.markdown("**Appears in:**")
                for film in loc["films_list"]:
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
