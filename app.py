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
# Youth eligibility rules & function
# ------------------------------
YOUTH_RULES = [
    (22, 100, 19, 17, 17, 19),  # 22+
    (19, 21, 20, 18, 18, 20),   # 19-21
    (0, 18, 22, 20, 20, 22)     # 0-18
]

def is_youth_eligible(row):
    age = row["Age"]
    pos = row["Position"]
    pos_col = {"GK": "St", "DF": "Tk", "MF": "Ps", "FW": "Sh"}[pos]
    for (age_min, age_max, max_gk, max_df, max_mf, max_fw) in YOUTH_RULES:
        if age_min <= age <= age_max:
            max_skill = {"GK": max_gk, "DF": max_df, "MF": max_mf, "FW": max_fw}[pos]
            return row[pos_col] <= max_skill
    return False

# Add Youth Eligible column
df["Youth Eligible"] = df.apply(lambda r: "Yes" if is_youth_eligible(r) else "No", axis=1)

# ------------------------------
# Club mapping (abbr → full name)
# ------------------------------
raw_club_map = {
    "ars": "Arsenal", "ast": "Aston Villa", "bir": "Birmingham City", "bla": "Blackburn Rovers",
    "bol": "Bolton Wanderers", "che": "Chelsea", "der": "Derby County", "eve": "Everton",
    "ful": "Fulham", "liv": "Liverpool", "mnc": "Manchester City", "mnu": "Manchester United",
    "mid": "Middlesbrough", "new": "Newcastle United", "por": "Portsmouth", "rea": "Reading",
    "sun": "Sunderland", "tot": "Tottenham Hotspur", "whu": "West Ham United", "wig": "Wigan Athletic",
    "bur": "Burnley", "car": "Cardiff City", "cha": "Charlton Athletic", "cov": "Coventry City",
    "cry": "Crystal Palace", "hul": "Hull City", "ips": "Ipswich Town", "lei": "Leicester City",
    "nor": "Norwich City", "qpr": "Queens Park Rangers", "scu": "Scunthorpe United",
    "shu": "Sheffield United", "shw": "Sheffield Wednesday", "sou": "Southampton",
    "sto": "Stoke City", "wat": "Watford", "wba": "West Bromwich Albion",
    "wol": "Wolverhampton Wanderers", "bha": "Brighton and Hove Albion", "not": "Nottingham Forest",
    "swi": "Swindon Town", "har": "Hartlepool United", "bri": "Brighton and Hove Albion",
    "lee": "Leeds United", "swa": "Swansea City",
    "yar": "Arsenal U21s", "yas": "Aston Villa U21s", "ybi": "Birmingham City U21s", 
    "ybo": "Bournemouth U21s", "ych": "Chelsea U21s", "yco": "Coventry City U21s",
    "yev": "Everton U21s", "yhu": "Hull City U21s", "yli": "Liverpool U21s",
    "ymc": "Manchester City U21s", "ymu": "Manchester United U21s", "yne": "Newcastle United U21s",
    "ypo": "Portsmouth U21s", "ysw": "Swindon Town U21s", "yth": "Tottenham Hotspur U21s",
    "ywh": "West Ham United U21s", "ybl": "Blackburn Rovers U21s", "yca": "Cardiff City U21s",
    "ycr": "Crystal Palace U21s", "yfu": "Fulham U21s", "ymi": "Middlesbrough U21s",
    "yno": "Norwich City U21s", "yqp": "Queens Park Rangers U21s", "yre": "Reading U21s",
    "ysu": "Sheffield United U21s", "ysh": "Sheffield Wednesday U21s", "yso": "Southampton U21s",
    "yst": "Stoke City U21s", "ysn": "Sunderland U21s", "ysc": "Swansea City U21s",
    "ywi": "Wigan Athletic U21s", "ywb": "West Bromwich U21s", "ybh": "Brighton U21s",
    "ybu": "Burnley U21s", "ycn": "Charlton Athletic U21s", "yde": "Derby County U21s",
    "yha": "Hartlepool United U21s", "yip": "Ipswich Town U21s", "yle": "Leeds United U21s",
    "ylc": "Leicester City U21s", "ynf": "Nottingham Forest U21s", "ysp": "Scunthorpe United U21s",
    "ywa": "Watford U21s", "ywo": "Wolverhampton U21s", "ybr": "Brentford U21s", "ysr": "Shrewsbury Town U21s",
    "ywr": "Wrexham U21s"
}

raw_senior_to_youth = {
    "ars": ["yar"], "ast": ["yas"], "bir": ["ybi"], "bla": ["ybl"], "bol": [],
    "che": ["ych"], "der": ["yde"], "eve": ["yev"], "ful": ["yfu"], "liv": ["yli"],
    "mnc": ["ymc"], "mnu": ["ymu"], "mid": ["ymi"], "new": ["yne"], "por": ["ypo"],
    "rea": ["yre"], "sun": ["ysn"], "tot": ["yth"], "whu": ["ywh"], "wig": ["ywi"],
    "bur": ["ybu"], "car": ["yca"], "cha": ["ycn"], "cov": ["yco"], "cry": ["ycr"],
    "hul": ["yhu"], "ips": ["yip"], "lei": ["ylc"], "nor": ["yno"], "qpr": ["yqp"],
    "scu": ["ysp"], "shu": ["ysu"], "shw": ["ysh"], "sou": ["yso"], "sto": ["yst"],
    "wat": ["ywa"], "wba": ["ywb"], "wol": ["ywo"], "bha": ["ybh"], "not": ["ynf"],
    "swi": ["ysw"], "har": ["yha"], "lee": ["yle"], "swa": ["ysc"]
}

