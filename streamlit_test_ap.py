import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Electricity Production", layout="wide")

# Fixed color per source, so filtering never changes a source's color
SOURCE_COLORS = {
    "Solar": "#E69F00",
    "Wind": "#0072B2",
    "Hydro": "#009E73",
    "Natural Gas": "#CC79A7",
    "Nuclear": "#56B4E9",
}


@st.cache_data
def make_dummy_data(days: int = 90, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hours = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days * 24, freq="h")
    hour_of_day = hours.hour.to_numpy()
    day_idx = np.arange(len(hours)) / 24

    # Solar follows a daylight curve, zero at night
    solar = np.clip(np.sin((hour_of_day - 6) / 12 * np.pi), 0, None) * 120
    solar *= rng.uniform(0.6, 1.0, len(hours))
    # Wind is noisy with slow multi-day swings
    wind = 60 + 35 * np.sin(day_idx / 5) + rng.normal(0, 12, len(hours))
    # Hydro is fairly steady with a seasonal drift
    hydro = 50 + 10 * np.sin(day_idx / 30) + rng.normal(0, 3, len(hours))
    # Gas ramps up in the evening peak
    gas = 80 + 50 * np.exp(-((hour_of_day - 19) ** 2) / 8) + rng.normal(0, 8, len(hours))
    # Nuclear is baseload
    nuclear = 150 + rng.normal(0, 2, len(hours))

    df = pd.DataFrame(
        {
            "timestamp": hours,
            "Solar": solar,
            "Wind": np.clip(wind, 0, None),
            "Hydro": hydro,
            "Natural Gas": gas,
            "Nuclear": nuclear,
        }
    )
    return df.round(1)


df = make_dummy_data()

# --- Sidebar filters ---
st.sidebar.header("Filters")
min_date, max_date = df["timestamp"].min().date(), df["timestamp"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(max_date - pd.Timedelta(days=30), max_date),
    min_value=min_date,
    max_value=max_date,
)
sources = st.sidebar.multiselect(
    "Sources", list(SOURCE_COLORS), default=list(SOURCE_COLORS)
)
resolution = st.sidebar.radio("Resolution", ["Hourly", "Daily"], index=1)

if len(date_range) != 2 or not sources:
    st.info("Pick a start and end date and at least one source.")
    st.stop()

start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
filtered = df[(df["timestamp"] >= start) & (df["timestamp"] < end)].set_index("timestamp")[sources]

if resolution == "Daily":
    # MW averaged over an hour = MWh, so summing hourly values gives daily MWh
    chart_df = filtered.resample("D").sum()
    unit = "MWh / day"
else:
    chart_df = filtered
    unit = "MW"

# --- Header & KPIs ---
st.title("⚡ Electricity Production Dashboard")
st.caption("Dummy data, generated for demo purposes only")

total_mwh = filtered.sum().sum()
peak_mw = filtered.sum(axis=1).max()
renewables = [s for s in ["Solar", "Wind", "Hydro"] if s in sources]
renewable_share = filtered[renewables].sum().sum() / total_mwh * 100 if renewables else 0
top_source = filtered.sum().idxmax()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total energy", f"{total_mwh / 1000:,.1f} GWh")
c2.metric("Peak output", f"{peak_mw:,.0f} MW")
c3.metric("Renewable share", f"{renewable_share:.1f}%")
c4.metric("Top source", top_source)

# --- Charts ---
colors = [SOURCE_COLORS[s] for s in sources]

st.subheader(f"Production by source ({unit})")
st.area_chart(chart_df, color=colors, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Total energy by source (MWh)")
    totals = filtered.sum().sort_values(ascending=False).to_frame("MWh")
    st.bar_chart(totals, horizontal=True, use_container_width=True)
with right:
    st.subheader("Average output by hour of day (MW)")
    hourly_profile = filtered.groupby(filtered.index.hour).mean()
    hourly_profile.index.name = "Hour"
    st.line_chart(hourly_profile, color=colors, use_container_width=True)

# --- Raw data ---
with st.expander("Show data table"):
    st.dataframe(chart_df.round(1), use_container_width=True)
    st.download_button(
        "Download CSV", chart_df.to_csv().encode(), "production_data.csv", "text/csv"
    )