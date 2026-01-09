import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="CourtCommand | Pro Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded" # Sidebar open by default for substitutions
)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Oswald:wght@500&display=swap');
    
    .stApp { background-color: #f8f9fa; color: #212529; }
    
    /* SCOREBOARD */
    .sticky-header {
        position: sticky; top: 0; z-index: 999; background: #fff;
        padding: 10px 0; border-bottom: 3px solid #0056b3;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .score-text { font-family: 'Oswald', sans-serif; font-size: 40px; font-weight: bold; line-height: 1; }
    
    /* ACTIVE PLAYER ROW */
    .active-row {
        background: #fff; border: 1px solid #dee2e6; border-radius: 8px;
        padding: 8px; margin-bottom: 5px; border-left: 5px solid #28a745; /* Green for Active */
    }
    .bench-row { border-left: 5px solid #6c757d; opacity: 0.6; } /* Gray for Bench */
    
    /* PLUS MINUS BADGES */
    .pm-positive { color: #198754; font-weight: bold; }
    .pm-negative { color: #dc3545; font-weight: bold; }
    
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. STATE INITIALIZATION ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'game_log' not in st.session_state: st.session_state.game_log = []
if 'teams' not in st.session_state: st.session_state.teams = {"Home": "WARRIORS", "Away": "LAKERS"}
if 'period' not in st.session_state: st.session_state.period = 1
if 'roster' not in st.session_state: st.session_state.roster = {"Home": [], "Away": []}

STATS_KEYS = ["PTS", "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PF", "PM"]

def init_player(name):
    p = {k: 0 for k in STATS_KEYS}
    p['name'] = name
    p['is_active'] = False # New Flag for Substitution
    return p

# --- 4. LOGIC ENGINE (UPDATED FOR +/-) ---

def update_plus_minus(scoring_team_key, points):
    # This function runs every time points are scored
    
    # 1. Add (+) to active players of the scoring team
    for p in st.session_state.roster[scoring_team_key]:
        if p['is_active']:
            p['PM'] += points
            
    # 2. Subtract (-) from active players of the opposing team
    opp_key = "Away" if scoring_team_key == "Home" else "Home"
    for p in st.session_state.roster[opp_key]:
        if p['is_active']:
            p['PM'] -= points

def log_event(team_key, player_idx, action_type):
    player = st.session_state.roster[team_key][player_idx]
    points_added = 0
    
    # Scoring Logic
    if action_type == "FTM":
        player["FTM"] += 1; player["FTA"] += 1; player["PTS"] += 1
        points_added = 1
    elif action_type == "FT_MISS": player["FTA"] += 1
    elif action_type == "2PM":
        player["FGM"] += 1; player["FGA"] += 1; player["PTS"] += 2
        points_added = 2
    elif action_type == "2P_MISS": player["FGA"] += 1
    elif action_type == "3PM":
        player["3PM"] += 1; player["3PA"] += 1; player["FGM"] += 1; player["FGA"] += 1; player["PTS"] += 3
        points_added = 3
    elif action_type == "3P_MISS": player["3PA"] += 1; player["FGA"] += 1
    else: player[action_type] += 1 # Other stats

    # Trigger Plus/Minus Calculation
    if points_added > 0:
        update_plus_minus(team_key, points_added)

    # Log
    st.session_state.game_log.insert(0, {
        "Q": st.session_state.period,
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Team": st.session_state.teams[team_key],
        "Player": player['name'],
        "Action": action_type,
        "Score": f"{get_score('Home')} - {get_score('Away')}"
    })
    
    if points_added > 0: st.toast(f"{player['name']} Scored! +/- Updated.", icon="🔥")
    else: st.toast(f"Recorded: {action_type}", icon="✅")

def get_score(team_key):
    return sum(p['PTS'] for p in st.session_state.roster[team_key])

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
                     <div class="period-indicator">Q{st.session_state.period}</div>
                </div>
                <div style="text-align: center; width: 30%;">
                    <div class="team-name">{st.session_state.teams['Away']}</div>
                    <div class="score-text" style="color: #dc3545;">{a_score}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_subs_sidebar():
    st.sidebar.header("🔄 Substitutions")
    st.sidebar.caption("Check players currently ON COURT")
    
    with st.sidebar.expander(f"🏠 {st.session_state.teams['Home']}", expanded=True):
        for p in st.session_state.roster["Home"]:
            # Checkbox creates a binding to the boolean
            p['is_active'] = st.checkbox(f"{p['name']} ({p['PM']})", value=p['is_active'], key=f"sub_h_{p['name']}")
            
    with st.sidebar.expander(f"✈️ {st.session_state.teams['Away']}", expanded=True):
        for p in st.session_state.roster["Away"]:
            p['is_active'] = st.checkbox(f"{p['name']} ({p['PM']})", value=p['is_active'], key=f"sub_a_{p['name']}")

def render_active_grid(team_key):
    roster = st.session_state.roster[team_key]
    active_players = [p for p in roster if p['is_active']]
    
    if not active_players:
        st.warning("⚠️ No players active! Go to the Sidebar and check 5 players to start scoring.")
        return

    # Headers
    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.5, 1.5, 1.5, 3, 2])
    c1.caption("ACTIVE 5")
    c2.caption("FT")
    c3.caption("2PT")
    c4.caption("3PT")
    c5.caption("STATS")

    for i, p in enumerate(roster):
        if p['is_active']: # Only show if active
            uid = f"{team_key}_{i}"
            with st.container():
                st.markdown('<div class="active-row">', unsafe_allow_html=True)
                r1, r2, r3, r4, r5, r6 = st.columns([2.5, 1.5, 1.5, 1.5, 3, 2])
                
                with r1:
                    # Show Name and +/-
                    pm_color = "pm-positive" if p['PM'] > 0 else "pm-negative"
                    st.markdown(f"**{p['name']}** <span class='{pm_color}'>({p['PM']:+d})</span>", unsafe_allow_html=True)
                    st.caption(f"{p['PTS']} pts | {p['FGM']}/{p['FGA']} FG")

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
                     if st.button("TO", key=f"{uid}_to"): log_event(team_key, i, "TOV")
                     if st.button("PF", key=f"{uid}_pf"): log_event(team_key, i, "PF")

                st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MAIN APP ---
if not st.session_state.game_active:
    st.title("🏀 Pro Setup")
    c1, c2 = st.columns(2)
    h_n = c1.text_input("Home", "Celtics")
    h_r = c1.text_area("Home Roster", "Tatum\nBrown\nWhite\nHoliday\nPorzingis\nHorford\nPritchard")
    a_n = c2.text_input("Away", "Heat")
    a_r = c2.text_area("Away Roster", "Butler\nAdebayo\nHerro\nRozier\nJovic\nHighsmith\nLove")
    
    if st.button("Start Game", type="primary"):
        st.session_state.teams["Home"] = h_n
        st.session_state.teams["Away"] = a_n
        # Initialize all players (default inactive)
        st.session_state.roster["Home"] = [init_player(x) for x in h_r.split('\n') if x.strip()]
        st.session_state.roster["Away"] = [init_player(x) for x in a_r.split('\n') if x.strip()]
        st.session_state.game_active = True
        st.rerun()
else:
    # Game Mode
    render_scoreboard()
    render_subs_sidebar() # <--- NEW FEATURE
    
    t1, t2, t3 = st.tabs(["🏠 Home Court", "✈️ Away Court", "📊 Stats Hub"])
    
    with t1: render_active_grid("Home")
    with t2: render_active_grid("Away")
    with t3:
        # Full Box Score
        data = []
        for t in ["Home", "Away"]:
            for p in st.session_state.roster[t]:
                row = p.copy()
                row['Team'] = st.session_state.teams[t]
                # Status column
                row['Status'] = "ON COURT" if p['is_active'] else "BENCH"
                data.append(row)
        
        if data:
            df = pd.DataFrame(data)
            cols = ["Team", "name", "Status", "PM", "PTS", "FGM", "FGA", "AST", "PF"]
            st.dataframe(
                df[cols].style.apply(lambda x: ['background-color: #d4edda' if v == 'ON COURT' else '' for v in x], subset=['Status']),
                use_container_width=True, height=600
            )
