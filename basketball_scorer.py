import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="FIBA LIVE STATS | CourtCommand",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED CSS (THEMING) ---
# This injects the "Professional" look: Sticky Header, Neon Buttons, Dark Theme
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@700&family=Oswald:wght@500&display=swap');

    /* GENERAL APP THEME */
    .stApp {
        background-color: #0e1117; /* Dark Background */
        color: #ffffff;
    }

    /* STICKY SCOREBOARD (JUMBOTRON) */
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
        padding: 15px 0px;
        border-bottom: 3px solid #fca311; /* NBA Orange Accent */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }
    .score-text {
        font-family: 'Oswald', sans-serif;
        font-size: 50px;
        font-weight: bold;
        text-align: center;
        margin: 0;
        line-height: 1;
    }
    .team-name {
        font-family: 'Roboto Mono', monospace;
        font-size: 18px;
        color: #9ca3af;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .period-indicator {
        background-color: #374151;
        color: #fca311;
        padding: 5px 15px;
        border-radius: 15px;
        font-weight: bold;
        text-align: center;
        display: inline-block;
    }

    /* PLAYER ROWS styling */
    .player-row {
        background-color: #1f2937;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 5px solid #374151;
        transition: all 0.2s;
    }
    .player-row:hover {
        border-left: 5px solid #fca311;
        background-color: #2d3748;
    }
    .player-name {
        font-size: 16px;
        font-weight: 600;
        color: #e5e7eb;
        padding-top: 5px;
    }

    /* CUSTOM BUTTON COLORING VIA CSS SELECTORS IS TRICKY IN STREAMLIT
       SO WE USE LAYOUT AND EMOJIS TO CREATE VISUAL DISTINCTION */
    
    div.stButton > button {
        width: 100%;
        border-radius: 4px;
        font-weight: bold;
        border: none;
        height: 40px;
    }
    
    /* HIDE STREAMLIT FOOTER */
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE INITIALIZATION ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'game_log' not in st.session_state:
    st.session_state.game_log = []
if 'teams' not in st.session_state:
    st.session_state.teams = {"Home": "LAKERS", "Away": "CELTICS"}
if 'period' not in st.session_state:
    st.session_state.period = 1
if 'home_fouls' not in st.session_state:
    st.session_state.home_fouls = 0
if 'away_fouls' not in st.session_state:
    st.session_state.away_fouls = 0
if 'roster' not in st.session_state:
    st.session_state.roster = {"Home": [], "Away": []}

