import streamlit as st
import pandas as pd

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

# ----------------------------
# Data URL
# ----------------------------
DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

# ----------------------------
# Load data
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, sep=r"\s+", header=None)
    df = df.iloc[:, :13]
    df.columns = [
        "Team",
        "Player",
        "Age",
        "Nat",
        "St",
        "Tk",
        "Ps",
        "Sh",
        "Ag",
        "KAb",
        "TAb",
        "PAb",
        "SAb"
    ]
    return df

df = load_data()

# Convert numeric columns
numeric_cols = ["Age", "St", "Tk", "Ps", "Sh", "Ag", "KAb", "TAb", "PAb", "SAb"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Age"])
df["Age"] = df["Age"].astype(int)

# ----------------------------
# Determine Position
# ----------------------------
def assign_position(row):
    stats = {"GK": row["St"], "DF": row["Tk"], "MF": row["Ps"], "FW": row["Sh"]}
    return max(stats, key=stats.get)

df["Position"] = df.apply(assign_position, axis=1)

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

# Age filter
age_min, age_max = st.sidebar.slider(
    "Age",
    min_value=15,
    max_value=40,
    value=(18, 30)
)

# Position filter (text input, empty = no filter)
position_input = st.sidebar.text_input(
    "Position (GK, DF, MF, FW)",
    value=""
).upper().strip()

# Stat filters (min/max text inputs)
stat_filters = {}
for col in numeric_cols:
    min_val = st.sidebar.text_input(f"{col} min", "")
    max_val = st.sidebar.text_input(f"{col} max", "")
    stat_filters[col] = (min_val, max_val)

# ----------------------------
# Apply filters
# ----------------------------
filtered = df[
    (df["Age"] >= age_min) &
    (df["Age"] <= age_max)
]

if position_input in ["GK", "DF", "MF", "FW"]:
    filtered = filtered[filtered["Position"] == position_input]

# Apply stat filters
for col, (min_val, max_val) in stat_filters.items():
    if min_val.strip():
        try:
            filtered = filtered[filtered[col] >= float(min_val)]
        except ValueError:
            pass  # ignore invalid input
    if max_val.strip():
        try:
            filtered = filtered[filtered[col] <= float(max_val)]
        except ValueError:
            pass

# ----------------------------
# Display counts
# ----------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered)}")

# ----------------------------
# Display table
# ----------------------------
filtered_display = filtered.reset_index(drop=True)

# Convert numeric columns to integers for display
for col in numeric_cols:
    filtered_display[col] = filtered_display[col].astype(int)

st.table(filtered_display)
