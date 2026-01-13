import streamlit as st
import pandas as pd

# ------------------------------
# Page setup
# ------------------------------
st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

# ------------------------------
# Load data
# ------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, sep=r"\s+", header=None)
    df = df.iloc[:, :13]
    df.columns = [
        "Team","Player","Age","Nat",
        "St","Tk","Ps","Sh","Ag",
        "KAb","TAb","PAb","SAb"
    ]
    return df

df = load_data()

numeric_cols = ["Age","St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Age"])
df["Age"] = df["Age"].astype(int)

# ------------------------------
# Assign Position
# ------------------------------
def assign_position(row):
    stats = {"GK": row["St"], "DF": row["Tk"], "MF": row["Ps"], "FW": row["Sh"]}
    return max(stats, key=stats.get)

df["Position"] = df.apply(assign_position, axis=1)

# ------------------------------
# Session state helpers
# ------------------------------
STAT_COLS = ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]

if "table_key" not in st.session_state:
    st.session_state.table_key = 0
if "slider_key_version" not in st.session_state:
    st.session_state.slider_key_version = 0
if "prev_club" not in st.session_state:
    st.session_state.prev_club = "All"
if "prev_position" not in st.session_state:
    st.session_state.prev_position = "All"

# ------------------------------
# Sidebar Filters & Reset
# ------------------------------
st.sidebar.header("Filters")

# Reset button
if st.sidebar.button("🔄 Reset all filters"):
    st.session_state.club = "All"
    st.session_state.position = "All"
    st.session_state.slider_key_version += 1  # Increment slider keys
    st.session_state.table_key += 1          # Increment table key to force refresh

# Club / Position filters
club_input = st.sidebar.selectbox(
    "Club",
    ["All"] + sorted(df["Team"].unique()),
    key="club"
)

position_input = st.sidebar.selectbox(
    "Position",
    ["All","GK","DF","MF","FW"],
    key="position"
)

# ------------------------------
# Compact Mobile View Toggle
# ------------------------------
compact_mobile = st.sidebar.checkbox("📱 Compact Mobile View", value=False)

# ------------------------------
# Reset sliders if Club/Position changed
# ------------------------------
if club_input != st.session_state.prev_club or position_input != st.session_state.prev_position:
    st.session_state.slider_key_version += 1
    st.session_state.table_key += 1
    st.session_state.prev_club = club_input
    st.session_state.prev_position = position_input

# ------------------------------
# Base filtering
# ------------------------------
base_filtered = df.copy()
if club_input != "All":
    base_filtered = base_filtered[base_filtered["Team"] == club_input]
if position_input != "All":
    base_filtered = base_filtered[base_filtered["Position"] == position_input]

# ------------------------------
# Slider ranges
# ------------------------------
SLIDER_RANGES = {}
for col in STAT_COLS:
    SLIDER_RANGES[col] = (int(df[col].min()), int(df[col].max()))

# ------------------------------
# Stat sliders
# ------------------------------
stat_filters = {}
for col in STAT_COLS:
    min_val, max_val = SLIDER_RANGES[col]
    step = 250 if col in ["KAb","TAb","PAb","SAb"] else 1

    # Use versioned key to force reset
    slider_key = f"{col}_range_v{st.session_state.slider_key_version}"

    stat_filters[col] = st.sidebar.slider(
        f"{col} range",
        min_val,
        max_val,
        value=(min_val, max_val),
        step=step,
        key=slider_key
    )

# ------------------------------
# Apply stat filters
# ------------------------------
filtered = base_filtered.copy()
for col, (lo, hi) in stat_filters.items():
    filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]

filtered = filtered.reset_index(drop=True)
for col in numeric_cols:
    filtered[col] = filtered[col].astype(int)

# ------------------------------
# Sorting logic
# ------------------------------
position_sort = {"GK":("St","KAb"), "DF":("Tk","TAb"), "MF":("Ps","PAb"), "FW":("Sh","SAb")}
position_order = {"GK":0, "DF":1, "MF":2, "FW":3}

if position_input != "All":
    p,s = position_sort[position_input]
    filtered = filtered.sort_values(by=[p,s], ascending=[False, False])
elif club_input != "All":
    filtered["__pos"] = filtered["Position"].map(position_order)
    filtered["__main"] = filtered.apply(lambda r: r[position_sort[r["Position"]][0]], axis=1)
    filtered["__abs"] = filtered.apply(lambda r: r[position_sort[r["Position"]][1]], axis=1)
    filtered = filtered.sort_values(by=["__pos","__main","__abs"], ascending=[True, False, False])
    filtered = filtered.drop(columns=["__pos","__main","__abs"])

filtered = filtered.reset_index(drop=True)

# ------------------------------
# Counts
# ------------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered)}")

# ------------------------------
# Table styling
# ------------------------------
if compact_mobile:
    row_height = 20  # smaller row height
    min_player_width = 120  # Player column narrower
else:
    row_height = 30
    min_player_width = 160

st.markdown(f"""
<style>
div[data-testid="stDataFrame"] table {{ table-layout: fixed; }}
div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td {{ text-align: center; white-space: nowrap; }}
div[data-testid="stDataFrame"] td:nth-child(2), div[data-testid="stDataFrame"] th:nth-child(2) {{ text-align: left; min-width: {min_player_width}px; }}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Display table
# ------------------------------
VISIBLE_ROWS = 30
TABLE_HEIGHT = row_height * VISIBLE_ROWS + 50

st.dataframe(
    filtered,
    use_container_width=True,
    height=TABLE_HEIGHT,
    key=f"table_{st.session_state.table_key}"
)

