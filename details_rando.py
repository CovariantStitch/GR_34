import streamlit as st

def start_details():
    st.title("Détails des randonnées")
    st.dataframe(st.session_state.user_data[["Nom", "Date", "Distance", "Locomotion", "Duration"]])
