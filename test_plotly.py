import streamlit as st
import plotly.graph_objs as go

fig = go.Figure()
fig.add_scatter(y=[2, 1, 4, 3])

st.plotly_chart(fig, use_container_width=True)