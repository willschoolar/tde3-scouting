import streamlit as st
import pandas as pd

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")
st.title("TDE3 Scouting Tool")

DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

# ----------------------------
# Load data
# ----------------------------
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

# ----------------------------
# Assign Position
# ----------------------------
def assign_position(row):
    stats = {
        "GK": row["St"],
        "DF": row["Tk"],
        "MF": row["Ps"],
        "FW": row["Sh"]
    }
    return max(stats, key=stats.get)

df["Position"] = df.apply(assign_position, axis=1)

# ----------------------------
# Init table key (forces reset)
# ----------------------------
if "table_key" not in st.session_state:
    st.session_state.table_key = 0

# ----------------------------
# Reset function
# ----------------------------
def reset_filters():
    st.session_state.club = "All"
    st.session_state.position = "All"
    for col in ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]:
        st.session_state[f"{col}_range"] = (
            int(df[col].min()),
            int(df[col].max())
        )
    # FORCE dataframe remount
    st.session_state.table_key += 1

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.header("Filters")

if st.sidebar.button("🔄 Reset all filters"):
    reset_filters()
    st.rerun()

club_options = ["All"] + sorted(df["Team"].unique())
club_input = st.sidebar.selectbox("Club", club_options, key="club")

position_input = st.sidebar.selectbox(
    "Position", ["All","GK","DF","MF","FW"], key="position"
)

stat_sliders = {}
for col in ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]:
    stat_sliders[col] = st.sidebar.slider(
        f"{col} range",
        int(df[col].min()),
        int(df[col].max()),
        (int(df[col].min()), int(df[col].max())),
        key=f"{col}_range"
    )

# 🔑 Any filter change forces table reset
st.session_state.table_key += 1

# ----------------------------
# Apply filters
# ----------------------------
filtered = df.copy()

if club_input != "All":
    filtered = filtered[filtered["Team"] == club_input]

if position_input != "All":
    filtered = filtered[filtered["Position"] == position_input]

for col, (min_val, max_val) in stat_sliders.items():
    filtered = filtered[(filtered[col] >= min_val) & (filtered[col] <= max_val)]

filtered_display = filtered.reset_index(drop=True).copy()

for col in numeric_cols:
    filtered_display[col] = filtered_display[col].astype(int)

# ----------------------------
# Sorting (team view)
# ----------------------------
position_order = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}
position_sort_map = {
    "GK": ("St","KAb"),
    "DF": ("Tk","TAb"),
    "MF": ("Ps","PAb"),
    "FW": ("Sh","SAb")
}

# --- SORTING LOGIC ---
if position_input != "All":
    # Sort ONLY by the selected position's stats
    primary, secondary = position_sort_map[position_input]
    filtered_display = (
        filtered_display
        .sort_values(by=[primary, secondary], ascending=[False, False])
        .reset_index(drop=True)
    )

elif club_input != "All":
    # Sort by position order, then relevant stats
    filtered_display["pos_order"] = filtered_display["Position"].map(position_order)
    filtered_display["primary"] = filtered_display.apply(
        lambda r: position_sort_map[r["Position"]][0], axis=1
    )
    filtered_display["primary_val"] = filtered_display.apply(
        lambda r: r[position_sort_map[r["Position"]][0]], axis=1
    )
    filtered_display["secondary_val"] = filtered_display.apply(
        lambda r: r[position_sort_map[r["Position"]][1]], axis=1
    )

    filtered_display = (
        filtered_display
        .sort_values(
            by=["pos_order", "primary_val", "secondary_val"],
            ascending=[True, False, False]
        )
        .drop(columns=["pos_order", "primary", "primary_val", "secondary_val"])
        .reset_index(drop=True)
    )


# ----------------------------
# Counts
# ----------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered_display)}")

# ----------------------------
# Styling
# ----------------------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] table { table-layout: fixed; }
div[data-testid="stDataFrame"] td,
div[data-testid="stDataFrame"] th {
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

# ----------------------------
# Display table (SORT RESET WORKS)
# ----------------------------
ROW_HEIGHT = 30
VISIBLE_ROWS = 30
TABLE_HEIGHT = ROW_HEIGHT * VISIBLE_ROWS + 50

st.dataframe(
    filtered_display,
    use_container_width=True,
    height=TABLE_HEIGHT,
    key=f"table_{st.session_state.table_key}"
)
