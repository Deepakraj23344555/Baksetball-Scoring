import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="CourtCommand | Official Light",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. LIGHT THEME CSS ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Oswald:wght@500&display=swap');

    /* LIGHT MODE OVERRIDES */
    .stApp {
        background-color: #f8f9fa; /* Light Gray Background */
        color: #212529; /* Dark Text */
    }

    /* STICKY SCOREBOARD (Light Version) */
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background: #ffffff;
        padding: 15px 0px;
        border-bottom: 3px solid #0056b3; /* Professional Blue */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .score-text {
        font-family: 'Oswald', sans-serif;
        font-size: 50px;
        font-weight: bold;
        text-align: center;
        color: #212529;
        margin: 0;
        line-height: 1;
    }
    .team-name {
        font-family: 'Roboto', sans-serif;
        font-size: 18px;
        color: #6c757d; /* Muted Gray */
        text-align: center;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .period-indicator {
        background-color: #e9ecef;
        color: #0056b3;
        padding: 5px 20px;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
        display: inline-block;
        border: 1px solid #dee2e6;
    }

    /* PLAYER ROWS styling (Light Card Style) */
    .player-row-container {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #dee2e6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s;
    }
    .player-row-container:hover {
        border-left: 5px solid #0056b3;
        transform: translateX(2px);
    }
    .player-name {
        font-size: 16px;
        font-weight: 700;
        color: #343a40;
    }
    .player-sub {
        font-size: 12px;
        color: #868e96;
    }
    
    /* REPORT CARD STYLE */
    .report-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* HIDE FOOTER */
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE INITIALIZATION ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'game_log' not in st.session_state:
    st.session_state.game_log = []
if 'teams' not in st.session_state:
    st.session_state.teams = {"Home": "WARRIORS", "Away": "LAKERS"}
if 'period' not in st.session_state:
    st.session_state.period = 1
if 'roster' not in st.session_state:
    st.session_state.roster = {"Home": [], "Away": []}

# Define Stats Structure (Includes Misses for Efficiency Calc)
STATS_KEYS = ["PTS", "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PF"]

def init_player(name):
    p = {k: 0 for k in STATS_KEYS}
    p['name'] = name
    return p

# --- 4. LOGIC ENGINE ---

def log_event(team_key, player_idx, action_type):
    player = st.session_state.roster[team_key][player_idx]
    
    # Logic Map
    if action_type == "FTM":
        player["FTM"] += 1
        player["FTA"] += 1
        player["PTS"] += 1
    elif action_type == "FT_MISS":
        player["FTA"] += 1
    elif action_type == "2PM":
        player["FGM"] += 1
        player["FGA"] += 1
        player["PTS"] += 2
    elif action_type == "2P_MISS":
        player["FGA"] += 1
    elif action_type == "3PM":
        player["3PM"] += 1
        player["3PA"] += 1 # 3PA also counts as FGA usually, but we keep separate for simple logic
        player["FGM"] += 1 # Add to total FG
        player["FGA"] += 1
        player["PTS"] += 3
    elif action_type == "3P_MISS":
        player["3PA"] += 1
        player["FGA"] += 1
    else:
        # Simple stats
        player[action_type] += 1

    # Create Log
    team_name = st.session_state.teams[team_key]
    time_stamp = datetime.now().strftime("%H:%M:%S")
    
    log_entry = {
        "Q": st.session_state.period,
        "Time": time_stamp,
        "Team": team_name,
        "Player": player['name'],
        "Action": action_type,
        "Score": f"{get_score('Home')} - {get_score('Away')}"
    }
    st.session_state.game_log.insert(0, log_entry)
    
    # Toast Feedback
    msg = f"Recorded: {player['name']} | {action_type}"
    if "MISS" in action_type:
        st.toast(msg, icon="🧱")
    else:
        st.toast(msg, icon="✅")

def get_score(team_key):
    return sum(p['PTS'] for p in st.session_state.roster[team_key])

def calculate_efficiency(p):
    # NBA Efficiency Formula: (PTS + REB + AST + STL + BLK) - ((FGA - FGM) + (FTA - FTM) + TOV)
    reb = p['OREB'] + p['DREB']
    missed_fg = p['FGA'] - p['FGM']
    missed_ft = p['FTA'] - p['FTM']
    eff = (p['PTS'] + reb + p['AST'] + p['STL'] + p['BLK']) - (missed_fg + missed_ft + p['TOV'])
    return eff

# --- 5. UI COMPONENTS ---

def render_scoreboard():
    h_score = get_score("Home")
    a_score = get_score("Away")
    
    st.markdown(f"""
        <div class="sticky-header">
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="text-align: center; width: 30%;">
                    <div class="team-name">{st.session_state.teams['Home']}</div>
                    <div class="score-text" style="color: #0d6efd;">{h_score}</div>
                </div>
                <div style="text-align: center; width: 20%;">
                     <div class="period-indicator">PERIOD {st.session_state.period}</div>
                </div>
                <div style="text-align: center; width: 30%;">
                    <div class="team-name">{st.session_state.teams['Away']}</div>
                    <div class="score-text" style="color: #dc3545;">{a_score}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_player_grid(team_key):
    roster = st.session_state.roster[team_key]
    
    # Headers
    c1, c2, c3, c4, c5, c6 = st.columns([3, 1.5, 1.5, 1.5, 3, 2])
    c1.caption("PLAYER")
    c2.caption("FT")
    c3.caption("2PT")
    c4.caption("3PT")
    c5.caption("STATS")
    c6.caption("FOUL/TO")

    for i, p in enumerate(roster):
        uid = f"{team_key}_{i}"
        
        with st.container():
            st.markdown('<div class="player-row-container">', unsafe_allow_html=True)
            r1, r2, r3, r4, r5, r6 = st.columns([3, 1.5, 1.5, 1.5, 3, 2])
            
            with r1:
                st.markdown(f"<div class='player-name'>{p['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='player-sub'>{p['PTS']} pts | {p['FGM']}/{p['FGA']} FG</div>", unsafe_allow_html=True)

            with r2: 
                if st.button("Hit", key=f"{uid}_ft1"): log_event(team_key, i, "FTM")
                if st.button("Mis", key=f"{uid}_ft0"): log_event(team_key, i, "FT_MISS")
            
            with r3:
                if st.button("Hit", key=f"{uid}_2p1"): log_event(team_key, i, "2PM")
                if st.button("Mis", key=f"{uid}_2p0"): log_event(team_key, i, "2P_MISS")
                
            with r4:
                if st.button("Hit", key=f"{uid}_3p1"): log_event(team_key, i, "3PM")
                if st.button("Mis", key=f"{uid}_3p0"): log_event(team_key, i, "3P_MISS")
                
            with r5:
                c_a, c_b = st.columns(2)
                if c_a.button("REB", key=f"{uid}_reb"): log_event(team_key, i, "DREB")
                if c_b.button("AST", key=f"{uid}_ast"): log_event(team_key, i, "AST")
                if c_a.button("STL", key=f"{uid}_stl"): log_event(team_key, i, "STL")
                if c_b.button("BLK", key=f"{uid}_blk"): log_event(team_key, i, "BLK")
            
            with r6:
                if st.button("TOV", key=f"{uid}_to"): log_event(team_key, i, "TOV")
                if st.button("PF", key=f"{uid}_pf"): log_event(team_key, i, "PF")

            st.markdown('</div>', unsafe_allow_html=True)

# --- 6. INDIVIDUAL REPORT CARD GENERATOR ---
def render_report_cards():
    st.subheader("📇 Player Performance Cards")
    
    # Select Team and Player
    col1, col2 = st.columns(2)
    with col1:
        team_select = st.selectbox("Select Team", ["Home", "Away"])
    with col2:
        # Get list of names for that team
        roster_names = [p['name'] for p in st.session_state.roster[team_select]]
        player_select = st.selectbox("Select Player", roster_names)

    # Find the player object
    player_data = next((p for p in st.session_state.roster[team_select] if p['name'] == player_select), None)
    
    if player_data:
        eff = calculate_efficiency(player_data)
        
        # Draw the Report Card
        st.markdown(f"""
        <div class="report-card">
            <h2 style="color:#0056b3; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">
                {player_data['name']} <span style="float:right; color:#6c757d; font-size: 20px;">{st.session_state.teams[team_select]}</span>
            </h2>
            <br>
        """, unsafe_allow_html=True)
        
        # Metric Row 1
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Points", player_data['PTS'])
        m2.metric("Efficiency (EFF)", eff, delta_color="normal")
        m3.metric("Rebounds", player_data['OREB'] + player_data['DREB'])
        m4.metric("Assists", player_data['AST'])
        
        st.markdown("---")
        
        # Metric Row 2
        m5, m6, m7, m8 = st.columns(4)
        fg_pct = 0 if player_data['FGA'] == 0 else (player_data['FGM'] / player_data['FGA']) * 100
        m5.metric("FG %", f"{fg_pct:.1f}%", f"{player_data['FGM']}/{player_data['FGA']}")
        
        m6.metric("Steals", player_data['STL'])
        m7.metric("Blocks", player_data['BLK'])
        m8.metric("Turnovers", player_data['TOV'], delta_color="inverse")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # CSV Download for this specific player
        st.write("")
        df_player = pd.DataFrame([player_data])
        st.download_button(
            label=f"📥 Download Report for {player_data['name']}",
            data=df_player.to_csv(index=False).encode('utf-8'),
            file_name=f"{player_data['name']}_report.csv",
            mime="text/csv"
        )

# --- 7. MAIN APP STRUCTURE ---
if not st.session_state.game_active:
    st.title("🏀 CourtCommand | Setup")
    c1, c2 = st.columns(2)
    h_n = c1.text_input("Home Team", "Warriors")
    h_r = c1.text_area("Home Roster", "Curry\nThompson\nGreen")
    a_n = c2.text_input("Away Team", "Lakers")
    a_r = c2.text_area("Away Roster", "LeBron\nDavis\nReaves")
    
    if st.button("Start Match", type="primary"):
        st.session_state.teams["Home"] = h_n
        st.session_state.teams["Away"] = a_n
        st.session_state.roster["Home"] = [init_player(x) for x in h_r.split('\n') if x.strip()]
        st.session_state.roster["Away"] = [init_player(x) for x in a_r.split('\n') if x.strip()]
        st.session_state.game_active = True
        st.rerun()

else:
    render_scoreboard()
    
    t1, t2, t3, t4 = st.tabs(["🏠 Home", "✈️ Away", "📊 Box Score", "📇 Player Cards"])
    
    with t1: render_player_grid("Home")
    with t2: render_player_grid("Away")
    with t3:
        # Full Box Score Table
        data = []
        for t in ["Home", "Away"]:
            for p in st.session_state.roster[t]:
                row = p.copy()
                row['Team'] = st.session_state.teams[t]
                row['EFF'] = calculate_efficiency(p)
                data.append(row)
        
        df = pd.DataFrame(data)
        # Reorder columns nicely
        cols = ["Team", "name", "PTS", "EFF", "FGM", "FGA", "3PM", "AST", "DREB", "STL", "TOV", "PF"]
        st.dataframe(df[cols], use_container_width=True, height=500)
        
    with t4:
        render_report_cards()
        
    # Sidebar Admin
    with st.sidebar:
        st.header("Admin Controls")
        if st.button("Next Period"):
            st.session_state.period += 1
            st.toast("Period Updated!")
        if st.button("Reset Game", type="primary"):
            st.session_state.clear()
            st.rerun()
