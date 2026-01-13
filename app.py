import streamlit as st
import pandas as pd

st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, sep=r"\s+", header=None)
    df = df.iloc[:, :13]
    df.columns = ["Team","Player","Age","Nat","St","Tk","Ps","Sh","Ag","KAb","TAb","PAb","SAb"]
    return df

df = load_data()

numeric_cols = ["Age","St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["Age"])
df["Age"] = df["Age"].astype(int)

def assign_position(row):
    stats = {"GK": row["St"], "DF": row["Tk"], "MF": row["Ps"], "FW": row["Sh"]}
    return max(stats, key=stats.get)
df["Position"] = df.apply(assign_position, axis=1)

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
position_input = st.sidebar.selectbox("Position", ["All","GK","DF","MF","FW"])

stat_sliders = {}
for col in ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]:
    min_val = int(df[col].min())
    max_val = int(df[col].max())
    stat_sliders[col] = st.sidebar.slider(f"{col} range", min_val, max_val, (min_val,max_val))

# ---------------- Apply filters ----------------
filtered = df.copy()
if position_input != "All":
    filtered = filtered[filtered["Position"] == position_input]
for col,(min_val,max_val) in stat_sliders.items():
    filtered = filtered[(filtered[col]>=min_val)&(filtered[col]<=max_val)]

# Reset index to remove row numbers
filtered_display = filtered.reset_index(drop=True).copy()
for col in numeric_cols:
    filtered_display[col] = filtered_display[col].astype(int)

# Auto-sort by position stat
position_sort_stat = {"GK":"St","DF":"Tk","MF":"Ps","FW":"Sh"}
if position_input != "All":
    sort_col = position_sort_stat[position_input]
    filtered_display = filtered_display.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

# ---------------- Display counts ----------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered_display)}")

# ---------------- Display table ----------------
st.dataframe(filtered_display, use_container_width=True)
