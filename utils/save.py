import pandas as pd
import streamlit as st

from utils.gsheets import update_data_gsheets
from utils.gpx import compute_dist


def save_data(df_: pd.DataFrame):
    st.session_state.user_data = pd.concat([st.session_state.user_data, df_])

@st.dialog("Ajouter des info")
def add_info(segment_: list):
    date = st.date_input(label="Date de la rando")
    locomotion = st.radio(label="Moyen de locomotion", options=["🦶", "🚲"])
    duration = st.time_input(label="Duree (optionnel)", value=None)
    df_ = pd.DataFrame.from_records([{"Date": date, "Locomotion": locomotion, "Duration": duration,
                                      "Distance": compute_dist(segment_),
                                      "Segment": segment_}])

    if st.button("Valider"):
        save_data(df_)
        update_data_gsheets()
        st.rerun()
