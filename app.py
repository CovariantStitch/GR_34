import streamlit as st

from utils.gsheets import connection_gsheets
from map import start_map
from details_rando import start_details
from stats import start_stats


# create GSHEETS connection and load data
if "user_data" not in st.session_state:
    connection_gsheets()

st.set_page_config(
    page_title="Suivi du GR34",
    page_icon="🗺️",
    layout="wide"
)

tab_map, tab_details, tab_stats = st.tabs(["Carte", "Détails des randonnées", "Stats par département"])
with tab_map:
    start_map()
with tab_details:
    start_details()
with tab_stats:
    start_stats()