# Define Stats Structure (NBA Standard)
STATS_KEYS = ["PTS", "FGM", "3PM", "FTM", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PF"]

def init_player(name):
    p = {k: 0 for k in STATS_KEYS}
    p['name'] = name
    return p

# --- 4. LOGIC ENGINE ---

def log_event(team_key, player_idx, stat, points=0, is_foul=False):
    # Update Stats
    player = st.session_state.roster[team_key][player_idx]
    player[stat] += 1
    
    if points > 0:
        player["PTS"] += points
    
    # Update Team Fouls
    if is_foul:
        if team_key == "Home": st.session_state.home_fouls += 1
        else: st.session_state.away_fouls += 1

    # Create Log
    team_name = st.session_state.teams[team_key]
    time_stamp = datetime.now().strftime("%H:%M:%S")
    score_str = f"{get_score('Home')} - {get_score('Away')}"
    
    log_entry = {
        "Q": st.session_state.period,
        "Time": time_stamp,
        "Team": team_name,
        "Player": player['name'],
        "Action": stat,
        "Score": score_str
    }
    st.session_state.game_log.insert(0, log_entry)
    
    # "Living App" Feedback
    st.toast(f"✅ {player['name']} | {stat} Recorded!", icon="🏀")

def get_score(team_key):
    return sum(p['PTS'] for p in st.session_state.roster[team_key])

def reset_period():
    st.session_state.period += 1
    st.session_state.home_fouls = 0
    st.session_state.away_fouls = 0
    st.toast(f"Period {st.session_state.period} Started. Team Fouls Reset.", icon="⏱️")

# --- 5. UI COMPONENTS ---

def render_scoreboard():
    h_score = get_score("Home")
    a_score = get_score("Away")
    h_name = st.session_state.teams["Home"]
    a_name = st.session_state.teams["Away"]
    
    # The Sticky Header
    st.markdown(f"""
        <div class="sticky-header">
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="text-align: center; width: 30%;">
                    <div class="team-name">{h_name}</div>
                    <div class="score-text" style="color: #4ade80;">{h_score}</div>
                    <div style="font-size: 12px; color: #ef4444;">FOULS: {st.session_state.home_fouls}</div>
                </div>
                <div style="text-align: center; width: 20%;">
                     <div class="period-indicator">Q{st.session_state.period}</div>
                </div>
                <div style="text-align: center; width: 30%;">
                    <div class="team-name">{a_name}</div>
                    <div class="score-text" style="color: #60a5fa;">{a_score}</div>
                    <div style="font-size: 12px; color: #ef4444;">FOULS: {st.session_state.away_fouls}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_player_grid(team_key):
    roster = st.session_state.roster[team_key]
    
    # Column Headers
    st.markdown(f"### {st.session_state.teams[team_key]} Roster")
    h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([2.5, 1, 1, 1, 1, 1, 1, 1, 1])
    h1.caption("PLAYER")
    h2.caption("PTS") # +1
    h3.caption("FG")  # +2
    h4.caption("3PT") # +3
    h5.caption("REB")
    h6.caption("AST")
    h7.caption("STL")
    h8.caption("TOV")
    h9.caption("PF")

    for i, p in enumerate(roster):
        uid = f"{team_key}_{i}"
        
        # We use a container to apply the CSS style
        with st.container():
            c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([2.5, 1, 1, 1, 1, 1, 1, 1, 1])
            
            c1.markdown(f"<div class='player-name'>{p['name']} <span style='color:grey; font-size:10px'>({p['PTS']}pts)</span></div>", unsafe_allow_html=True)
            
            # SCORING (Green/Primary)
            if c2.button("FT", key=f"{uid}_ft", help="+1 Point"): log_event(team_key, i, "FTM", 1)
            if c3.button("2P", key=f"{uid}_2p", help="+2 Points"): log_event(team_key, i, "FGM", 2)
            if c4.button("3P", key=f"{uid}_3p", help="+3 Points"): log_event(team_key, i, "3PM", 3)
            
            # POSITIVE STATS (Secondary)
            if c5.button("REB", key=f"{uid}_rb"): log_event(team_key, i, "DREB") # Simplified to generic Reb
            if c6.button("AST", key=f"{uid}_as"): log_event(team_key, i, "AST")
            if c7.button("STL", key=f"{uid}_st"): log_event(team_key, i, "STL")
            
            # NEGATIVE STATS (Danger)
            if c8.button("TO", key=f"{uid}_to"): log_event(team_key, i, "TOV")
            if c9.button("PF", key=f"{uid}_pf"): log_event(team_key, i, "PF", is_foul=True)
        
        st.markdown("<div style='margin-bottom: 5px'></div>", unsafe_allow_html=True) # Spacer

# --- 6. SETUP PAGE ---
def setup_screen():
    st.title("🏀 COURT COMMAND PRO Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### HOME TEAM")
        h_team = st.text_input("Home Name", "Lakers")
        h_text = st.text_area("Home Roster (Paste Names)", "LeBron James\nAnthony Davis\nAustin Reaves")
    
    with col2:
        st.markdown("### AWAY TEAM")
        a_team = st.text_input("Away Name", "Celtics")
        a_text = st.text_area("Away Roster (Paste Names)", "Jayson Tatum\nJaylen Brown\nJrue Holiday")

    if st.button("INITIALIZE GAME SYSTEM", type="primary", use_container_width=True):
        st.session_state.teams["Home"] = h_team
        st.session_state.teams["Away"] = a_team
        
        # Process Lists
        h_list = [x.strip() for x in h_text.split('\n') if x.strip()]
        a_list = [x.strip() for x in a_text.split('\n') if x.strip()]
        
        st.session_state.roster["Home"] = [init_player(n) for n in h_list]
        st.session_state.roster["Away"] = [init_player(n) for n in a_list]
        
        st.session_state.game_active = True
        st.rerun()

# --- 7. MAIN GAME SCREEN ---
def game_screen():
    render_scoreboard()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 HOME ENTRY", "✈️ AWAY ENTRY", "📊 LIVE BOX SCORE", "⚙️ ADMIN"])
    
    with tab1:
        render_player_grid("Home")
    
    with tab2:
        render_player_grid("Away")
        
    with tab3:
        st.markdown("### 📊 Live Box Score")
        # Flatten Data
        all_players = []
        for t in ["Home", "Away"]:
            for p in st.session_state.roster[t]:
                row = p.copy()
                row["Team"] = st.session_state.teams[t]
                all_players.append(row)
        
        if all_players:
            df = pd.DataFrame(all_players)
            # Reorder
            cols = ["Team", "name", "PTS", "FGM", "3PM", "FTM", "AST", "DREB", "STL", "BLK", "TOV", "PF"]
            st.dataframe(
                df[cols].style.background_gradient(cmap="Greens", subset=["PTS"]), 
                use_container_width=True, 
                height=600
            )
    
    with tab4:
        st.markdown("### Game Administration")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("End Quarter / Period", use_container_width=True):
                reset_period()
        with c2:
            if st.button("📥 Download CSV Report", use_container_width=True):
                df_log = pd.DataFrame(st.session_state.game_log)
                st.download_button("Click to Download", df_log.to_csv(), "game_report.csv")
        with c3:
             if st.button("⚠️ RESET MATCH", type="primary", use_container_width=True):
                for key in st.session_state.keys(): del st.session_state[key]
                st.rerun()

# --- APP ROUTER ---
if st.session_state.game_active:
    game_screen()
else:
    setup_screen()
