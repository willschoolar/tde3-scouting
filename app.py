import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# Page setup
st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

# URL to the player data
DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

# ----------------------------
# Load and clean data
# ----------------------------
@st.cache_data
def load_data():
    # Read whitespace-delimited file
    df = pd.read_csv(DATA_URL, sep=r"\s+", header=None)

    # Take only the first 13 columns
    df = df.iloc[:, :13]

    # Assign column names
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

# Convert numeric columns safely
numeric_cols = ["Age", "St", "Tk", "Ps", "Sh", "Ag", "KAb", "TAb", "PAb", "SAb"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows where Age is missing
df = df.dropna(subset=["Age"])
df["Age"] = df["Age"].astype(int)

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

# Hard-coded safe age range slider
age_min, age_max = st.sidebar.slider(
    "Age",
    min_value=15,
    max_value=40,
    value=(18, 30)
)

# Apply age filter
filtered = df[
    (df["Age"] >= age_min) &
    (df["Age"] <= age_max)
]

# ----------------------------
# Display table using AgGrid
# ----------------------------
# Reset index to remove row numbers
filtered_display = filtered.reset_index(drop=True)

# Build AgGrid options
gb = GridOptionsBuilder.from_dataframe(filtered_display)
gb.configure_default_column(resizable=True, filter=True)

# Center-align numeric columns
for col in numeric_cols:
    gb.configure_column(col, type=["numericColumn"], cellStyle={"textAlign": "center"})

# Left-align Player column
gb.configure_column("Player", cellStyle={"textAlign": "left"})

# Build grid options
gridOptions = gb.build()

# Display interactive table (browser scrolling, columns auto-fit)
row_height = 2500  # pixels per row
grid_height = min(len(filtered_display) * row_height, 2000)  # max 2000px
AgGrid(
    filtered_display,
    gridOptions=gridOptions,
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
    height=grid_height
)

