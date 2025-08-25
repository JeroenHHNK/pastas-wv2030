import streamlit as st
from tabs.series import render as render_precipitation
from tabs.kalibratie import render as render_kalibratie
from tabs.model_vergelijkingen import render as render_model_vergelijkingen
from tabs.terugkeertijden import render as render_terugkeertijden

st.set_page_config(page_title="Pastas WV2030", layout="wide")
st.sidebar.title("Navigation")
choice = st.sidebar.radio("", [
    "Meetreeksen",
    "Model Bouwen",
    "Model Vergelijkingen",
    "Terugkeertijden en voorspellingen"
])

if choice == "Meetreeksen":
    render_precipitation()
elif choice == "Model Bouwen":
    render_kalibratie()
elif choice == "Model Vergelijkingen":
    render_model_vergelijkingen()
elif choice == "Terugkeertijden en voorspellingen":
    render_terugkeertijden()
