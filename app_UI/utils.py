# Shared utility functions for app_UI
import pandas as pd
import numpy as np
import requests
from io import StringIO

def fetch_knmi_prec_evap(station: int, start_date: str, end_date: str):
    """
    Fetch KNMI daily data and compute precipitation and evapotranspiration (Hargreaves).
    """
    url = "https://www.daggegevens.knmi.nl/klimatologie/daggegevens"
    params = {
        "start": start_date,
        "end": end_date,
        "stns": str(station),
        "vars": "Q:RH:TN:TX:TG",
        "fmt": "csv"
    }
    response = requests.post(url, data=params)
    response.raise_for_status()
    csv_data = "\n".join(
        line for line in response.text.splitlines() if not line.startswith("#")
    )
    knmi_df = pd.read_csv(StringIO(csv_data), header=None)
    knmi_df.columns = ["STN", "DATE", "Q", "RH", "TN", "TX", "TG"]
    knmi_df["DATE"] = pd.to_datetime(knmi_df["DATE"], format="%Y%m%d")
    knmi_df["Q"] = knmi_df["Q"] * 0.01
    knmi_df["RH"] = knmi_df["RH"] / 10.0
    knmi_df["TN"] = knmi_df["TN"] / 10.0
    knmi_df["TX"] = knmi_df["TX"] / 10.0
    knmi_df["TG"] = knmi_df["TG"] / 10.0
    knmi_df.rename(columns={
        "Q": "Radiation",
        "RH": "Precipitation",
        "TN": "Tmin",
        "TX": "Tmax",
        "TG": "Tavg"
    }, inplace=True)
    def hargreaves_pet(row):
        t_avg, t_max, t_min, ra = row["Tavg"], row["Tmax"], row["Tmin"], row["Radiation"]
        if np.isnan(t_avg) or np.isnan(t_max) or np.isnan(t_min) or np.isnan(ra):
            return np.nan
        return 0.0023 * (t_avg + 17.8) * np.sqrt(t_max - t_min) * ra
    knmi_df["ET"] = knmi_df.apply(hargreaves_pet, axis=1)
    knmi_df = knmi_df.set_index("DATE")
    prec = (knmi_df['Precipitation']).astype(float)
    evap = (knmi_df['ET']).astype(float)
    return prec, evap
