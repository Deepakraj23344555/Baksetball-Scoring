import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Court Command | Pro Scorer", page_icon="🏀", layout="wide")

# --- CUSTOM CSS FOR "PRO" LOOK ---
# This CSS tightens the buttons and makes the scoreboard look like an LED display
st.markdown("""
    <style>
    div.stButton > button {
        padding: 0px 10px;
        font-size: 12px;
        height: 35px;
        width: 100%;
        border-radius: 4px;
    }
    .player-name {
        font-size: 16px;
        font-weight: bold;
        padding-top: 8px;
    }
    .score-display {
        font-family: 'Courier New', monospace;
        background-color: #000;
        color: #0f0;
        font-size: 40px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'game_log' not in st.session_state:
    st.session_state.game_log = []
if 'teams' not in st.session_state:
    st.session_state.teams = {"Home": "Warriors", "Away": "Lakers"}
if 'roster' not in st.session_state:
    # Structure: {'Home': [{'name': 'Curry', 'stats': {...}}, ...], 'Away': ...}
    st.session_state.roster = {"Home": [], "Away": []}

# --- STATS ENGINE ---
STATS_TEMPLATE = {
    "PTS": 0, "FG": 0, "3PT": 0, "FT": 0,
    "REB": 0, "AST": 0, "STL": 0, "BLK": 0, 
    "TO": 0, "PF": 0
}

def update_stat(team, player_idx, stat_type, points=0):
    # 1. Update Player Stats
    player = st.session_state.roster[team][player_idx]
    
    if stat_type in ["FG", "3PT", "FT"]:
        player['stats'][stat_type] += 1
        player['stats']['PTS'] += points
    else:
        player['stats'][stat_type] += 1
        
    # 2. Log Event
    timestamp = datetime.now().strftime("%H:%M:%S")
    event_desc = f"{stat_type} ({points}pts)" if points > 0 else stat_type
    
    log_entry = {
        "Time": timestamp,
        "Team": st.session_state.teams[team],
        "Player": player['name'],
        "Event": event_desc,
        "Score": get_score_string()
    }
    st.session_state.game_log.insert(0, log_entry)
    st.toast(f"{player['name']} - {event_desc}")

def get_team_score(team_key):
    total = 0
    for p in st.session_state.roster[team_key]:
        total += p['stats']['PTS']
    return total

def get_score_string():
    h = get_team_score("Home")
    a = get_team_score("Away")
    return f"{h} - {a}"

# --- PAGE 1: SETUP ---
def render_setup():
    st.title("📋 Game Setup")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Home Team")
        home_name = st.text_input("Home Team Name", "Home Team")
        # Text area for bulk entry
        home_roster_input = st.text_area("Home Roster (One name per line)", "Player 1\nPlayer 2\nPlayer 3\nPlayer 4\nPlayer 5")
    
    with c2:
        st.subheader("Away Team")
        away_name = st.text_input("Away Team Name", "Away Team")
        away_roster_input = st.text_area("Away Roster (One name per line)", "Opponent A\nOpponent B\nOpponent C\nOpponent D\nOpponent E")

    if st.button("🚀 Lock In Rosters & Start Game", type="primary"):
        # Process Rosters
        st.session_state.teams["Home"] = home_name
        st.session_state.teams["Away"] = away_name
        
        # Parse text area into list
        h_list = [x.strip() for x in home_roster_input.split('\n') if x.strip()]
        a_list = [x.strip() for x in away_roster_input.split('\n') if x.strip()]
        
        # Initialize Player Objects
        st.session_state.roster["Home"] = [{'name': name, 'stats': STATS_TEMPLATE.copy()} for name in h_list]
        st.session_state.roster["Away"] = [{'name': name, 'stats': STATS_TEMPLATE.copy()} for name in a_list]
        
        st.session_state.game_started = True
        st.rerun()

# --- PAGE 2: LIVE GAME ---
def render_game():
    # --- SCOREBOARD HEADER ---
    h_score = get_team_score("Home")
    a_score = get_team_score("Away")
    
    sc1, sc2, sc3 = st.columns([2,1,2])
    with sc1:
        st.markdown(f"<h3 style='text-align:center'>{st.session_state.teams['Home']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='score-display'>{h_score}</div>", unsafe_allow_html=True)
    with sc2:
        st.markdown("<h4 style='text-align:center; padding-top:20px'>VS</h4>", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"<h3 style='text-align:center'>{st.session_state.teams['Away']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='score-display'>{a_score}</div>", unsafe_allow_html=True)
    
    st.divider()

    # --- MAIN CONTROLS (TABS) ---
    tab_home, tab_away, tab_box, tab_log = st.tabs([
        f"🏠 {st.session_state.teams['Home']} Controls", 
        f"✈️ {st.session_state.teams['Away']} Controls", 
        "📊 Live Box Score",
        "📝 Play-by-Play"
    ])
    
    # HELPER TO RENDER PLAYER ROWS
    def render_player_rows(team_key):
        # Header Row
        h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
        h1.markdown("**Player**")
        h2.markdown("**+1**")
        h3.markdown("**+2**")
        h4.markdown("**+3**")
        h5.markdown("**REB**")
        h6.markdown("**AST**")
        h7.markdown("**STL**")
        h8.markdown("**BLK**")
        h9.markdown("**PF**") # Personal Foul
        
        # Player Rows
        for idx, player in enumerate(st.session_state.roster[team_key]):
            c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
            
            with c1: st.markdown(f"<div class='player-name'>{player['name']}</div>", unsafe_allow_html=True)
            
            # Action Buttons - using unique keys for every single button
            uid = f"{team_key}_{idx}"
            if c2.button("FT", key=f"{uid}_ft"): update_stat(team_key, idx, "FT", 1)
            if c3.button("2P", key=f"{uid}_2p"): update_stat(team_key, idx, "FG", 2)
            if c4.button("3P", key=f"{uid}_3p"): update_stat(team_key, idx, "3PT", 3)
            if c5.button("RB", key=f"{uid}_reb"): update_stat(team_key, idx, "REB")
            if c6.button("AS", key=f"{uid}_ast"): update_stat(team_key, idx, "AST")
            if c7.button("ST", key=f"{uid}_stl"): update_stat(team_key, idx, "STL")
            if c8.button("BL", key=f"{uid}_blk"): update_stat(team_key, idx, "BLK")
            if c9.button("PF", key=f"{uid}_pf"): update_stat(team_key, idx, "PF")
            
            # Optional: Add TO (Turnover) in a separate line or dropdown if needed, but this covers 90%
            
    with tab_home:
        render_player_rows("Home")
        
    with tab_away:
        render_player_rows("Away")

    with tab_box:
        st.subheader("Combined Box Score")
        # Flatten data for DataFrame
        box_data = []
        for team in ["Home", "Away"]:
            team_name = st.session_state.teams[team]
            for p in st.session_state.roster[team]:
                row = p['stats'].copy()
                row['Player'] = p['name']
                row['Team'] = team_name
                box_data.append(row)
        
        if box_data:
            df = pd.DataFrame(box_data)
            # Reorder columns
            cols = ['Team', 'Player', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'PF', 'FG', '3PT', 'FT']
            st.dataframe(df[cols], use_container_width=True, height=500)
            
            # CSV Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Box Score CSV", csv, "box_score.csv", "text/csv")
            
    with tab_log:
        if st.session_state.game_log:
            st.dataframe(pd.DataFrame(st.session_state.game_log), use_container_width=True)
        else:
            st.info("Game hasn't started yet.")

    # Sidebar Reset
    with st.sidebar:
        st.warning("⚠️ Danger Zone")
        if st.button("End Game / Reset"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

# --- MAIN ROUTER ---
if st.session_state.game_started:
    render_game()
else:
    render_setup()
