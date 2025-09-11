import gpxpy
import pandas as pd
import streamlit as st
from haversine import haversine

from utils.departments import join_segments_to_departments


def compute_dist(points: list) -> float:
    dist = 0
    for j in range(len(points) - 1):
        dist += haversine(points[j], points[j + 1])
    return dist


@st.cache_data
def load_and_clean_gpx(gpx_file: str, distance_threshold_km: float = 5):
    # load GPX with GR34 tracks
    with open(gpx_file, 'r') as f:
        gpx = gpxpy.parse(f)

    all_continuous_segments = []
    all_points = []
    points = []
    distances_per_department = []
    departments = st.session_state.departments

    for track in gpx.tracks:
        for segment in track.segments:
            for i, point in enumerate(segment.points):
                if len(points) > 0:
                    prev_point = points[-1]
                    dist = haversine((prev_point[0], prev_point[1]),
                                     (point.latitude, point.longitude))
                    # deal with the huge jump (island, end point far from next start point, ...)
                    if dist > distance_threshold_km:
                        if len(points) > 1:
                            distances_per_department.append(join_segments_to_departments(points, departments))
                            all_continuous_segments.append(points)
                        points = []

                points.append((point.latitude, point.longitude))
                all_points.append((point.latitude, point.longitude))

    if len(points) > 1:
        distances_per_department.append(join_segments_to_departments(points, departments))
        all_continuous_segments.append(points)

    segment_distances = []
    for seg in all_continuous_segments:
        dist = 0
        for j in range(len(seg) - 1):
            dist += haversine(seg[j], seg[j + 1])
        segment_distances.append(dist)

    distances_per_department = pd.concat(distances_per_department).groupby("nom").sum().reset_index()
    st.session_state.distances_per_department = distances_per_department
    return all_continuous_segments, segment_distances, all_points
