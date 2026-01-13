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
numeric_cols = ["Age", "St", "Tk", "Ps", "Sh", "KAb", "TAb", "PAb", "SAb"]
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

# Position dropdown
position_input = st.sidebar.selectbox(
    "Position",
    ["All", "GK", "DF", "MF", "FW"]
)

# Stat sliders
stat_sliders = {}
for col in numeric_cols:
    min_val = int(df[col].min())
    max_val = int(df[col].max())
    stat_sliders[col] = st.sidebar.slider(
        f"{col} range",
        min_val,
        max_val,
        (min_val, max_val)
    )

# ----------------------------
# Apply filters
# ----------------------------
filtered = df.copy()

# Position filter
if position_input != "All":
    filtered = filtered[filtered["Position"] == position_input]

# Stat sliders filter
for col, (min_val, max_val) in stat_sliders.items():
    filtered = filtered[(filtered[col] >= min_val) & (filtered[col] <= max_val)]

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
