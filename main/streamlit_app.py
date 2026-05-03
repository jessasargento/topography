import os
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RomCom Filming Locations",
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
.pill     { display: inline-block; background: #f0eeff; color: #5b4fcf; border-radius: 20px; padding: 3px 12px; font-size: 0.78rem; font-weight: 500; margin: 2px; }
.pill-ph  { display: inline-block; background: #fff0f0; color: #c1506a; border-radius: 20px; padding: 3px 12px; font-size: 0.78rem; font-weight: 500; margin: 2px; }
.pill-us  { display: inline-block; background: #f0f4ff; color: #3a5fcf; border-radius: 20px; padding: 3px 12px; font-size: 0.78rem; font-weight: 500; margin: 2px; }
.section-header { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a1a2e; border-left: 4px solid #e63946; padding-left: 12px; margin-bottom: 0.5rem; }
.caption-text { font-size: 0.82rem; color: #888; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ── Shared parsing logic ──────────────────────────────────────────────────────
# Column name mapping — location 4 has a typo: lon column is "Longitude_5"
LON_COLS = {1: "Longitude_1", 2: "Longitude_2", 3: "Longitude_3",
            4: "Longitude_5", 5: None}


def safe_filename(title: str) -> str:
    name = re.sub(r'[^\w\s-]', '', title).strip()
    name = re.sub(r'[\s]+', '_', name)
    return name[:80] + ".jpg"

def parse_csv(csv_path: str, source_label: str) -> pd.DataFrame:
    """
    Read one wide-format CSV and return a normalised long DataFrame.
    source_label ('Filipino' / 'US') is stored so datasets can be
    distinguished after merging.
    """
    raw = pd.read_csv(csv_path)
    records = []
    for _, row in raw.iterrows():
        for i in range(1, 6):
            city    = row.get(f"city_{i}")
            country = row.get(f"country_{i}")
            lat     = row.get(f"Latitude_{i}")
            lon_key = LON_COLS.get(i)
            lon     = row.get(lon_key) if lon_key else None
            addr    = row.get(f"fulladdress_{i}", "")

            if pd.isna(city) or pd.isna(lat) or (lon is None or pd.isna(lon)):
                continue

            poster = row.get("poster_url", "")
            records.append({
                "source":     source_label,
                "title":      row["title"],
                "year":       int(row["year_of_release"]),
                "genre":      row["film_genre"],
                "runtime":    row.get("runtime"),
                "origin":     row.get("country_of_origin"),
                "city":       str(city).strip(),
                "country":    str(country).strip() if pd.notna(country) else "",
                "address":    str(addr).strip() if pd.notna(addr) else "",
                "lat":        float(lat),
                "lon":        float(lon),
                "poster_url": str(poster).strip() if pd.notna(poster) else "",
            })
    return pd.DataFrame(records)


def build_cities(long_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate long_df to one row per unique city."""
    return (
        long_df
        .groupby(["city", "country", "lat", "lon"], as_index=False)
        .agg(
            num_films=("title",  "nunique"),
            films    =("title",  lambda x: ", ".join(sorted(x.unique()))),
            years    =("year",   lambda x: ", ".join(str(y) for y in sorted(x.unique()))),
            sources  =("source", lambda x: " + ".join(sorted(x.unique()))),
        )
        .sort_values("num_films", ascending=False)
        .reset_index(drop=True)
    )


# ── Load both CSVs (cached) ───────────────────────────────────────────────────
@st.cache_data
def load_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    ph_path = os.path.join(base_dir, "ph_romance.csv")
    us_path = os.path.join(base_dir, "us_romance.csv")

    ph_long = parse_csv(ph_path, "Filipino") if os.path.exists(ph_path) else pd.DataFrame()
    us_long = parse_csv(us_path, "US")       if os.path.exists(us_path) else pd.DataFrame()
    all_long = pd.concat([ph_long, us_long], ignore_index=True)

    return {
        "🇵🇭  Filipino":  (ph_long,  build_cities(ph_long)  if not ph_long.empty  else pd.DataFrame()),
        "🇺🇸  US":        (us_long,  build_cities(us_long)  if not us_long.empty  else pd.DataFrame()),
        "🌐  All Films":  (all_long, build_cities(all_long) if not all_long.empty else pd.DataFrame()),
    }

datasets = load_all()

# ── Header + dataset toggle ───────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 RomCom — Filming Locations</div>', unsafe_allow_html=True)

dataset_choice = st.radio(
    "Dataset",
    options=list(datasets.keys()),
    horizontal=True,
    label_visibility="collapsed",
)

long_df, cities_df = datasets[dataset_choice]

SUBTITLES = {
    "🇵🇭  Filipino": "Filipino romantic comedy productions",
    "🇺🇸  US":       "US romantic comedy productions",
    "🌐  All Films": "All productions combined — Filipino & US",
}
st.markdown(f'<div class="subtitle">{SUBTITLES[dataset_choice]}</div>', unsafe_allow_html=True)

# Guard: warn clearly if a CSV file is missing
if long_df.empty:
    st.warning(
        f"No data loaded for **{dataset_choice.strip()}**. "
        "Make sure the corresponding CSV file is in the same folder as this script."
    )
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🌍  World Overview", "🗺️  Country Deep-Dive"])

# ── TAB 1: World Overview ─────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Cities Across Productions</div>', unsafe_allow_html=True)
    st.markdown('<p class="caption-text">Bubble size = number of films shot there. Hover for film titles.</p>', unsafe_allow_html=True)

    # "All Films" mode: colour bubbles by which dataset(s) a city appears in
    # Single-dataset modes: colour by film count
    if dataset_choice == "🌐  All Films":
        color_kwargs = dict(
            color="sources",
            color_discrete_map={
                "Filipino":          "#e63946",
                "US":                "#3a5fcf",
                "Filipino + US":     "#8b5cf6",
            },
        )
    else:
        color_kwargs = dict(
            color="num_films",
            color_continuous_scale=[
                [0.0, "#c1506a"],
                [0.4, "#e63946"],
                [0.7, "#b5182a"],
                [1.0, "#6b0a14"],
            ],
        )

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
        labels={
            "num_films": "# of Films",
            "films":     "Films",
            "years":     "Year(s)",
            "sources":   "Origin",
        },
        mapbox_style="carto-positron",
        zoom=1.5,
        center={"lat": 20.0, "lon": 10.0},
        height=560,
        **color_kwargs,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="# Films", thickness=12, len=0.5),
        font=dict(family="DM Sans"),
    )

    st.plotly_chart(fig, on_select="rerun", selection_mode=["points"], use_container_width=True)

    # "All Films" colour legend
    if dataset_choice == "🌐  All Films":
        st.markdown(
            '<span style="color:#e63946;font-weight:700;">●</span> Filipino &nbsp;'
            '<span style="color:#3a5fcf;font-weight:700;">●</span> US &nbsp;'
            '<span style="color:#8b5cf6;font-weight:700;">●</span> Both',
            unsafe_allow_html=True,
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cities Mapped",     len(cities_df))
    col2.metric("Total Productions", long_df["title"].nunique())
    col3.metric("Countries",         cities_df["country"].nunique())
    col4.metric("Most Filmed",       cities_df.loc[cities_df["num_films"].idxmax(), "city"])

    st.divider()

    st.markdown('<div class="section-header">Full City Index</div>', unsafe_allow_html=True)
    table_cols = ["city", "country", "num_films", "films"]
    if dataset_choice == "🌐  All Films":
        table_cols.append("sources")
    display_df = (
        cities_df[table_cols]
        .copy()
        .rename(columns={"city": "City", "country": "Country",
                         "num_films": "# Films", "films": "Films",
                         "sources": "Origin"})
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── TAB 2: Country Deep-Dive ──────────────────────────────────────────────────
with tab2:
    # Build sorted country list: most-filmed first
    country_stats = (
        long_df
        .groupby("country", as_index=False)
        .agg(
            num_films=("title",  "nunique"),
            num_cities=("city",  "nunique"),
            films    =("title",  lambda x: sorted(x.unique())),
        )
        .sort_values("num_films", ascending=False)
        .reset_index(drop=True)
    )

    country_options = country_stats.apply(
        lambda r: (
            f"{r['country']} — "
            f"{r['num_films']} film{'s' if r['num_films'] > 1 else ''}, "
            f"{r['num_cities']} cit{'ies' if r['num_cities'] > 1 else 'y'}"
        ),
        axis=1,
    ).tolist()

    st.markdown('<div class="section-header">Explore a Country</div>', unsafe_allow_html=True)
    selected_country_label = st.selectbox(
        "Choose a country to explore:",
        options=country_options,
        index=0,
    )

    sel_country = country_stats.iloc[country_options.index(selected_country_label)]["country"]

    # All data for the selected country
    country_long  = long_df[long_df["country"] == sel_country]
    country_cities = (
        country_long
        .groupby(["city", "lat", "lon"], as_index=False)
        .agg(
            num_films=("title",  "nunique"),
            film_list=("title",  lambda x: list(x.unique())),
            src_list =("source", lambda x: list(x.unique())),
        )
        .sort_values("num_films", ascending=False)
    )
    country_films = (
        country_long
        .drop_duplicates("title")
        .sort_values("year")
    )

    num_films_country  = country_films["title"].nunique()
    num_cities_country = country_cities["city"].nunique()

    st.markdown(
        f'<p class="caption-text">'
        f'<b>{sel_country}</b> — {num_films_country} film{"s" if num_films_country > 1 else ""} '
        f'across {num_cities_country} cit{"ies" if num_cities_country > 1 else "y"}. '
        f'Each bubble is a city; click for film details.</p>',
        unsafe_allow_html=True,
    )

    col_map, col_detail = st.columns([3, 2])

    with col_map:
        # Auto-centre & zoom to fit all cities in this country
        avg_lat = country_cities["lat"].mean()
        avg_lon = country_cities["lon"].mean()
        lat_range = country_cities["lat"].max() - country_cities["lat"].min()
        lon_range = country_cities["lon"].max() - country_cities["lon"].min()
        span = max(lat_range, lon_range)
        if span < 0.5:
            zoom = 11
        elif span < 2:
            zoom = 8
        elif span < 5:
            zoom = 6
        elif span < 15:
            zoom = 5
        else:
            zoom = 4

        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=zoom,
            tiles="CartoDB positron",
        )

        marker_colors = ["#e63946", "#5b4fcf", "#2a9d8f", "#e9c46a", "#f4a0b0"]

        for i, (_, loc) in enumerate(country_cities.iterrows()):
            color      = marker_colors[i % len(marker_colors)]
            films_html = "".join(
                f'<span style="font-size:10px; color:#5b4fcf;">• {f}</span><br>'
                for f in loc["film_list"]
            )
            badges = "".join(
                f'<span style="background:{"#fff0f0" if s == "Filipino" else "#f0f4ff"}; '
                f'color:{"#c1506a" if s == "Filipino" else "#3a5fcf"}; '
                f'border-radius:10px; padding:1px 8px; font-size:10px; margin-right:4px;">{s}</span>'
                for s in loc["src_list"]
            )
            popup_html = f"""
            <div style="font-family:'DM Sans',sans-serif; width:210px;">
                <b style="font-size:13px; color:#1a1a2e;">📍 {loc['city']}</b><br>
                <span style="font-size:11px; color:#e63946;">🎬 {loc['num_films']} film(s)</span>
                &nbsp;{badges}<br><br>
                <b style="font-size:11px;">Films:</b><br>{films_html}
            </div>
            """
            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=10 + loc["num_films"] * 4,
                color=color, fill=True, fill_color=color, fill_opacity=0.78,
                tooltip=f"{loc['city']} — {loc['num_films']} film(s)",
                popup=folium.Popup(popup_html, max_width=230),
            ).add_to(m)

            # City name label
            folium.map.Marker(
                [loc["lat"], loc["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:10px; font-family:DM Sans,sans-serif; '
                         f'font-weight:600; color:#1a1a2e; white-space:nowrap; '
                         f'margin-top:-18px; margin-left:16px;">{loc["city"]}</div>',
                    icon_size=(160, 20),
                    icon_anchor=(0, 0),
                )
            ).add_to(m)

        st_folium(m, width="100%", height=480)

    with col_detail:
        st.markdown(f"#### 🎬 Films set in {sel_country}")

        def origin_pill(src):
            cls = "pill-ph" if src == "Filipino" else "pill-us" if src == "US" else "pill"
            return f"<span class='{cls}'>{src}</span>"

        for _, film in country_films.iterrows():
            emoji = "🔴" if film["year"] >= 2020 else "🟠" if film["year"] >= 2010 else "🟣"
            with st.expander(f"{emoji} {film['title']} ({film['year']})", expanded=False):
                poster_path = os.path.join("posters", safe_filename(film["title"]))
                if os.path.exists(poster_path):
                    # Poster + metadata side by side
                    img_col, info_col = st.columns([1, 2])
                    with img_col:
                        st.image(poster_path, use_container_width=True)
                    with info_col:
                        st.markdown("**Genre**")
                        st.markdown(f"_{film['genre']}_")
                        st.markdown("**Runtime**")
                        st.markdown(f"_{int(film['runtime'])} min_" if pd.notna(film['runtime']) else "_—_")
                        st.markdown(f"**City:** {film['city']}")
                        if film["address"]:
                            st.markdown(f"**Address:** {film['address']}")
                        st.markdown(origin_pill(film["source"]), unsafe_allow_html=True)
                else:
                    # No poster — fall back to plain metadata layout
                    meta_cols = st.columns(2)
                    meta_cols[0].markdown("**Genre**")
                    meta_cols[0].markdown(f"_{film['genre']}_")
                    meta_cols[1].markdown("**Runtime**")
                    meta_cols[1].markdown(f"_{int(film['runtime'])} min_" if pd.notna(film['runtime']) else "_—_")
                    st.markdown(f"**City:** {film['city']}")
                    if film["address"]:
                        st.markdown(f"**Address:** {film['address']}")
                    st.markdown(origin_pill(film["source"]), unsafe_allow_html=True)

        st.divider()
        st.markdown("#### Legend")
        st.markdown("""
        <span style='color:#e63946; font-weight:700;'>●</span> 2020s &nbsp;
        <span style='color:#f4a0b0; font-weight:700;'>●</span> 2010s &nbsp;
        <span style='color:#5b4fcf; font-weight:700;'>●</span> 2000s
        """, unsafe_allow_html=True)
        if dataset_choice == "🌐  All Films":
            st.markdown(
                '<span class="pill-ph">Filipino</span> '
                '<span class="pill-us">US</span> '
                'origin badges shown on each film card.',
                unsafe_allow_html=True,
            )
        st.caption("Bubble size scales with number of film appearances in that city.")
