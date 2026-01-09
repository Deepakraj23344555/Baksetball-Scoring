import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Digital Scorer's Table", page_icon="📝", layout="wide")

# --- CSS FOR REALISTIC SCOREBOARD LOOK ---
st.markdown("""
    <style>
    .score-box {
        font-size: 60px;
        font-weight: bold;
        text-align: center;
        background-color: #000;
        color: #f00; /* LED Red */
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stat-label {
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        color: #555;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
# Initialize all session state variables if they don't exist
default_values = {
    'home_score': 0, 'away_score': 0,
    'home_fouls': 0, 'away_fouls': 0,
    'home_timeouts': 0, 'away_timeouts': 0,
    'period': 1,
    'possession': 'HOME',
    'game_log': []  # This will hold the official running scoresheet
}

for key, val in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- HELPER FUNCTIONS ---
def add_event(team, player_num, event_type, points=0):
    # Update Scores
    if team == "HOME":
        st.session_state.home_score += points
    else:
        st.session_state.away_score += points
    
    # Create Log Entry
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "Period": st.session_state.period,
        "Time": timestamp,
        "Team": team,
        "Player #": player_num if player_num else "TEAM",
        "Event": event_type,
        "Running Score": f"{st.session_state.home_score} - {st.session_state.away_score}"
    }
    st.session_state.game_log.insert(0, log_entry) # Add to top of list

def reset_fouls():
    st.session_state.home_fouls = 0
    st.session_state.away_fouls = 0
    st.toast("Team fouls reset for new quarter!")

# --- SIDEBAR: GAME SETUP ---
with st.sidebar:
    st.header("⚙️ Game Setup")
    home_name = st.text_input("Home Team", "Home")
    away_name = st.text_input("Away Team", "Away")
    
    st.divider()
    
    st.subheader("Game Admin")
    if st.button("End Period / Quarter"):
        st.session_state.period += 1
        reset_fouls() # Typically fouls reset every quarter (FIBA/NBA)
    
    if st.button("Switch Possession Arrow"):
        st.session_state.possession = "AWAY" if st.session_state.possession == "HOME" else "HOME"

    if st.button("RESET GAME", type="primary"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- MAIN SCOREBOARD ---
c1, c2, c3 = st.columns([2, 1, 2])

with c1:
    st.markdown(f"<h2 style='text-align:center;'>{home_name}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='score-box'>{st.session_state.home_score}</div>", unsafe_allow_html=True)
    
    # Team Stats Row
    s1, s2 = st.columns(2)
    s1.metric("Fouls", st.session_state.home_fouls)
    s2.metric("Timeouts", st.session_state.home_timeouts)
    
    if st.session_state.possession == "HOME":
        st.markdown("🚨 **POSSESSION**")

with c2:
    st.markdown(f"<div style='text-align:center; padding-top:20px; font-size: 24px;'>PERIOD</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; font-size: 40px; font-weight:bold;'>{st.session_state.period}</div>", unsafe_allow_html=True)

with c3:
    st.markdown(f"<h2 style='text-align:center;'>{away_name}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='score-box'>{st.session_state.away_score}</div>", unsafe_allow_html=True)
    
    # Team Stats Row
    s1, s2 = st.columns(2)
    s1.metric("Fouls", st.session_state.away_fouls)
    s2.metric("Timeouts", st.session_state.away_timeouts)
    
    if st.session_state.possession == "AWAY":
        st.markdown("🚨 **POSSESSION**")

st.divider()

# --- INPUT CONSOLE ---
# This is where the user enters data
col_home, col_away = st.columns(2)

# === HOME CONTROLS ===
with col_home:
    st.subheader(f"📝 {home_name} Entry")
    h_player = st.text_input("Player Jersey #", key="h_player", placeholder="e.g. 23")
    
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    if r1_c1.button("+1 FT", key="h1"):
        add_event(home_name, h_player, "Free Throw (1pt)", 1)
    if r1_c2.button("+2 FG", key="h2"):
        add_event(home_name, h_player, "Field Goal (2pt)", 2)
    if r1_c3.button("+3 3PT", key="h3"):
        add_event(home_name, h_player, "3-Pointer (3pt)", 3)
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    if r2_c1.button("Foul (P)", key="hf"):
        st.session_state.home_fouls += 1
        add_event(home_name, h_player, "Personal Foul", 0)
    if r2_c2.button("Tech Foul", key="htf"):
        add_event(home_name, h_player, "Technical Foul", 0)
        # Note: Tech fouls often don't add to team foul count depending on rules, handled manually here
    if r2_c3.button("Timeout", key="hto"):
        st.session_state.home_timeouts += 1
        add_event(home_name, "TEAM", "Timeout Taken", 0)

# === AWAY CONTROLS ===
with col_away:
    st.subheader(f"📝 {away_name} Entry")
    a_player = st.text_input("Player Jersey #", key="a_player", placeholder="e.g. 0")
    
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    if r1_c1.button("+1 FT", key="a1"):
        add_event(away_name, a_player, "Free Throw (1pt)", 1)
    if r1_c2.button("+2 FG", key="a2"):
        add_event(away_name, a_player, "Field Goal (2pt)", 2)
    if r1_c3.button("+3 3PT", key="a3"):
        add_event(away_name, a_player, "3-Pointer (3pt)", 3)
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    if r2_c1.button("Foul (P)", key="af"):
        st.session_state.away_fouls += 1
        add_event(away_name, a_player, "Personal Foul", 0)
    if r2_c2.button("Tech Foul", key="atf"):
        add_event(away_name, a_player, "Technical Foul", 0)
    if r2_c3.button("Timeout", key="ato"):
        st.session_state.away_timeouts += 1
        add_event(away_name, "TEAM", "Timeout Taken", 0)

st.divider()

# --- OFFICIAL SCORESHEET LOG ---
st.subheader("📋 Official Game Log")
if st.session_state.game_log:
    df = pd.DataFrame(st.session_state.game_log)
    st.dataframe(df, use_container_width=True)
    
    # Download Button for the report
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Scoresheet (CSV)",
        data=csv,
        file_name='basketball_scoresheet.csv',
        mime='text/csv',
    )
else:
    st.info("No events recorded yet. Enter a play above.")
