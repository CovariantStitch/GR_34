import ast

import streamlit as st
from streamlit_gsheets import GSheetsConnection


def connection_gsheets():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    df["Segment"] = df["Segment"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df["Nom"] = df["Nom"].astype(str)
    df["Distance"] = df["Distance"].astype(float)
    st.session_state.gsheets_connection = conn
    st.session_state.user_data = df


def update_data_gsheets():
    st.session_state.gsheets_connection.update(data=st.session_state.user_data)
