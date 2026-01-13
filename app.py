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
numeric_cols = ["Age", "St", "Tk", "Ps", "Sh", "Ag",
                "KAb", "TAb", "PAb", "SAb"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows where Age is missing
df = df.dropna(subset=["Age"])

# Ensure Age is integer
df["Age"] = df["Age"].astype(int)

# Sidebar filters
st.sidebar.header("Filters")

# HARD-CODED safe age range
age_min, age_max = st.sidebar.slider(
    "Age",
    min_value=15,
    max_value=40,
    value=(18, 30)
)

filtered = df[
    (df["Age"] >= age_min) &
    (df["Age"] <= age_max)
]

st.write("Total players loaded:", len(df))
st.write("Players after filtering:", len(filtered))

st.dataframe(
    filtered,
    use_container_width=True,
    height=600
)
