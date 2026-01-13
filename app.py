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
if "prev_club" not in st.session_state:
    st.session_state.prev_club = "All"
if "prev_position" not in st.session_state:
    st.session_state.prev_position = "All"
if "reset_filters" not in st.session_state:
    st.session_state.reset_filters = False

# ------------------------------
# Sidebar Filters & Reset
# ------------------------------
st.sidebar.header("Filters")

# Reset button
if st.sidebar.button("🔄 Reset all filters"):
    st.session_state.club = "All"
    st.session_state.position = "All"
    st.session_state.reset_filters = True
    st.session_state.table_key += 1

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
# Clear sliders if filter changed
# ------------------------------
if club_input != st.session_state.prev_club or position_input != st.session_state.prev_position:
    st.session_state.reset_filters = True
    st.session_state.prev_club = club_input
    st.session_state.prev_position = position_input
    st.session_state.table_key += 1

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

    # Use reset flag to force default values
    default_val = (min_val, max_val) if st.session_state.reset_filters else st.session_state.get(f"{col}_range", (min_val, max_val))

    stat_filters[col] = st.sidebar.slider(
        f"{col} range",
        min_val,
        max_val,
        value=default_val,
        step=step,
        key=f"{col}_range"
    )

# Clear reset flag after sliders are drawn
st.session_state.reset_filters = False

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
st.markdown("""
<style>
div[data-testid="stDataFrame"] table { table-layout: fixed; }
div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td { text-align: center; white-space: nowrap; }
div[data-testid="stDataFrame"] td:nth-child(2), div[data-testid="stDataFrame"] th:nth-child(2) { text-align: left; min-width: 160px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Display table
# ------------------------------
ROW_HEIGHT = 30
VISIBLE_ROWS = 30
TABLE_HEIGHT = ROW_HEIGHT * VISIBLE_ROWS + 50

st.dataframe(
    filtered,
    use_container_width=True,
    height=TABLE_HEIGHT,
    key=f"table_{st.session_state.table_key}"
)
