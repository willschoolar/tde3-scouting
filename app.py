import streamlit as st
import pandas as pd

st.set_page_config(page_title="TDE3 Scouting Tool", layout="wide")

st.title("TDE3 Scouting Tool")

DATA_URL = "https://www.tde3.co.uk/season33/all_plrs.txt"

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv(
        DATA_URL,
        header=None,
        delim_whitespace=True,
        engine="python"
    ).iloc[:, :13]

    df.columns = [
        "Team", "Player", "Age", "Nat", "St", "Tk", "Ps", "Sh",
        "Ag", "KAb", "TAb", "PAb", "SAb"
    ]

    numeric_cols = ["Age", "St", "Tk", "Ps", "Sh", "Ag",
                    "KAb", "TAb", "PAb", "SAb"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Age"])
    df["Age"] = df["Age"].astype(int)

    # Add Position based on main stat
    def get_position(r):
        stats = {"GK": r["St"], "DF": r["Tk"], "MF": r["Ps"], "FW": r["Sh"]}
        return max(stats, key=stats.get)

    df["Position"] = df.apply(get_position, axis=1)

    # Add Youth Eligible column
    def is_youth(r):
        age = r["Age"]
        pos = r["Position"]
        max_skill = 0
        if age >= 22:
            max_skill = {"GK": 19, "DF": 17, "MF": 17, "FW": 19}[pos]
        elif 19 <= age <= 21:
            max_skill = {"GK": 20, "DF": 18, "MF": 18, "FW": 20}[pos]
        else:
            max_skill = {"GK": 22, "DF": 20, "MF": 20, "FW": 22}[pos]
        main_stat = {"GK": r["St"], "DF": r["Tk"], "MF": r["Ps"], "FW": r["Sh"]}[pos]
        return main_stat <= max_skill

    df["Youth Eligible"] = df.apply(is_youth, axis=1)

    return df

df = load_data()

st.sidebar.header("Filters")

# Position filter
position = st.sidebar.selectbox("Position", ["All", "GK", "DF", "MF", "FW"])

# Club filter
clubs_in_df = sorted(df["Team"].unique())
club = st.sidebar.selectbox("Club", ["All"] + clubs_in_df)

# Include Youth / Youth Teams only
include_youth = st.sidebar.checkbox("Include Youth Teams", value=True)
youth_only = st.sidebar.checkbox("Youth Teams Only", value=False)
youth_eligible_flag = st.sidebar.checkbox("Youth Eligible Only", value=False)

# Ability sliders
stat_sliders = {}
ability_cols = ["St", "Tk", "Ps", "Sh", "KAb", "TAb", "PAb", "SAb"]
for col in ability_cols:
    min_val = int(df[col].min())
    max_val = int(df[col].max())
    step = 250 if col in ["KAb", "TAb", "PAb", "SAb"] else 1
    stat_sliders[col] = st.sidebar.slider(
        f"{col} range",
        min_value=min_val,
        max_value=max_val,
        value=(min_val, max_val),
        step=step
    )

# Shortlist multi-select
if "shortlist" not in st.session_state:
    st.session_state.shortlist = []

shortlist_options = df["Player"].tolist()
selected_shortlist = st.sidebar.multiselect(
    "Add to Shortlist",
    options=shortlist_options,
    default=st.session_state.shortlist
)
st.session_state.shortlist = selected_shortlist

show_shortlist_only = st.sidebar.checkbox("Show Shortlist Only", value=False)

# Apply filters
filtered = df.copy()

if position != "All":
    filtered = filtered[filtered["Position"] == position]

if club != "All":
    filtered = filtered[filtered["Team"] == club]

if not include_youth:
    filtered = filtered[~filtered["Team"].str.startswith("y")]

if youth_only:
    filtered = filtered[filtered["Team"].str.startswith("y")]

if youth_eligible_flag:
    filtered = filtered[filtered["Youth Eligible"]]

# Apply stat sliders
for col, (lo, hi) in stat_sliders.items():
    filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]

# Apply shortlist filter
if show_shortlist_only:
    filtered = filtered[filtered["Player"].isin(st.session_state.shortlist)]

# Default sorting: Position -> main stat -> abs -> Player
position_order = ["GK", "DF", "MF", "FW"]
position_sort = {"GK": ("St", "KAb"), "DF": ("Tk", "TAb"), "MF": ("Ps", "PAb"), "FW": ("Sh", "SAb")}

filtered["__position_rank"] = filtered["Position"].map(lambda x: position_order.index(x))
filtered["__main_stat"] = filtered.apply(lambda r: r[position_sort[r["Position"]][0]], axis=1)
filtered["__abs_stat"] = filtered.apply(lambda r: r[position_sort[r["Position"]][1]], axis=1)

filtered = filtered.sort_values(
    by=["__position_rank", "__main_stat", "__abs_stat", "Player"],
    ascending=[True, False, False, True]
).drop(columns=["__position_rank", "__main_stat", "__abs_stat"])

# Display counts
st.write(f"Players loaded: {len(df)}, Players after filters: {len(filtered)}")

# Highlight main stat column
def highlight_main_stat(df):
    pos_map = {"GK": "St", "DF": "Tk", "MF": "Ps", "FW": "Sh"}
    color_df = pd.DataFrame("", index=df.index, columns=df.columns)
    for pos, col in pos_map.items():
        mask = df["Position"] == pos
        color_df.loc[mask, col] = "background-color: #b6fcb6"  # light green
    return color_df

styled_df = filtered.style.apply(lambda _: highlight_main_stat(filtered), axis=None)

st.dataframe(styled_df, use_container_width=True)
