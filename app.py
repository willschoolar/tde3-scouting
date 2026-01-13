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

# Age slider
age_min, age_max = st.sidebar.slider(
    "Age",
    min_value=15,
    max_value=40,
    value=(18, 30)
)

# Apply filter
filtered = df[
    (df["Age"] >= age_min) &
    (df["Age"] <= age_max)
]

# ----------------------------
# Display counts
# ----------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered)}")

# ----------------------------
# Display table
# ----------------------------
# Reset index to remove row numbers
filtered_display = filtered.reset_index(drop=True)

# Convert numeric columns to integers for display
for col in numeric_cols:
    filtered_display[col] = filtered_display[col].astype(int)

# Show the table
st.table(filtered_display)
