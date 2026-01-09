import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="CourtCommand | Pro Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. PROFESSIONAL LIGHT THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Oswald:wght@500&display=swap');
    
    /* Global App Style */
    .stApp { background-color: #f8f9fa; color: #212529; }
    
    /* STICKY SCOREBOARD */
    .sticky-header {
        position: sticky; top: 0; z-index: 999; background: #ffffff;
        padding: 10px 0; border-bottom: 3px solid #0056b3;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .score-text { font-family: 'Oswald', sans-serif; font-size: 45px; font-weight: bold; line-height: 1; color: #212529; }
    .team-label { font-family: 'Roboto', sans-serif; font-size: 14px; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; }
    
    /* ACTIVE PLAYER ROW STYLE */
    .active-row {
        background: #ffffff; 
        border: 1px solid #dee2e6; 
        border-radius: 8px;
        padding: 10px; 
        margin-bottom: 8px; 
        border-left: 6px solid #28a745; /* Green indicator for ON COURT */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.1s;
    }
    .active-row:hover { transform: scale(1.01); }
    
    /* PLUS MINUS INDICATORS */
    .pm-positive { color: #198754; font-weight: bold; background: #d1e7dd; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
    .pm-negative { color: #dc3545; font-weight: bold; background: #f8d7da; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
    .pm-neutral { color: #6c757d; background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 12px; }

    /* HIDE DEFAULT FOOTER */
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. STATE INITIALIZATION & DATA REPAIR ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'game_log' not in st.session_state: st.session_state.game_log = []
if 'teams' not in st.session_state: st.session_state.teams = {"Home": "WARRIORS", "Away": "LAKERS"}
if 'period' not in st.session_state: st.session_state.period = 1
if 'roster' not in st.session_state: st.session_state.roster = {"Home": [], "Away": []}

# === 🛠️ AUTO-FIXER: PREVENTS CRASHES FROM OLD DATA ===
if 'roster' in st.session_state:
    for team in ["Home", "Away"]:
        for p in st.session_state.roster[team]:
            # Ensure new keys exist if loading old session data
            if 'PM' not in p: p['PM'] = 0
            if 'is_active' not in p: p['is_active'] = False
# ======================================================

# METRIC KEYS
STATS_KEYS = ["PTS", "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PF", "PM"]

def init_player(name):
    p = {k: 0 for k in STATS_KEYS}
    p['name'] = name
    p['is_active'] = False # Default to bench
    return p

# --- 4. LOGIC ENGINE ---

def update_plus_minus(scoring_team_key, points):
    """Updates +/- for all players currently on the court"""
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
    
    # Scoring Logic & Stats
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
    else: 
        player[action_type] += 1 # AST, REB, STL, etc.

    # Update +/- if points were scored
    if points_added > 0:
        update_plus_minus(team_key, points_added)

    # Log to Game Feed
    st.session_state.game_log.insert(0, {
        "Q": st.session_state.period,
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Team": st.session_state.teams[team_key],
        "Player": player['name'],
        "Action": action_type,
        "Score": f"{get_score('Home')} - {get_score('Away')}"
    })
    
    # Toast Notification
    if points_added > 0: 
        st.toast(f"{player['name']} +{points_added} PTS | +/- Updated", icon="🔥")
    else: 
        st.toast(f"{player['name']} recorded {action_type}", icon="✅")

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
                    <div class="team-label">{st.session_state.teams['Home']}</div>
                    <div class="score-text" style="color: #0d6efd;">{h_score}</div>
                </div>
                <div style="text-align: center; width: 20%;">
                     <span style="background:#e9ecef; color:#495057; padding:5px 15px; border-radius:15px; font-weight:bold;">
                        Q{st.session_state.period}
                     </span>
                </div>
                <div style="text-align: center; width: 30%;">
                    <div class="team-label">{st.session_state.teams['Away']}</div>
                    <div class="score-text" style="color: #dc3545;">{a_score}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_subs_sidebar():
    st.sidebar.title("🔄 Substitution")
    st.sidebar.info("Select the 5 players currently on the court.")
    
    # Home Subs
    st.sidebar.markdown(f"**{st.session_state.teams['Home']}**")
    for p in st.session_state.roster["Home"]:
        p['is_active'] = st.sidebar.checkbox(f"{p['name']}", value=p['is_active'], key=f"sub_h_{p['name']}")
            
    st.sidebar.markdown("---")
    
    # Away Subs
    st.sidebar.markdown(f"**{st.session_state.teams['Away']}**")
    for p in st.session_state.roster["Away"]:
        p['is_active'] = st.sidebar.checkbox(f"{p['name']}", value=p['is_active'], key=f"sub_a_{p['name']}")

def render_active_grid(team_key):
    roster = st.session_state.roster[team_key]
    active_players = [p for p in roster if p['is_active']]
    
    if not active_players:
        st.info("👈 Please check players in the Sidebar to put them ON COURT.")
        return

    # Column Headers
    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.5, 1.5, 1.5, 3, 2])
    c1.caption("ACTIVE PLAYER")
    c2.caption("FT")
    c3.caption("2PT")
    c4.caption("3PT")
    c5.caption("STATS")
    c6.caption("FOUL/TO")

    for i, p in enumerate(roster):
        if p['is_active']: # Only render if Checked in Sidebar
            uid = f"{team_key}_{i}"
            with st.container():
                st.markdown('<div class="active-row">', unsafe_allow_html=True)
                r1, r2, r3, r4, r5, r6 = st.columns([2.5, 1.5, 1.5, 1.5, 3, 2])
                
                with r1:
                    # Plus/Minus Badge Logic
                    if p['PM'] > 0: pm_badge = f"<span class='pm-positive'>+{p['PM']}</span>"
                    elif p['PM'] < 0: pm_badge = f"<span class='pm-negative'>{p['PM']}</span>"
                    else: pm_badge = f"<span class='pm-neutral'>E</span>"
                    
                    st.markdown(f"**{p['name']}** {pm_badge}", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:grey; font-size:12px'>{p['PTS']} pts</span>", unsafe_allow_html=True)

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

# --- 6. MAIN APP ROUTING ---
if not st.session_state.game_active:
    # SETUP PAGE
    st.title("📋 Match Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Home Team")
        h_n = st.text_input("Name", "Warriors")
        h_r = st.text_area("Roster (1 name per line)", "Curry\nThompson\nGreen\nWiggins\nLooney\nPaul\nKuminga")
    with col2:
        st.markdown("### Away Team")
        a_n = st.text_input("Name", "Lakers")
        a_r = st.text_area("Roster (1 name per line)", "LeBron\nDavis\nReaves\nRussell\nHachimura\nVanderbilt\nWood")
    
    st.divider()
    if st.button("🚀 Start Match", type="primary", use_container_width=True):
        st.session_state.teams["Home"] = h_n
        st.session_state.teams["Away"] = a_n
        # Initialize Players
        st.session_state.roster["Home"] = [init_player(x) for x in h_r.split('\n') if x.strip()]
        st.session_state.roster["Away"] = [init_player(x) for x in a_r.split('\n') if x.strip()]
        
        st.session_state.game_active = True
        st.rerun()

else:
    # GAME PAGE
    render_scoreboard()
    render_subs_sidebar()
    
    t1, t2, t3, t4 = st.tabs(["🏠 Home Court", "✈️ Away Court", "📊 Box Score", "⚙️ Admin"])
    
    with t1: render_active_grid("Home")
    with t2: render_active_grid("Away")
    
    with t3:
        # ADVANCED BOX SCORE
        st.markdown("### 📊 Live Game Stats")
        data = []
        for t in ["Home", "Away"]:
            for p in st.session_state.roster[t]:
                row = p.copy()
                row['Team'] = st.session_state.teams[t]
                row['Status'] = "ON COURT" if p['is_active'] else "BENCH"
                # Calculate simple Efficiency
                eff = (p['PTS'] + p['OREB'] + p['DREB'] + p['AST'] + p['STL'] + p['BLK']) - ((p['FGA']-p['FGM']) + (p['FTA']-p['FTM']) + p['TOV'])
                row['EFF'] = eff
                data.append(row)
        
        if data:
            df = pd.DataFrame(data)
            cols = ["Team", "name", "Status", "PM", "PTS", "EFF", "FGM", "FGA", "AST", "PF"]
            
            # Simple clean dataframe
            st.dataframe(df[cols], use_container_width=True, height=600)
            
            # Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full CSV", csv, "game_stats.csv", "text/csv")
            
    with t4:
        st.markdown("### Game Controls")
        if st.button("End Period / Next Quarter"):
            st.session_state.period += 1
            st.toast("Period Updated")
        
        st.divider()
        if st.button("⚠️ Reset Game Data", type="primary"):
            st.session_state.clear()
            st.rerun()
