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
# Club mapping (abbr → full name)
# ------------------------------
club_map = {
    "ars": "Arsenal",
    "liv": "Liverpool",
    "mci": "Manchester City",
    "che": "Chelsea",
    "tot": "Tottenham",
    "man": "Manchester United",
    "eve": "Everton",
    # Add all your club mappings here
}

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
    st.session_state.slider_key_version += 1
    st.session_state.table_key += 1

# Club dropdown using full names
club_options = ["All"] + [club_map[abbr] for abbr in sorted(club_map)]
club_input_full = st.sidebar.selectbox("Club", club_options, key="club")

# Convert back to abbreviation for filtering
if club_input_full == "All":
    club_abbr = "All"
else:
    club_abbr = [abbr for abbr, full in club_map.items() if full == club_input_full][0]

# Position filter
position_input = st.sidebar.selectbox(
    "Position",
    ["All","GK","DF","MF","FW"],
    key="position"
)

# Youth-only filter
youth_filter = st.sidebar.checkbox("Youth Teams Only")

# Reset sliders if Club/Position changed
if club_input_full != st.session_state.prev_club or position_input != st.session_state.prev_position:
    st.session_state.slider_key_version += 1
    st.session_state.table_key += 1
    st.session_state.prev_club = club_input_full
    st.session_state.prev_position = position_input

# ------------------------------
# Base filtering
# ------------------------------
base_filtered = df.copy()

# Club filter
if club_abbr != "All":
    base_filtered = base_filtered[base_filtered["Team"] == club_abbr]

# Position filter
if position_input != "All":
    base_filtered = base_filtered[base_filtered["Position"] == position_input]

# Youth filter
if youth_filter:
    base_filtered = base_filtered[base_filtered["Team"].str.startswith("y")]

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
elif club_abbr != "All":
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
