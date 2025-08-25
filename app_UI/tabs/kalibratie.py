# tabs/kalibratie.py
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import pastas as ps

# — 1) Data folders
INPUT_PREC = Path('../input_files/input_prec')
INPUT_EVAP = Path('../input_files/input_evap')
INPUT_HEAD = Path('../input_files/input_head')  # your observed heads

# — 2) Utility: list all CSVs in a folder
@st.cache_data
def list_csv_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return sorted(f for f in os.listdir(directory) if f.lower().endswith('.csv'))

# — 3) Model‐component dictionaries
recharge_models = {
    "Linear":       ps.rch.Linear(),
    "FlexModel":    ps.rch.FlexModel(),
    "Berendrecht":  ps.rch.Berendrecht()
}
response_functions = {
    "Exponential":       ps.Exponential(),
    "Gamma":             ps.Gamma(),
    "DoubleExponential": ps.DoubleExponential(),
    "Hantush":           ps.Hantush(),
    "FourParam":         ps.FourParam(),
}

def render():
   # helper to load a series from CSV
    def load_series(path: Path) -> pd.Series:
        df = pd.read_csv(path)
        df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
        return df.set_index(df.columns[0])[df.columns[1]].dropna()

    st.header("Kalibratie")

     # 1) File selectors
    col1, col2, col3 = st.columns(3)
    with col1:
        prec_files = list_csv_files(INPUT_PREC)
        sel_prec  = st.selectbox("Precipitation CSV", prec_files)
    with col2:
        evap_files = list_csv_files(INPUT_EVAP)
        sel_evap   = st.selectbox("Evaporation CSV", evap_files)
    with col3:
        head_files = list_csv_files(INPUT_HEAD)
        sel_head   = st.selectbox("Observed head CSV", head_files)

    if not (sel_prec and sel_evap and sel_head):
        st.warning("Please select all three CSV files before proceeding.")
        return

    # 2) Recharge & response selectors
    col4, col5 = st.columns(2)
    with col4:
        sel_rch = st.selectbox("Recharge model", list(recharge_models.keys()))
    with col5:
        sel_rf  = st.selectbox("Response function", list(response_functions.keys()))

    # 3) Head aggregation selector
    agg_method = st.selectbox(
        "Head series aggregation",
        ["Original", "Daily Mean", "Daily Median", "Daily Max"]
    )

    # 4) Noise toggle
    include_noise = st.checkbox("Include AR noise model")

    # 5) Plot raw inputs on demand
    if st.button("Plot input series"):
        prec_s = load_series(INPUT_PREC/sel_prec)
        evap_s = load_series(INPUT_EVAP/sel_evap)
        head_s = load_series(INPUT_HEAD/sel_head)

        # apply aggregation if needed
        if agg_method != "Original":
            head_s = head_s.resample("D").agg({
                "Daily Mean": "mean",
                "Daily Median": "median",
                "Daily Max": "max"
            }[agg_method])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prec_s.index, y=prec_s.values, mode='lines', name='Precipitation'))
        fig.add_trace(go.Scatter(x=evap_s.index, y=evap_s.values, mode='lines', name='Evaporation'))
        fig.add_trace(go.Scatter(x=head_s.index, y=head_s.values, mode='lines', name=f'Observed Head ({agg_method})'))
        fig.update_layout(
            title="Input time series",
            xaxis_title="Date",
            yaxis_title="Value"
        )
        st.plotly_chart(fig, use_container_width=True)

    # 6) Build & run model
    if st.button("Build & run model"):
        # load & optionally aggregate
        prec_s = load_series(INPUT_PREC/sel_prec)
        evap_s = load_series(INPUT_EVAP/sel_evap)
        head_s = load_series(INPUT_HEAD/sel_head)
        if agg_method != "Original":
            head_s = head_s.resample("D").agg({
                "Daily Mean": "mean",
                "Daily Median": "median",
                "Daily Max": "max"
            }[agg_method])

        # build the Pastas model
        ml = ps.Model(head_s, name="Kalibratie")
        rm = ps.RechargeModel(
            prec=prec_s,
            evap=evap_s,
            recharge=recharge_models[sel_rch],
            rfunc=response_functions[sel_rf],
            name="rch"
        )
        ml.add_stressmodel(rm)
        if include_noise:
            ml.add_noisemodel(ps.ArNoiseModel())
        ml.solve(report=True)

        # show parameters
        st.subheader("Calibration results")
        st.dataframe(ml.parameters)

        # Obs vs Sim plot
        st.subheader("Observed vs Simulated heads")
        ax1 = ml.plot()
        fig1 = ax1.get_figure()
        fig1.set_size_inches(12, 6)
        st.pyplot(fig1, dpi=200, clear_figure=True)

        # Diagnostic plots
        st.subheader("Model diagnostic plots")
        axes = ml.plots.results()
        fig2 = axes[0].get_figure()
        fig2.set_size_inches(12, 6)
        st.pyplot(fig2, dpi=200, clear_figure=True)