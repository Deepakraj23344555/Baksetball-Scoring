import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. PRO CONFIGURATION & STYLING ---
st.set_page_config(page_title="FIBA Digital Scorer", layout="wide", page_icon="🏀")

# Custom CSS for that "NBA/FIBA" Dark Dashboard Look
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Scoreboard Header */
    .scoreboard-container {
        background-color: #000000;
        border: 2px solid #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .score-text {
        font-size: 80px; 
        font-weight: bold; 
        color: #fca311; /* Jersey Orange */
    }
    .team-text {
        font-size: 30px; 
        font-weight: bold; 
        color: #e5e5e5;
        text-transform: uppercase;
    }
    .timer-text {
        font-size: 60px;
        font-family: 'Courier New', Courier, monospace;
        color: #ff3b30; /* LED Red */
        font-weight: bold;
    }
    
    /* Action Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
        height: 60px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---
if 'match_data' not in st.session_state:
    st.session_state.match_data = {
        'team_a_name': "HOME",
        'team_b_name': "AWAY",
        'team_a_roster': [], # List of dicts
        'team_b_roster': [],
        'match_log': [],
        'score_a': 0,
        'score_b': 0,
    }

if 'timer' not in st.session_state:
    st.session_state.timer = {'running': False, 'time_left': 600} # 10 mins FIBA standard

# --- 3. HELPER FUNCTIONS ---
def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"

def log_event(quarter, team, player, event_type, points):
    # Log the data
    st.session_state.match_data['match_log'].append({
        'Quarter': quarter,
        'Time': format_time(st.session_state.timer['time_left']),
        'Team': team,
        'Player': player,
        'Event': event_type,
        'Points': points
    })
    
    # Update Live Score
    if team == st.session_state.match_data['team_a_name']:
        st.session_state.match_data['score_a'] += points
    elif team == st.session_state.match_data['team_b_name']:
        st.session_state.match_data['score_b'] += points

# --- 4. APP LAYOUT ---

# Sidebar for Setup (Keeps main screen clean)
with st.sidebar:
    st.title("⚙️ Game Setup")
    
    with st.expander("Team Configurations", expanded=True):
        st.session_state.match_data['team_a_name'] = st.text_input("Home Team", st.session_state.match_data['team_a_name'])
        st.session_state.match_data['team_b_name'] = st.text_input("Away Team", st.session_state.match_data['team_b_name'])
    
    with st.expander("Roster Management"):
        st.write(f"**Add to {st.session_state.match_data['team_a_name']}**")
        with st.form("a_roster"):
            p_name = st.text_input("Name")
            p_no = st.number_input("Jersey", 0, 99, key="a_no")
            if st.form_submit_button("Add Home Player"):
                st.session_state.match_data['team_a_roster'].append(f"#{p_no} {p_name}")

        st.write(f"**Add to {st.session_state.match_data['team_b_name']}**")
        with st.form("b_roster"):
            p_name_b = st.text_input("Name")
            p_no_b = st.number_input("Jersey", 0, 99, key="b_no")
            if st.form_submit_button("Add Away Player"):
                st.session_state.match_data['team_b_roster'].append(f"#{p_no_b} {p_name_b}")

# --- MAIN DASHBOARD ---

# Top Navigation
nav = st.radio("", ["Match Console", "Analytics & Reports"], horizontal=True)

if nav == "Match Console":
    # --- SECTION A: THE SCOREBOARD ---
    # This creates the visual impact of a real stadium board
    
    col_sb1, col_sb2, col_sb3 = st.columns([2, 3, 2])
    
    with col_sb1:
        st.markdown(f"<div class='scoreboard-container'><div class='team-text'>{st.session_state.match_data['team_a_name']}</div><div class='score-text'>{st.session_state.match_data['score_a']}</div></div>", unsafe_allow_html=True)
    
    with col_sb2:
        # Timer Logic
        st.markdown(f"<div class='scoreboard-container'><div class='team-text'>GAME CLOCK</div><div class='timer-text'>{format_time(st.session_state.timer['time_left'])}</div></div>", unsafe_allow_html=True)
        
        # Timer Controls
        t_c1, t_c2, t_c3 = st.columns(3)
        with t_c1:
            if st.button("▶ START"):
                st.session_state.timer['running'] = True
        with t_c2:
            if st.button("⏸ PAUSE"):
                st.session_state.timer['running'] = False
        with t_c3:
            if st.button("RESET QTR"):
                st.session_state.timer['time_left'] = 600

        # Auto-run timer logic if 'running' is True
        if st.session_state.timer['running']:
            time.sleep(1)
            st.session_state.timer['time_left'] -= 1
            st.rerun()

    with col_sb3:
        st.markdown(f"<div class='scoreboard-container'><div class='team-text'>{st.session_state.match_data['team_b_name']}</div><div class='score-text'>{st.session_state.match_data['score_b']}</div></div>", unsafe_allow_html=True)

    st.divider()

    # --- SECTION B: COURT CONTROLS ---
    
    # Context Settings
    c_sett1, c_sett2, c_sett3, c_sett4 = st.columns(4)
    with c_sett1:
        quarter = st.selectbox("QUARTER", ["Q1", "Q2", "Q3", "Q4", "OT"])
    with c_sett2:
        match_id = st.text_input("MATCH ID", "GM-2024-001")
    with c_sett3:
        if st.button("TIMEOUT (Home)"):
            log_event(quarter, st.session_state.match_data['team_a_name'], "TEAM", "TIMEOUT", 0)
            st.toast("Timeout Recorded - Home")
    with c_sett4:
        if st.button("TIMEOUT (Away)"):
            log_event(quarter, st.session_state.match_data['team_b_name'], "TEAM", "TIMEOUT", 0)
            st.toast("Timeout Recorded - Away")

    # The "5-Player" Active Selector
    st.subheader("Active Lineup (On Court)")
    
    row_act1, row_act2 = st.columns(2)
    with row_act1:
        st.info(f"🏀 {st.session_state.match_data['team_a_name']} Lineup")
        active_a = st.selectbox("Select Scorer/Fouler (Home)", st.session_state.match_data['team_a_roster'])
        
        # Big Buttons for Easy Clicking
        btn_a1, btn_a2, btn_a3, btn_a4 = st.columns(4)
        if btn_a1.button("+1 FT", key="a1"): log_event(quarter, st.session_state.match_data['team_a_name'], active_a, "Free Throw", 1)
        if btn_a2.button("+2 PTS", key="a2"): log_event(quarter, st.session_state.match_data['team_a_name'], active_a, "Field Goal", 2)
        if btn_a3.button("+3 PTS", key="a3"): log_event(quarter, st.session_state.match_data['team_a_name'], active_a, "3-Pointer", 3)
        if btn_a4.button("FOUL", key="af"): log_event(quarter, st.session_state.match_data['team_a_name'], active_a, "Personal Foul", 0)

    with row_act2:
        st.error(f"🏀 {st.session_state.match_data['team_b_name']} Lineup")
        active_b = st.selectbox("Select Scorer/Fouler (Away)", st.session_state.match_data['team_b_roster'])
        
        btn_b1, btn_b2, btn_b3, btn_b4 = st.columns(4)
        if btn_b1.button("+1 FT", key="b1"): log_event(quarter, st.session_state.match_data['team_b_name'], active_b, "Free Throw", 1)
        if btn_b2.button("+2 PTS", key="b2"): log_event(quarter, st.session_state.match_data['team_b_name'], active_b, "Field Goal", 2)
        if btn_b3.button("+3 PTS", key="b3"): log_event(quarter, st.session_state.match_data['team_b_name'], active_b, "3-Pointer", 3)
        if btn_b4.button("FOUL", key="bf"): log_event(quarter, st.session_state.match_data['team_b_name'], active_b, "Personal Foul", 0)

elif nav == "Analytics & Reports":
    st.title("📊 Post-Game Analysis")
    
    if st.session_state.match_data['match_log']:
        df = pd.DataFrame(st.session_state.match_data['match_log'])
        
        # Top Level Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Leading Scorer", df.groupby('Player')['Points'].sum().idxmax())
        m2.metric("Total Fouls", len(df[df['Event'] == "Personal Foul"]))
        m3.metric("Highest Scoring Qtr", df.groupby('Quarter')['Points'].sum().idxmax())

        st.divider()
        
        # Quarter Flow Chart
        st.subheader("Scoring Flow by Quarter")
        qtr_chart = df.groupby(['Quarter', 'Team'])['Points'].sum().reset_index()
        st.bar_chart(qtr_chart, x="Quarter", y="Points", color="Team", stack=False)

        # Detailed Box Score
        st.subheader("Official Box Score")
        box_score = df.groupby(['Team', 'Player']).agg({
            'Points': 'sum',
            'Event': 'count' # Simplified: counts total actions involved in
        }).rename(columns={'Event': 'Actions Involved'}).reset_index()
        
        st.dataframe(box_score, use_container_width=True)
        
        # CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Official Match Report (CSV)", data=csv, file_name="match_report.csv", mime="text/csv")
        
    else:
        st.info("Match hasn't started. No data available.")
