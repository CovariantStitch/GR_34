import streamlit as st

from gsheets import connection_gsheets
from map import start_map
from details_rando import start_details

# create GSHEETS connection and load data
if "user_data" not in st.session_state:
    connection_gsheets()

st.set_page_config(
    page_title="Suivi du GR34",
    page_icon="🗺️",
    layout="wide"
)

tab_map, tab_details = st.tabs(["Carte", "Détails des randonnées"])
with tab_map:
    start_map()
with tab_details:
    start_details()
