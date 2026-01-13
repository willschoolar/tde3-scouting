import streamlit as st
import pandas as pd

# --------------------------------------------------
# Page setup
# --------------------------------------------------
st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

# --------------------------------------------------
# Load data
# --------------------------------------------------
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

# --------------------------------------------------
# Assign Position
# --------------------------------------------------
def assign_position(row):
    stats = {
        "GK": row["St"],
        "DF": row["Tk"],
        "MF": row["Ps"],
        "FW": row["Sh"]
    }
    return max(stats, key=stats.get)

df["Position"] = df.apply(assign_position, axis=1)

# --------------------------------------------------
# Reset logic
# --------------------------------------------------
def reset_filters():
    st.session_state.club = "All"
    st.session_state.position = "All"
    for col in ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]:
        st.session_state.pop(f"{col}_range", None)
    st.session_state.table_key += 1

if "table_key" not in st.session_state:
    st.session_state.table_key = 0

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.header("Filters")

if st.sidebar.button("🔄 Reset all filters"):
    reset_filters()
    st.rerun()

club_options = ["All"] + sorted(df["Team"].unique())
club_input = st.sidebar.selectbox("Club", club_options, key="club")

position_input = st.sidebar.selectbox(
    "Position", ["All","GK","DF","MF","FW"], key="position"
)

# --------------------------------------------------
# Base filtering (Club + Position only)
# --------------------------------------------------
base_filtered = df.copy()

if club_input != "All":
    base_filtered = base_filtered[base_filtered["Team"] == club_input]

if position_input != "All":
    base_filtered = base_filtered[base_filtered["Position"] == position_input]

# --------------------------------------------------
# Dynamic sliders (SAFE)
# --------------------------------------------------
stat_sliders = {}

for col in ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]:
    min_val = int(base_filtered[col].min())
    max_val = int(base_filtered[col].max())

    # Initialize once
    if f"{col}_range" not in st.session_state:
        st.session_state[f"{col}_range"] = (min_val, max_val)

    # Clamp values
    cur_min, cur_max = st.session_state[f"{col}_range"]
    cur_min = max(min_val, cur_min)
    cur_max = min(max_val, cur_max)
    st.session_state[f"{col}_range"] = (cur_min, cur_max)

    if min_val == max_val:
        st.sidebar.slider(
            f"{col} range",
            min_val,
            max_val,
            disabled=True,
            key=f"{col}_range"
        )
        stat_sliders[col] = (min_val, max_val)
    else:
        stat_sliders[col] = st.sidebar.slider(
            f"{col} range",
            min_val,
            max_val,
            key=f"{col}_range"
        )

# Force table remount when filters change
st.session_state.table_key += 1

# --------------------------------------------------
# Apply stat filters
# --------------------------------------------------
filtered = base_filtered.copy()

for col, (lo, hi) in stat_sliders.items():
    filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]

filtered_display = filtered.reset_index(drop=True).copy()

for col in numeric_cols:
    filtered_display[col] = filtered_display[col].astype(int)

# --------------------------------------------------
# Sorting logic
# --------------------------------------------------
position_sort = {
    "GK": ("St","KAb"),
    "DF": ("Tk","TAb"),
    "MF": ("Ps","PAb"),
    "FW": ("Sh","SAb")
}
pos_order = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}

if position_input != "All":
    p, s = position_sort[position_input]
    filtered_display = filtered_display.sort_values(
        by=[p, s], ascending=[False, False]
    )
elif club_input != "All":
    filtered_display["__pos"] = filtered_display["Position"].map(pos_order)
    filtered_display["__main"] = filtered_display.apply(
        lambda r: position_sort[r["Position"]][0], axis=1
    )
    filtered_display["__val"] = filtered_display.apply(
        lambda r: r[position_sort[r["Position"]][0]], axis=1
    )
    filtered_display["__ab"] = filtered_display.apply(
        lambda r: r[position_sort[r["Position"]][1]], axis=1
    )

    filtered_display = (
        filtered_display
        .sort_values(
            by=["__pos","__val","__ab"],
            ascending=[True, False, False]
        )
        .drop(columns=["__pos","__main","__val","__ab"])
    )

filtered_display = filtered_display.reset_index(drop=True)

# --------------------------------------------------
# Counts
# --------------------------------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered_display)}")

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] table {
    table-layout: fixed;
}
div[data-testid="stDataFrame"] th,
div[data-testid="stDataFrame"] td {
    text-align: center;
    white-space: nowrap;
}
div[data-testid="stDataFrame"] td:nth-child(2),
div[data-testid="stDataFrame"] th:nth-child(2) {
    text-align: left;
    min-width: 160px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Display table
# --------------------------------------------------
ROW_HEIGHT = 30
VISIBLE_ROWS = 30
TABLE_HEIGHT = ROW_HEIGHT * VISIBLE_ROWS + 50

st.dataframe(
    filtered_display,
    use_container_width=True,
    height=TABLE_HEIGHT,
    key=f"table_{st.session_state.table_key}"
)
