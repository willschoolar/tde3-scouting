import streamlit as st
import pandas as pd

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

# ----------------------------
# Load data
# ----------------------------
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

# ----------------------------
# Determine Position
# ----------------------------
def assign_position(row):
    stats = {"GK": row["St"], "DF": row["Tk"], "MF": row["Ps"], "FW": row["Sh"]}
    return max(stats, key=stats.get)
df["Position"] = df.apply(assign_position, axis=1)

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("Filters")

# Club filter
club_options = ["All"] + sorted(df["Team"].unique())
club_input = st.sidebar.selectbox("Club", club_options)

# Position filter
position_input = st.sidebar.selectbox("Position", ["All","GK","DF","MF","FW"])

# Stat sliders
stat_sliders = {}
for col in ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]:
    min_val = int(df[col].min())
    max_val = int(df[col].max())
    stat_sliders[col] = st.sidebar.slider(f"{col} range", min_val, max_val, (min_val,max_val))

# ----------------------------
# Apply filters
# ----------------------------
filtered = df.copy()
if club_input != "All":
    filtered = filtered[filtered["Team"] == club_input]
if position_input != "All":
    filtered = filtered[filtered["Position"] == position_input]

for col,(min_val,max_val) in stat_sliders.items():
    filtered = filtered[(filtered[col]>=min_val)&(filtered[col]<=max_val)]

# Reset index to remove row numbers
filtered_display = filtered.reset_index(drop=True).copy()
for col in numeric_cols:
    filtered_display[col] = filtered_display[col].astype(int)

# ----------------------------
# Auto-sort by position (primary + secondary)
# ----------------------------
position_sort_map = {
    "GK": ("St","KAb"),
    "DF": ("Tk","TAb"),
    "MF": ("Ps","PAb"),
    "FW": ("Sh","SAb")
}
if position_input in position_sort_map:
    primary, secondary = position_sort_map[position_input]
    filtered_display = filtered_display.sort_values(
        by=[primary, secondary], ascending=[False, False]
    ).reset_index(drop=True)

# ----------------------------
# Display counts
# ----------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered_display)}")

# ----------------------------
# Mobile-friendly CSS
# ----------------------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] table {table-layout: fixed;}
div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {text-align: center;}
div[data-testid="stDataFrame"] td:nth-child(2) {text-align: left;} /* Player left-aligned */
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Display table with dynamic height
# ----------------------------
row_height_px = 30  # pixels per row
max_height = 800    # maximum table height in px
table_height = min(max_height, len(filtered_display)*row_height_px + 50)  # add header height

st.dataframe(filtered_display, use_container_width=True, height=table_height)
