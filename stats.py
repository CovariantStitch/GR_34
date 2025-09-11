import pandas as pd
import plotly.express as px
import streamlit as st


def start_stats():
    st.title("Statistiques par département")

    # merge the dataframes
    df_all = st.session_state.distances_per_department
    df_done = st.session_state.distances_per_department_done.rename(columns={"distance_km": "distance_km_done"})
    df = pd.merge(df_all, df_done, on="nom", how="outer").fillna(0)
    df["distance_km_rest"] = df["distance_km"] - df["distance_km_done"]

    # show the already done repartition
    cols = st.columns(2)
    # make a plot to show the overall repartition
    fig = px.pie(df, names="nom", values="distance_km_done",
                 title="Répartition des kilomètres effectués par département")
    cols[0].plotly_chart(fig)

    fig = px.pie(df, names="nom", values="distance_km",
                 title="Répartition des kilomètres totaux par département")
    cols[1].plotly_chart(fig)

    # make the pie plots
    n_cols = 3
    cols = st.columns(n_cols)
    i_ = 0
    for _, row in df.iterrows():
        fig = px.pie(
            names=["Fait", "Restant"],
            values=[row["distance_km_done"], row["distance_km_rest"]],
            color=["Fait", "Restant"],
            color_discrete_map={"Fait": "#4C78A8", "Restant": "#A3A3A3"},
            hole=0.3,
            title=row["nom"]
        )
        fig.update_traces(textinfo="label+percent", textposition="inside")
        fig.update_layout(showlegend=False)
        cols[i_ % n_cols].plotly_chart(fig, key=f"pie_plot_stat_{i_}")
        i_ += 1
