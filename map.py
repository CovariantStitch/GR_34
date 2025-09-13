import folium
import numpy as np
import streamlit as st
from folium.plugins import Draw
from scipy.spatial import cKDTree
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
import cloudinary.api

from utils.create_layers import create_geojson_done, create_geojson_features
from utils.departments import load_departments
from utils.gpx import load_and_clean_gpx
from utils.save import add_info, upload_images_to_cloudinary, save_data
from utils.gsheets import update_data_gsheets


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


def show_images(folder: str, n_images_per_row:int = 3, already_displayed: list = []):
    folder = "GR_34/" + folder
    cols = st.columns(n_images_per_row)
    images = cloudinary.api.resources(
        type="upload",
        prefix=folder,
        max_results=500
    )
    urls = [image["secure_url"] for image in images["resources"]]
    displayed = []
    n_ = 0
    for url in urls:
        if url not in already_displayed:
            cols[n_%n_images_per_row].image(url)
            n_ += 1
        displayed.append(url)
    return displayed

def start_map():
    if "departments" not in st.session_state:
        load_departments()
    segments, segment_distances, gpx_points, distances_per_department = load_and_clean_gpx('./data/gr-34-en-entier-2020.gpx')
    st.session_state.distances_per_department = distances_per_department
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
    if "user_lat" not in st.session_state:
        st.session_state.user_lat = None
    if 'user_lon' not in st.session_state:
        st.session_state.user_lon = None
    if "cloudinary" not in st.session_state:
        st.session_state.cloudinary_config = cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"]
        )
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = None

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
    if cols[1].button("Géolocalisation"):
        get_geolocation_()

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
            tooltip=folium.features.GeoJsonTooltip(fields=['Nom', 'Date', "Distance", "Locomotion", "Durée"])
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
    Draw(draw_options={
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
            add_info(segment)
            # clear the marker
            map_data["all_drawings"].clear()

            st.session_state.zoom = map_data["zoom"]
            st.session_state.center = [map_data["center"]["lat"], map_data["center"]["lng"]]

    cols_below_map = st.columns([0.4, 0.6])
    # dealing with the selection of a trace
    if map_data.get("last_object_clicked_tooltip"):
        # first, make the mapping between the trace and the corresponding row
        line = map_data.get("last_object_clicked_tooltip")
        line = [x for x in line.replace(' ', '').split("\n") if x != '']
        name = line[1]
        # get the associated line in dataframe
        df_ = st.session_state.user_data
        filter_ = df_["Nom"].apply(lambda x: x.replace(" ", "")) == name
        row = df_[filter_][["Nom", "Date", "Distance", "Duration", "Locomotion"]]
        index = row.index[0]

        # user can edit information here
        new_row = cols_below_map[0].data_editor(row, hide_index=True)
        col_button = cols_below_map[0].columns(2)
        # save button after editing information
        if col_button[0].button("Sauvegarder les modifications"):
            df_.loc[index, ["Nom", "Date", "Distance", "Duration", "Locomotion"]] = new_row.iloc[0]
            save_data(df_)
            update_data_gsheets()
        if col_button[1].button("Supprimer cette randonnée", type="primary"):
            st.session_state.user_data = st.session_state.user_data.drop(index)
            update_data_gsheets()
            st.rerun()

        # images of the trace are loaded here
        already_displayed = show_images(folder=name)
        # and the user can load new images here
        images = cols_below_map[1].file_uploader("Ajouter des images", accept_multiple_files=True,
                                                 key=st.session_state.uploader_key)
        if cols_below_map[1].button("Sauvegarder les images"):
            upload_images_to_cloudinary(images, folder=name)
            show_images(folder=name, already_displayed=already_displayed)
            st.session_state.uploader_key = None
