# import streamlit as st
# import pandas as pd
# import plotly.graph_objs as go
# from datetime import date
# from app_UI.config import DEFAULT_START_DATE, DEFAULT_END_DATE
# from app_UI.utils import fetch_knmi_prec_evap

# def render():
#     st.header("Instellen Meetreeksen")
#     station = st.number_input("KNMI Station Number", min_value=200, max_value=400, value=249)
#     start_date = st.date_input("Start Date", value=DEFAULT_START_DATE)
#     end_date = st.date_input("End Date", value=DEFAULT_END_DATE)

#     def date_to_str(dt):
#         return dt.strftime("%Y%m%d")

#     if st.button("Fetch and Plot KNMI Data"):
#         if start_date > end_date:
#             st.error("Start date must be before end date.")
#         else:
#             try:
#                 prec, evap = fetch_knmi_prec_evap(station, date_to_str(start_date), date_to_str(end_date))
#                 if prec.empty or evap.empty:
#                     st.error("No data returned for the selected period and station.")
#                 else:
#                     fig = go.Figure()
#                     fig.add_trace(go.Scatter(x=prec.index, y=prec.values, mode='lines', name='Precipitation (mm/day)', line=dict(color='blue')))
#                     fig.add_trace(go.Scatter(x=evap.index, y=evap.values, mode='lines', name='Evapotranspiration (mm/day)', line=dict(color='orange')))
#                     fig.update_layout(
#                         title=f"KNMI Precipitation & Evapotranspiration (Station {station})",
#                         xaxis_title="Date",
#                         yaxis_title="mm/day",
#                         legend_title="Variable",
#                         template="plotly_white"
#                     )
#                     st.plotly_chart(fig, use_container_width=True)
#             except Exception as e:
#                 st.error(f"Error fetching or plotting data: {e}")

import os
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import date
from app_UI.config import DEFAULT_START_DATE, DEFAULT_END_DATE
from app_UI.utils import fetch_knmi_prec_evap

def render():
    st.header("Bekijken Meetreeksen")

    # --- KNMI inputs -----------------------
    station    = st.number_input("KNMI Station Number", min_value=200, max_value=400, value=249)
    start_date = st.date_input("Start Date", value=DEFAULT_START_DATE)
    end_date   = st.date_input("End Date",   value=DEFAULT_END_DATE)

    # --- Observer‐series file selector -----
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    FILE_DIR = os.path.join(BASE_DIR, "input_files", "input_single")
    excel_files = [f for f in os.listdir(FILE_DIR) if f.lower().endswith(".xlsx")]

    selected_file = st.selectbox(
        "Selecteer observer‐series bestand (.xlsx):",
        options=excel_files,
        help="Kies hier je lokale .xlsx met de observer‐data."
    )

    obs_df = None
    if selected_file:
        try:
            path = os.path.join(FILE_DIR, selected_file)
            obs_df = pd.read_excel(path, parse_dates=[0], index_col=0)
            st.success(f"Loaded `{selected_file}`")
        except Exception as e:
            st.error(f"Fout bij inladen van `{selected_file}`: {e}")
            return

    # --- Fetch & Plot button --------------
    if st.button("Fetch and Plot KNMI Data"):
        if start_date > end_date:
            st.error("Start date must be before end date.")
            return

        try:
            # 1) Fetch KNMI precipitation & evaporation
            prec, evap = fetch_knmi_prec_evap(
                station,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d")
            )

            if prec.empty or evap.empty:
                st.error("No KNMI data returned for the selected period and station.")
                return

            # 2) Compute KNMI recharge
            common_idx = prec.index.intersection(evap.index)
            recharge_knmi = None
            if not common_idx.empty:
                recharge_knmi = prec.loc[common_idx] - evap.loc[common_idx]

            # 3) If observer data loaded, compute its daily mean
            obs_resampled = None
            if obs_df is not None and not obs_df.empty:
                obs_resampled = obs_df.resample("D").mean()

            # 4) Build Plotly figure
            fig = go.Figure()

            # KNMI series (left y-axis)
            fig.add_trace(go.Scatter(
                x=prec.index, y=prec.values,
                mode="lines", name="Precipitation (mm/day)",
                line=dict(color="blue")
            ))
            fig.add_trace(go.Scatter(
                x=evap.index, y=evap.values,
                mode="lines", name="Evapotranspiration (mm/day)",
                line=dict(color="orange")
            ))
            if recharge_knmi is not None:
                fig.add_trace(go.Scatter(
                    x=common_idx,
                    y=recharge_knmi.values,
                    mode="lines",
                    name="Recharge (KNMI)",
                    line=dict(color="green")
                ))

            # Observer original (secondary y-axis)
            if obs_df is not None and not obs_df.empty:
                col = obs_df.columns[0]
                fig.add_trace(go.Scatter(
                    x=obs_df.index,
                    y=obs_df[col],
                    mode="markers+lines",
                    name=f"Observer Original: {col}",
                    yaxis="y2",
                    marker=dict(symbol="circle-open"),
                    line=dict(dash="dot")
                ))

            # Observer daily mean (secondary y-axis)
            if obs_resampled is not None and not obs_resampled.empty:
                col = obs_resampled.columns[0]
                fig.add_trace(go.Scatter(
                    x=obs_resampled.index,
                    y=obs_resampled[col],
                    mode="lines",
                    name=f"Observer Daily Mean: {col}",
                    yaxis="y2",
                    line=dict(color="red", width=2)
                ))

            # 5) Layout with dual y-axes
            fig.update_layout(
                title=f"KNMI & Observer Series (Station {station})",
                xaxis=dict(title="Date"),
                yaxis=dict(title="KNMI mm/day"),
                yaxis2=dict(
                    title="Observer Values",
                    overlaying="y",
                    side="right"
                ),
                legend_title="Variable",
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error fetching or plotting data: {e}")



