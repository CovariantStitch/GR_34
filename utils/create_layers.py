import pandas as pd
import streamlit as st

from utils.departments import join_segments_to_departments


@st.cache_data
def create_geojson_features(segments_: list) -> dict:
    features = []
    for i, segment_points in enumerate(segments_):
        line_coords = [[lon, lat] for lat, lon in segment_points]

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': line_coords,
            },
            'properties': {
                'style': {'weight': 5, 'opacity': 0.6}
            },
        }
        features.append(feature)
    return {'type': 'FeatureCollection', 'features': features}


def create_geojson_done(segments_: pd.DataFrame) -> dict:
    features = []
    distances_per_department = []
    for _, segment_ in segments_.iterrows():
        segment_points = segment_["Segment"]
        line_coords = [[lon, lat] for lat, lon in segment_points]

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': line_coords,
            },
            'properties': {
                'Nom': f"{segment_['Nom']}",
                'Date': f"{segment_['Date']}",
                'Distance': f"{segment_["Distance"]:.2f} km",
                'Locomotion': f"{segment_['Locomotion']}",
                'Durée': f"{segment_['Duration'] if segment_['Duration'] is not None else 'Non renseignée'}",
                'style': {'weight': 5, 'opacity': 1},
            }
        }
        features.append(feature)
        distances_per_department.append(join_segments_to_departments(segment_points, st.session_state.departments))
    distances_per_department = pd.concat(distances_per_department).groupby("nom").sum().reset_index()
    st.session_state.distances_per_department_done = distances_per_department
    return {'type': 'FeatureCollection', 'features': features}
