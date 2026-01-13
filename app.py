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
# Sorting
# ----------------------------
position_order = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}
position_sort_map = {
    "GK": ("St","KAb"),
    "DF": ("Tk","TAb"),
    "MF": ("Ps","PAb"),
    "FW": ("Sh","SAb")
}

if club_input != "All":
    # Add position order
    filtered_display["pos_order"] = filtered_display["Position"].map(position_order)
    # Add primary & secondary for sorting
    filtered_display["primary"] = filtered_display.apply(lambda r: r[position_sort_map[r["Position"]][0]], axis=1)
    filtered_display["secondary"] = filtered_display.apply(lambda r: r[position_sort_map[r["Position"]][1]], axis=1)
    # Sort: position order, then primary desc, then secondary desc
    filtered_display = filtered_display.sort_values(
        by=["pos_order","primary","secondary"],
        ascending=[True, False, False]
    ).drop(columns=["pos_order","primary","secondary"]).reset_index(drop=True)

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
div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {text-align: center; white-space: nowrap;}
div[data-testid="stDataFrame"] td:nth-child(2), div[data-testid="stDataFrame"] th:nth-child(2) {
    text-align: left; min-width: 150px;  /* Player column fixed width to avoid wrapping */
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Display table with dynamic height
# ----------------------------
row_height_px = 30
num_rows_to_show = 30
max_height = row_height_px*num_rows_to_show + 50  # 30 rows + header

st.dataframe(filtered_display, use_container_width=True, height=max_height)
