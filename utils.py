import streamlit as st
import gpxpy
from haversine import haversine


def compute_dist(points: list) -> float:
    dist = 0
    for j in range(len(points) - 1):
        dist += haversine(points[j], points[j + 1])
    return dist

@st.cache_data
def load_and_clean_gpx(gpx_file: str, distance_threshold_km: float=5):
    with open(gpx_file, 'r') as f:
        gpx = gpxpy.parse(f)

    all_continuous_segments = []
    all_points = []
    points = []

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
                            all_continuous_segments.append(points)
                        points = []

                points.append((point.latitude, point.longitude))
                all_points.append((point.latitude, point.longitude))

    if len(points) > 1:
        all_continuous_segments.append(points)

    segment_distances = []
    for seg in all_continuous_segments:
        dist = 0
        for j in range(len(seg) - 1):
            dist += haversine(seg[j], seg[j + 1])
        segment_distances.append(dist)

    return all_continuous_segments, segment_distances, all_points