import streamlit as st
import os
from pathlib import Path

def render():
    st.header("Kalibratie")

    # Placeholder for future clickable map (currently a black box)
    st.markdown(
        """
        <div style="width:100%;height:200px;background:black;border-radius:8px;margin-bottom:24px;display:flex;align-items:center;justify-content:center;">
            <span style="color:white;font-size:1.2em;">[Klikbare kaart placeholder]</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # go up from tabs/ → app_UI/ → project root
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    FILE_DIR = os.path.join(BASE_DIR, "input_files", "input_single")

    xlsx_files = [f for f in os.listdir(FILE_DIR) if f.endswith(".xlsx")]
    selected_file = st.selectbox("Selecteer meetreeks bestand", xlsx_files if xlsx_files else ["Geen bestanden gevonden"])

    # Dropdown for precipitation dataset
    # (Replace with your actual list of datasets if needed)
    precipitation_options = ["KNMI", "NOAA", "Custom CSV"]
    selected_precip = st.selectbox("Selecteer neerslag dataset", precipitation_options)

    # Dropdown for evaporation dataset
    evaporation_options = ["KNMI", "FAO", "Custom CSV"]
    selected_evap = st.selectbox("Selecteer verdamping dataset", evaporation_options)