all_teams = set(df["Team"].unique())
club_map = {abbr: name for abbr, name in raw_club_map.items() if abbr in all_teams}
senior_to_youth = {sen: [y for y in youth_list if y in all_teams] 
                   for sen, youth_list in raw_senior_to_youth.items() if sen in all_teams}

# ------------------------------
# Session state helpers
# ------------------------------
STAT_COLS = ["St","Tk","Ps","Sh","KAb","TAb","PAb","SAb"]
if "table_key" not in st.session_state: st.session_state.table_key = 0
if "slider_key_version" not in st.session_state: st.session_state.slider_key_version = 0
if "prev_club" not in st.session_state: st.session_state.prev_club = "All"
if "prev_position" not in st.session_state: st.session_state.prev_position = "All"

# ------------------------------
# Sidebar Filters & Reset
# ------------------------------
st.sidebar.header("Filters")

if st.sidebar.button("Reset all filters"):
    st.session_state.club = "All"
    st.session_state.position = "All"
    st.session_state.slider_key_version += 1
    st.session_state.table_key += 1

youth_filter = st.sidebar.checkbox("Youth Teams Only")
position_input = st.sidebar.selectbox("Position", ["All","GK","DF","MF","FW"], key="position")
youth_eligible_only = st.sidebar.checkbox("Youth Eligible Only")

# Club dropdown
if youth_filter:
    available_clubs = sorted([abbr for abbr in df["Team"].unique() if abbr.startswith("y")])
else:
    available_clubs = sorted([abbr for abbr in df["Team"].unique() if not abbr.startswith("y")])

club_options = ["All"] + [club_map.get(abbr, abbr) for abbr in available_clubs]
club_input_full = st.sidebar.selectbox("Club", club_options, key="club")
include_youths = st.sidebar.checkbox("Include youth teams for selected club?", value=True)

# Reset sliders if club/position changed
if club_input_full != st.session_state.prev_club or position_input != st.session_state.prev_position:
    st.session_state.slider_key_version += 1
    st.session_state.table_key += 1
    st.session_state.prev_club = club_input_full
    st.session_state.prev_position = position_input

# ------------------------------
# Filtering logic
# ------------------------------
base_filtered = df.copy()

# Club filtering
if club_input_full == "All":
    if not include_youths:
        base_filtered = base_filtered[~base_filtered["Team"].str.startswith("y")]
else:
    club_abbr = [abbr for abbr, full in club_map.items() if full == club_input_full]
    club_abbr = club_abbr[0] if club_abbr else club_input_full
    clubs_to_include = [club_abbr]
    if include_youths and club_abbr in senior_to_youth:
        clubs_to_include += senior_to_youth[club_abbr]
    base_filtered = base_filtered[base_filtered["Team"].isin(clubs_to_include)]

# Position filter
if position_input != "All":
    base_filtered = base_filtered[base_filtered["Position"] == position_input]

# Youth Teams only
if youth_filter:
    base_filtered = base_filtered[base_filtered["Team"].str.startswith("y")]

# Youth Eligible filter
if youth_eligible_only:
    base_filtered = base_filtered[base_filtered.apply(is_youth_eligible, axis=1)]

# ------------------------------
# Stat sliders
# ------------------------------
SLIDER_RANGES = {col:(int(df[col].min()), int(df[col].max())) for col in STAT_COLS}
stat_filters = {}
for col in STAT_COLS:
    min_val, max_val = SLIDER_RANGES[col]
    step = 250 if col in ["KAb","TAb","PAb","SAb"] else 1
    slider_key = f"{col}_range_v{st.session_state.slider_key_version}"
    stat_filters[col] = st.sidebar.slider(f"{col} range", min_val, max_val, (min_val,max_val), step=step, key=slider_key)

# Apply stat filters
filtered = base_filtered.copy()
for col, (lo, hi) in stat_filters.items():
    filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]

filtered = filtered.reset_index(drop=True)
for col in numeric_cols:
    filtered[col] = filtered[col].astype(int)

# ------------------------------
# Sorting
# ------------------------------
position_sort = {"GK":("St","KAb"), "DF":("Tk","TAb"), "MF":("Ps","PAb"), "FW":("Sh","SAb")}
position_order = {"GK":0,"DF":1,"MF":2,"FW":3}

if position_input != "All":
    p,s = position_sort[position_input]
    filtered = filtered.sort_values(by=[p,s], ascending=[False,False])
elif club_input_full != "All":
    filtered["__pos"] = filtered["Position"].map(position_order)
    filtered["__main"] = filtered.apply(lambda r: r[position_sort[r["Position"]][0]], axis=1)
    filtered["__abs"] = filtered.apply(lambda r: r[position_sort[r["Position"]][1]], axis=1)
    filtered = filtered.sort_values(by=["__pos","__main","__abs"], ascending=[True,False,False])
    filtered = filtered.drop(columns=["__pos","__main","__abs"])

filtered = filtered.reset_index(drop=True)

# ------------------------------
# Counts
# ------------------------------
st.write(f"Total players loaded: {len(df)}")
st.write(f"Players after filtering: {len(filtered)}")

# ------------------------------
# Styling
# ------------------------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] table { table-layout: fixed; }
div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td { text-align: center; white-space: nowrap; }
div[data-testid="stDataFrame"] td:nth-child(2), div[data-testid="stDataFrame"] th:nth-child(2) { text-align: left; min-width: 160px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Display
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
