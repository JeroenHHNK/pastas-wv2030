import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date
from app_UI.config import DEFAULT_START_DATE, DEFAULT_END_DATE

def fetch_knmi_meetreeksen_series():
    url = "https://api.dataplatform.knmi.nl/open-data/v1/datasets/Actuele10mindataKNMIstations/versions/2.0/series"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [
            {"label": s.get("name", s.get("id", str(i))), "value": s.get("id", str(i))}
            for i, s in enumerate(data.get("series", []))
        ]
    except Exception as e:
        st.error(f"Fout bij ophalen van KNMI meetreeksen: {e}")
        return []

def fetch_knmi_meetreeks_data(series_id, start, end):
    url = f"https://api.dataplatform.knmi.nl/open-data/v1/datasets/Actuele10mindataKNMIstations/versions/2.0/data?seriesId={series_id}&start={start}&end={end}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data.get("values", []))
        if not df.empty and "timestamp" in df.columns and "value" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        return df
    except Exception as e:
        st.error(f"Fout bij ophalen van meetreeks data: {e}")
        return pd.DataFrame()

def render():
    st.header("Meetreeksen")
    series_options = fetch_knmi_meetreeksen_series()
    if not series_options:
        st.warning("Geen KNMI meetreeksen gevonden.")
        return
    selected = st.selectbox("Kies een meetreeks:", [o["label"] for o in series_options])
    selected_id = next((o["value"] for o in series_options if o["label"] == selected), None)
    start_date = st.date_input("Startdatum", value=DEFAULT_START_DATE)
    end_date = st.date_input("Einddatum", value=DEFAULT_END_DATE)
    if st.button("Toon meetreeks"):
        if start_date > end_date:
            st.error("Startdatum moet voor de einddatum liggen.")
            return
        start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
        end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
        df = fetch_knmi_meetreeks_data(selected_id, start_str, end_str)
        if df is not None and not df.empty and "value" in df.columns:
            fig = px.line(df, x=df.index, y="value", title=f"KNMI Meetreeks: {selected}")
            fig.update_layout(
                xaxis_title="Datum",
                yaxis_title="Waarde",
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Geen data gevonden voor deze selectie.")
