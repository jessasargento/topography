import os
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Filipino RomCom Filming Locations",
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

# ── Load & transform data ─────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """
    Reads the wide-format CSV and returns two DataFrames:
      - long_df  : one row per (film, location) with lat/lon
      - cities_df: one row per unique city, aggregated film counts
    """
    # Resolve path relative to this script so it works from any working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "ph_romance.csv")
    raw = pd.read_csv(csv_path)

    # Column name mapping — location 4 has a typo: lon column is "Longitude_5"
    lon_cols = {1: "Longitude_1", 2: "Longitude_2", 3: "Longitude_3",
                4: "Longitude_5", 5: None}   # location 5 has no coords in the CSV

    records = []
    for _, row in raw.iterrows():
        for i in range(1, 6):
            city    = row.get(f"city_{i}")
            country = row.get(f"country_{i}")
            lat     = row.get(f"Latitude_{i}")
            lon_key = lon_cols.get(i)
            lon     = row.get(lon_key) if lon_key else None
            addr    = row.get(f"fulladdress_{i}", "")

            # Skip if no city name or no usable coordinates
            if pd.isna(city) or pd.isna(lat) or pd.isna(lon):
                continue

            records.append({
                "title":   row["title"],
                "year":   int(row["year_of_release"]),
                "genre":   row["film_genre"],
                "runtime": row.get("runtime"),
                "origin":  row.get("country_of_origin"),
                "city":    str(city).strip(),
                "country": str(country).strip() if pd.notna(country) else "",
                "address": str(addr).strip() if pd.notna(addr) else "",
                "lat":     float(lat),
                "lon":     float(lon),
            })

    long_df = pd.DataFrame(records)

    # Aggregate: one row per unique city (by name + country)
    cities_df = (
        long_df
        .groupby(["city", "country", "lat", "lon"], as_index=False)
        .agg(
            num_films=("title", "nunique"),
            films=("title", lambda x: ", ".join(sorted(x.unique()))),
            years=("year", lambda x: ", ".join(str(y) for y in sorted(x.unique()))),
        )
        .sort_values("num_films", ascending=False)
        .reset_index(drop=True)
    )

    return long_df, cities_df

long_df, cities_df = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 Filipino RomCom — Filming Locations</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">International filming locations across Filipino romantic comedy productions</div>',
    unsafe_allow_html=True
)

tab1, tab2 = st.tabs(["🌍  World Overview", "📍  City Deep-Dive"])

# ── TAB 1: World Overview ─────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Cities Across Productions</div>', unsafe_allow_html=True)
    st.markdown('<p class="caption-text">Bubble size = number of films shot there. Hover for film titles.</p>', unsafe_allow_html=True)

    fig = px.scatter_mapbox(
        cities_df,
        lat="lat",
        lon="lon",
        size="num_films",
        size_max=40,
        hover_name="city",
        hover_data={
            "country":   True,
            "num_films": True,
            "films":     True,
            "years":     True,
            "lat":       False,
            "lon":       False,
        },
       color="num_films",
        color_continuous_scale=[
            [0.0, "#c1506a"],
            [0.4, "#e63946"],
            [0.7, "#b5182a"],
            [1.0, "#6b0a14"],
        ],
        labels={"num_films": "# of Films", "films": "Films", "years": "Year(s)"},
        mapbox_style="carto-positron",
        zoom=1.5,
        center={"lat": 20.0, "lon": 10.0},
        height=560,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="# Films", thickness=12, len=0.5),
        font=dict(family="DM Sans"),
    )

    st.plotly_chart(fig, on_select="rerun", selection_mode=["points"], use_container_width=True)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cities Mapped",    len(cities_df))
    col2.metric("Total Productions", long_df["title"].nunique())
    col3.metric("Countries",         cities_df["country"].nunique())
    col4.metric("Most Filmed",       cities_df.loc[cities_df["num_films"].idxmax(), "city"])

    st.divider()

    # Full index table
    st.markdown('<div class="section-header">Full City Index</div>', unsafe_allow_html=True)
    display_df = (
        cities_df[["city", "country", "num_films", "films"]]
        .copy()
        .rename(columns={"city": "City", "country": "Country",
                         "num_films": "# Films", "films": "Films"})
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── TAB 2: City Deep-Dive ─────────────────────────────────────────────────────
with tab2:
    # Build list of cities that appear in at least 1 film; sort by film count desc
    city_options = (
        cities_df[["city", "country", "num_films"]]
        .apply(lambda r: f"{r['city']} ({r['country']}) — {r['num_films']} film{'s' if r['num_films'] > 1 else ''}",
               axis=1)
        .tolist()
    )
    city_keys = cities_df[["city", "country"]].apply(
        lambda r: (r["city"], r["country"]), axis=1
    ).tolist()

    st.markdown('<div class="section-header">Explore a City</div>', unsafe_allow_html=True)
    selected_label = st.selectbox(
        "Choose a city to explore:",
        options=city_options,
        index=0,
    )

    # Resolve selected city/country
    sel_idx   = city_options.index(selected_label)
    sel_city, sel_country = city_keys[sel_idx]

    # Filter long_df to selected city
    city_films = long_df[
        (long_df["city"] == sel_city) & (long_df["country"] == sel_country)
    ].drop_duplicates("title").sort_values("year")

    city_meta = cities_df[
        (cities_df["city"] == sel_city) & (cities_df["country"] == sel_country)
    ].iloc[0]

    st.markdown(
        f'<p class="caption-text">Showing all films set (at least partially) in '
        f'<b>{sel_city}</b>, {sel_country}. Click a marker for address details.</p>',
        unsafe_allow_html=True
    )

    col_map, col_detail = st.columns([3, 2])

    with col_map:
        m = folium.Map(
            location=[city_meta["lat"], city_meta["lon"]],
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # One marker per unique address in this city across all films
        # (multiple films can share the same coords if only city-level coords are known)
        addr_groups = (
            long_df[
                (long_df["city"] == sel_city) & (long_df["country"] == sel_country)
            ]
            .groupby(["lat", "lon", "address"], as_index=False)
            .agg(film_list=("title", lambda x: list(x.unique())))
        )

        colors = ["#e63946", "#5b4fcf", "#2a9d8f", "#e9c46a", "#f4a0b0"]

        for i, (_, loc) in enumerate(addr_groups.iterrows()):
            color = colors[i % len(colors)]
            films_html = "".join(
                f'<span style="font-size:10px; color:#5b4fcf;">• {f}</span><br>'
                for f in loc["film_list"]
            )
            popup_html = f"""
            <div style="font-family:'DM Sans',sans-serif; width:210px;">
                <b style="font-size:12px; color:#1a1a2e;">{loc['address'] or sel_city}</b><br>
                <span style="font-size:11px; color:#e63946;">🎬 {len(loc['film_list'])} film(s)</span><br><br>
                <b style="font-size:11px;">Films:</b><br>{films_html}
            </div>
            """
            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=10 + len(loc["film_list"]) * 3,
                color=color, fill=True, fill_color=color, fill_opacity=0.75,
                tooltip=f"{loc['address'] or sel_city} — {len(loc['film_list'])} film(s)",
                popup=folium.Popup(popup_html, max_width=230),
            ).add_to(m)

        st_folium(m, width="100%", height=480)

    with col_detail:
        st.markdown(f"#### 🎬 Films set in {sel_city}")

        for _, film in city_films.iterrows():
            emoji = "🔴" if film["year"] >= 2020 else "🟠" if film["year"] >= 2010 else "🟣"
            with st.expander(f"{emoji} {film['title']} ({int(film['year'])})", expanded=True):
                meta_cols = st.columns(2)
                meta_cols[0].markdown(f"**Genre**")
                meta_cols[0].markdown(f"_{film['genre']}_")
                meta_cols[1].markdown(f"**Runtime**")
                meta_cols[1].markdown(f"_{film['runtime']} min_" if pd.notna(film['runtime']) else "_—_")
                if film["address"]:
                    st.markdown(f"**Location:** {film['address']}")
                st.markdown(
                    f"<span class='pill'>{film['origin']}</span>",
                    unsafe_allow_html=True
                )

        st.divider()
        st.markdown("#### 🔴 Legend")
        st.markdown("""
        <span style='color:#e63946; font-weight:700;'>●</span> 2020s &nbsp;
        <span style='color:#f4a0b0; font-weight:700;'>●</span> 2010s &nbsp;
        <span style='color:#5b4fcf; font-weight:700;'>●</span> 2000s
        """, unsafe_allow_html=True)
        st.caption("Bubble size scales with number of film appearances at that location.")
