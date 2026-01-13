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

# Sidebar filters
st.sidebar.header("Filters")

age_min, age_max = st.sidebar.slider(
    "Age",
    int(df["Age"].min()),
    int(df["Age"].max()),
    (18, 30)
)

filtered = df[
    (df["Age"] >= age_min) &
    (df["Age"] <= age_max)
]

# Display table
st.dataframe(
    filtered,
    use_container_width=True,
    height=600
)

st.caption("Data source: tde3.co.uk – updates automatically on page load")
