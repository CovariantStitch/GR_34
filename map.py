import folium
import numpy as np
import streamlit as st
from folium.plugins import Draw
from scipy.spatial import cKDTree
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from utils.create_layers import create_geojson_done, create_geojson_features
from utils.departments import load_departments
from utils.gpx import load_and_clean_gpx
from utils.save import add_info


def get_geolocation_():
    loc = get_geolocation()
    if loc is not None:
        user_lat = loc["coords"]["latitude"]
        user_lon = loc["coords"]["longitude"]
    else:
        user_lat = None
        user_lon = None
    st.session_state.user_lat = user_lat
    st.session_state.user_lon = user_lon


def start_map():
    load_departments()
    segments, segment_distances, gpx_points = load_and_clean_gpx('./data/gr-34-en-entier-2020.gpx')
    # compute total distance
    total_distance = sum(segment_distances)
    # create the traces for the all GR34
    geojson_data = create_geojson_features(segments)
    # create the traces for the already done segments
    geojson_done = create_geojson_done(st.session_state.user_data)
    # create a tree for efficient point searching
    tree = cKDTree(np.array(gpx_points))

    # declare some streamlit session state variables
    if 'center' not in st.session_state:
        st.session_state.center = segments[0][0] if segments else [48.8566, 2.3522]
    if 'zoom' not in st.session_state:
        st.session_state.zoom = 8

    # ----------- Start the application ----------- #
    st.title("🗺️ Suivi de l'avancée sur le GR34 de Choupette & Flowflow")

    # compute and show the progress
    distance_done = st.session_state.user_data["Distance"].sum()
    distance_remaining = total_distance - distance_done
    progress = distance_done / total_distance if total_distance > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Kilométrage effectué", f"{distance_done:.2f} km")
    col2.metric("Kilométrage restant", f"{distance_remaining:.2f} km")
    col3.metric("Progression totale", f"{progress:.2%}")
    st.progress(progress)

    # add the map
    cols = st.columns([0.8, 0.2])
    cols[0].subheader("Carte de la progression")
    cols[1].button("Géolocalisation", on_click=get_geolocation_())

    m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom, tiles="OpenStreetMap")

    folium.GeoJson(
        geojson_data, name="Randonnées restantes",
        color="red",
    ).add_to(m, name="Randonnées restantes")

    if len(geojson_done["features"]) > 0:
        folium.GeoJson(
            geojson_done, name="Randonnées effectuées",
            color="green",
            highlight_function=lambda x: {'weight': 8},
            tooltip=folium.features.GeoJsonTooltip(fields=['Date', "Distance", "Locomotion", "Durée"])
        ).add_to(m)

    if st.session_state.user_lat is not None:
        folium.CircleMarker(
            location=[st.session_state.user_lat, st.session_state.user_lon],
            radius=8,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.8,
            popup="Vous êtes ici"
        ).add_to(m)

    # add layer control to show (or not) the different traces
    folium.LayerControl().add_to(m)

    # add drawing possibilities to add markers (used to add done segments)
    draw = Draw(draw_options={
        "polyline": False,
        "polygon": False,
        "circle": False,
        "circlemarker": False,
        "rectangle": False,
        "marker": True,
    }, export=False).add_to(m)

    # create the map
    map_data = st_folium(
        m,
        width='100%',
        height=500,
        returned_objects=['last_clicked', 'last_object_clicked', 'last_object_clicked_tooltip', 'center', 'zoom',
                          'all_drawings']
    )

    # get the drawing events
    if map_data.get("all_drawings"):
        markers = [feat["geometry"]["coordinates"][::-1]
                   for feat in map_data["all_drawings"]
                   if feat["geometry"]["type"] == "Point"]
        # if we have two markers, we can create a segment
        if len(map_data.get("all_drawings")) == 2:
            # search the closest points on the GPX track to the ones entered by user
            _, idx1 = tree.query(markers[0])
            _, idx2 = tree.query(markers[1])

            i1, i2 = sorted([idx1, idx2])
            segment = gpx_points[i1:i2 + 1]
            # we had all the points in between
            # st.session_state.done_segments.append({"segment": segment})
            add_info(segment)
            # clear the marker
            map_data["all_drawings"].clear()

            st.session_state.zoom = map_data["zoom"]
            st.session_state.center = [map_data["center"]["lat"], map_data["center"]["lng"]]
