import geopandas as gpd
import streamlit as st
from haversine import haversine
from shapely.geometry import LineString


@st.cache_data
def load_departments():
    departments = gpd.read_file("data/departements.geojson")
    departments = departments.to_crs(epsg=4326)
    st.session_state.departments = departments


def join_segments_to_departments(gpx_points, departments):
    segments = []
    for i in range(len(gpx_points) - 1):
        seg = LineString([gpx_points[i][::-1], gpx_points[i + 1][::-1]])
        segments.append(seg)
    gdf_segments = gpd.GeoDataFrame(geometry=segments, crs="EPSG:4326")
    joined = gpd.sjoin(gdf_segments, departments, how="left", predicate="intersects")
    joined["distance_km"] = joined.geometry.apply(lambda x: haversine(x.coords[0], x.coords[1]))
    distances = joined.groupby("nom")["distance_km"].sum().reset_index()
    return distances
