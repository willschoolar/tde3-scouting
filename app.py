import streamlit as st
import pandas as pd

st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")

st.title("TDE3 Scouting Tool")

DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

@st.cache_data
def load_data():
    df = pd.read_csv(
        DATA_URL,
        sep=r"\s+",
        header=None
    )
    df = df.iloc[:, :13]
    df.columns = [
        "Team", "Age", "Nat", "St", "Tk", "Ps", "Sh",
        "Ag", "KAb", "TAb", "PAb", "SAb", "X"
    ]
    return df

df = load_data()

# Convert numeric columns safely
numeric_cols = ["Age", "St", "Tk", "Ps", "Sh", "Ag",
                "KAb", "TAb", "PAb", "SAb"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows where Age is missing or invalid
df = df.dropna(subset=["Age"])

# Ensure Age is integer
df["Age"] = df["Age"].astype(int)

# Sidebar filters
st.sidebar.header("Filters")

age_min_value = int(df["Age"].min())
age_max_value = int(df["Age"].max())

# Safe default values
default_min = max(18, age_min_value)
default_max = min(30, age_max_value)

age_min, age_max = st.sidebar.slider(
    "Age",
    age_min_value,
    age_max_value,
    (default_min, default_max)
)

filtered = df[
    (df["Age"] >= age_min) &
    (df["Age"] <= age_max)
]
