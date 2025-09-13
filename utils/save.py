import cloudinary.uploader
import pandas as pd
import streamlit as st
from PIL import Image
import io

from utils.gpx import compute_dist
from utils.gsheets import update_data_gsheets


def resize_image(uploaded_file, max_width=1024, max_height=1024, quality=85):
    image = Image.open(uploaded_file)

    image.thumbnail((max_width, max_height))

    buffer = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffer, format="JPEG", quality=int(quality))
    buffer.seek(0)
    return buffer


max_size_cloudinary = 10_485_760
def upload_images_to_cloudinary(files: list, folder: str) -> list[str]:
    urls = []
    if "GR_34" not in folder:
        folder = "GR_34/" + folder
    for file in files:
        # check the size of the file
        file.seek(0, 2) # just go to the end of the file
        size_bytes = file.tell() # get the size
        file.seek(0)
        if size_bytes > max_size_cloudinary:
            print(f"File size above {max_size_cloudinary} -> start compression")
            # compress the image
            file = resize_image(file, quality=size_bytes / max_size_cloudinary * 100. * 0.9)

        result = cloudinary.uploader.upload(file, folder=folder)
        urls.append(result["secure_url"])
    return urls


def save_data(df_: pd.DataFrame):
    st.session_state.user_data = pd.concat([st.session_state.user_data, df_])


@st.dialog("Ajouter des info")
def add_info(segment_: list):
    distance = compute_dist(segment_)
    st.write(f"Randonnée de {distance} km")
    name = st.text_input(label="Nom de la randonnée")
    date = st.date_input(label="Date de la rando")
    locomotion = st.radio(label="Moyen de locomotion", options=["🦶", "🚲"])
    duration = st.time_input(label="Durée (optionnel)", value=None)
    # add images and save urls
    images = st.file_uploader("Ajouter des images pour cette randonnée")
    upload_images_to_cloudinary(files=images, folder=name.replace(" ", ""))
    # convert to dataframe
    df_ = pd.DataFrame.from_records([{"Nom": name, "Date": date, "Locomotion": locomotion, "Duration": duration,
                                      "Distance": distance, "Segment": segment_}, ])

    if st.button("Valider"):
        save_data(df_)
        update_data_gsheets()
        st.rerun()
