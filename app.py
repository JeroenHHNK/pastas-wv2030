import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
from pathlib import Path
from scripts.knmi_pull import fetch_knmi_prec_evap  # adjust if you have other fetch functions

def list_xlsx_files(folder):
    """Return a list of .xlsx files in the given folder."""
    return [f for f in os.listdir(folder) if f.endswith('.xlsx')]

@st.cache_data
def load_excel_file(filepath):
    """Load an Excel file into a DataFrame."""
    return pd.read_excel(filepath)

def tab_meetreeksen():
    st.header("Meetreeksen: Data en Visualisatie")
    folder = Path("input_files/input_single/")
    xlsx_files = list_xlsx_files(folder)
    if not xlsx_files:
        st.warning("No .xlsx files found in input_files/input_single/.")
        return
    file_choice = st.selectbox("Kies een meetreeks bestand:", xlsx_files)
    df = load_excel_file(folder / file_choice)

    # Ensure date column is datetime and get start/end before setting index
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    data_cols = df.columns[1:]
    if len(data_cols) == 0:
        st.warning("Geen datakolommen gevonden na de datumkolom.")
        return
    prec_col = data_cols[0]
    evap_col = data_cols[1] if len(data_cols) > 1 else None
    start_dt = df[date_col].min()
    end_dt = df[date_col].max()
    df = df.set_index(date_col)
    df.index = pd.to_datetime(df.index)
    df_plot = df.loc[start_dt:end_dt]

    # Fetch KNMI data
    try:
        prec_knmi, evap_knmi = fetch_knmi_prec_evap(249, start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d"))
    except Exception as e:
        st.error(f"Fout bij ophalen van KNMI data: {e}")
        prec_knmi, evap_knmi = None, None

    # Calculate recharge if possible
    recharge = (df_plot[prec_col] - df_plot[evap_col]) if evap_col else None

    # Calculate recharge from KNMI data if possible
    recharge_knmi = None
    if prec_knmi is not None and not prec_knmi.empty and evap_knmi is not None and not evap_knmi.empty:
        # Align indices to ensure subtraction is valid
        common_idx = prec_knmi.index.intersection(evap_knmi.index)
        recharge_knmi = prec_knmi.loc[common_idx].values - evap_knmi.loc[common_idx].values
        recharge_knmi_x = common_idx
    else:
        recharge_knmi_x = None

    # Plot all series in one graph
    st.subheader("Vergelijking: Bestand, KNMI en Recharge")
    bestand_name = file_choice.rsplit('.', 1)[0]
    fig_all = go.Figure()
    # Bestand Neerslag on secondary y-axis
    fig_all.add_trace(go.Scatter(x=df_plot.index, y=df_plot[prec_col], mode='lines', name=bestand_name, yaxis='y2'))
    if evap_col:
        fig_all.add_trace(go.Scatter(x=df_plot.index, y=df_plot[evap_col], mode='lines', name='Bestand Verdamping'))
    if prec_knmi is not None and not prec_knmi.empty:
        fig_all.add_trace(go.Scatter(x=prec_knmi.index, y=prec_knmi.values, mode='lines', name='KNMI Neerslag'))
    if evap_knmi is not None and not evap_knmi.empty:
        fig_all.add_trace(go.Scatter(x=evap_knmi.index, y=evap_knmi.values, mode='lines', name='KNMI Verdamping'))
    if recharge_knmi is not None:
        fig_all.add_trace(go.Scatter(x=recharge_knmi_x, y=recharge_knmi, mode='lines', name='Recharge (KNMI)'))
    # Layout with secondary y-axis
    fig_all.update_layout(
        title=f"Neerslag, Verdamping, KNMI en Recharge ({start_dt.date()} t/m {end_dt.date()})",
        xaxis_title="Datum",
        yaxis=dict(title="mm/dag (KNMI en Bestand Verdamping)", side='left'),
        yaxis2=dict(title=f"Stijghoogte ({bestand_name})", overlaying='y', side='right', showgrid=False),
        template="plotly_white"
    )
    st.plotly_chart(fig_all, use_container_width=True)

def tab_knmi():
    st.header("KNMI Precipitation & Evapotranspiration")
    from datetime import date
    station = st.number_input("KNMI Station Number", min_value=200, max_value=400, value=249)
    start_date = st.date_input("Start Date", value=date(2024, 1, 1))
    end_date = st.date_input("End Date", value=date(2024, 3, 31))

    def date_to_str(dt):
        return dt.strftime("%Y%m%d")

    if st.button("Fetch and Plot KNMI Data"):
        if start_date > end_date:
            st.error("Start date must be before end date.")
        else:
            try:
                prec, evap = fetch_knmi_prec_evap(station, date_to_str(start_date), date_to_str(end_date))
                if prec.empty or evap.empty:
                    st.error("No data returned for the selected period and station.")
                else:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=prec.index, y=prec.values, mode='lines', name='Precipitation (mm/day)', line=dict(color='blue')))
                    fig.add_trace(go.Scatter(x=evap.index, y=evap.values, mode='lines', name='Evapotranspiration (mm/day)', line=dict(color='orange')))
                    fig.update_layout(
                        title=f"KNMI Precipitation & Evapotranspiration (Station {station})",
                        xaxis_title="Date",
                        yaxis_title="mm/day",
                        legend_title="Variable",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error fetching or plotting data: {e}")

def tab_kalibratie():
    st.header("Kalibratie")
    st.info("Placeholder voor kalibratie-workflows.")

def tab_model_vergelijkingen():
    st.header("Model Vergelijkingen")
    st.info("Placeholder voor modelvergelijkingen.")

def tab_terugkeertijden():
    st.header("Terugkeertijden en voorspellingen")
    st.info("Placeholder voor terugkeertijden en voorspellingen.")

def main():
    st.set_page_config(page_title="Pastas WV2030", layout="wide")
    tabs = st.tabs([
        "Meetreeksen",
        "KNMI Data",
        "Kalibratie",
        "Model Vergelijkingen",
        "Terugkeertijden en voorspellingen"
    ])
    with tabs[0]:
        tab_meetreeksen()
    with tabs[1]:
        tab_knmi()
    with tabs[2]:
        tab_kalibratie()
    with tabs[3]:
        tab_model_vergelijkingen()
    with tabs[4]:
        tab_terugkeertijden()

if __name__ == "__main__":
    main()
