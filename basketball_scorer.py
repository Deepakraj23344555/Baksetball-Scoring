import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Pro Basket Manager", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'match_data' not in st.session_state:
    st.session_state.match_data = {
        'team_a_name': "Team A",
        'team_b_name': "Team B",
        'team_a_roster': [], # List of dicts: {'name':, 'jersey':}
        'team_b_roster': [],
        'match_log': [],     # Stores every event: {'qtr', 'time', 'player', 'event'}
        'game_active': False
    }

if 'timer' not in st.session_state:
    st.session_state.timer = {'running': False, 'time_left': 720} # 12 mins in seconds

# --- HELPER FUNCTIONS ---
def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"

def log_event(quarter, team, player, event_type, points=0):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.match_data['match_log'].append({
        'Quarter': quarter,
        'Time': timestamp,
        'Team': team,
        'Player': player,
        'Event': event_type,
        'Points': points
    })
    st.success(f"Recorded: {event_type} for {player}")

# --- TABS FOR WORKFLOW ---
tab1, tab2, tab3 = st.tabs(["1. Team Setup & Roster", "2. Match Console", "3. Reports & Analytics"])

# ==========================================
# TAB 1: TEAM SETUP & ROSTER
# ==========================================
with tab1:
    st.header("Step 1: Team & Roster Registration")
    
    col1, col2 = st.columns(2)
    
    # Team A Setup
    with col1:
        st.session_state.match_data['team_a_name'] = st.text_input("Team A Name", value=st.session_state.match_data['team_a_name'])
        st.subheader(f"Add Player to {st.session_state.match_data['team_a_name']}")
        with st.form("team_a_form", clear_on_submit=True):
            name_a = st.text_input("Player Name")
            jersey_a = st.number_input("Jersey #", min_value=0, max_value=99)
            if st.form_submit_button("Add Player"):
                st.session_state.match_data['team_a_roster'].append(f"{name_a} (#{jersey_a})")
                st.rerun()
        
        st.write("Current Roster:", st.session_state.match_data['team_a_roster'])

    # Team B Setup
    with col2:
        st.session_state.match_data['team_b_name'] = st.text_input("Team B Name", value=st.session_state.match_data['team_b_name'])
        st.subheader(f"Add Player to {st.session_state.match_data['team_b_name']}")
        with st.form("team_b_form", clear_on_submit=True):
            name_b = st.text_input("Player Name")
            jersey_b = st.number_input("Jersey #", min_value=0, max_value=99)
            if st.form_submit_button("Add Player"):
                st.session_state.match_data['team_b_roster'].append(f"{name_b} (#{jersey_b})")
                st.rerun()
        
        st.write("Current Roster:", st.session_state.match_data['team_b_roster'])

# ==========================================
# TAB 2: MATCH CONSOLE
# ==========================================
with tab2:
    st.header("Step 2: Match Controls")
    
    # 2.1 Pre-Match Selections
    with st.expander("Starters Selection & Match Settings", expanded=True):
        col_sets_1, col_sets_2, col_sets_3 = st.columns(3)
        
        with col_sets_1:
            match_num = st.text_input("Match Number", "M-001")
            quarter = st.selectbox("Current Quarter", ["Q1", "Q2", "Q3", "Q4"])
            
        with col_sets_2:
            starters_a = st.multiselect(f"{st.session_state.match_data['team_a_name']} Starters (Pick 5)", 
                                        options=st.session_state.match_data['team_a_roster'],
                                        max_selections=5)
        with col_sets_3:
            starters_b = st.multiselect(f"{st.session_state.match_data['team_b_name']} Starters (Pick 5)", 
                                        options=st.session_state.match_data['team_b_roster'],
                                        max_selections=5)

    if len(starters_a) < 1 or len(starters_b) < 1:
        st.warning("Please select starters to activate the console.")
    else:
        st.divider()
        
        # 2.2 The Timer & Scoreboard
        t_col1, t_col2, t_col3 = st.columns([1, 2, 1])
        with t_col2:
            st.metric(label=f"QTR: {quarter} | Match: {match_num}", value=format_time(st.session_state.timer['time_left']))
            
            # Simple Timer Logic (Manual for stability in web app)
            timer_act = st.radio("Timer Action", ["Pause", "Running"], horizontal=True)
            if timer_act == "Running":
                time.sleep(1)
                st.session_state.timer['time_left'] -= 1
                st.rerun()
                
            if st.button("TIMEOUT (60s)"):
                log_event(quarter, "System", "TIMEOUT", "Timeout Called")
                
        # 2.3 Action Console
        st.subheader("Live Actions")
        act_col1, act_col2 = st.columns(2)
        
        # Team A Actions
        with act_col1:
            st.markdown(f"**{st.session_state.match_data['team_a_name']}**")
            active_player_a = st.selectbox("Select Player A", starters_a)
            if st.button(f"2 Points ({st.session_state.match_data['team_a_name']})"):
                log_event(quarter, st.session_state.match_data['team_a_name'], active_player_a, "Score", 2)
            if st.button(f"3 Points ({st.session_state.match_data['team_a_name']})"):
                log_event(quarter, st.session_state.match_data['team_a_name'], active_player_a, "Score", 3)
            if st.button(f"Foul ({st.session_state.match_data['team_a_name']})"):
                log_event(quarter, st.session_state.match_data['team_a_name'], active_player_a, "Foul", 0)

        # Team B Actions
        with act_col2:
            st.markdown(f"**{st.session_state.match_data['team_b_name']}**")
            active_player_b = st.selectbox("Select Player B", starters_b)
            if st.button(f"2 Points ({st.session_state.match_data['team_b_name']})"):
                log_event(quarter, st.session_state.match_data['team_b_name'], active_player_b, "Score", 2)
            if st.button(f"3 Points ({st.session_state.match_data['team_b_name']})"):
                log_event(quarter, st.session_state.match_data['team_b_name'], active_player_b, "Score", 3)
            if st.button(f"Foul ({st.session_state.match_data['team_b_name']})"):
                log_event(quarter, st.session_state.match_data['team_b_name'], active_player_b, "Foul", 0)

# ==========================================
# TAB 3: REPORTS
# ==========================================
with tab3:
    st.header("Step 3: Detailed Match Reports")
    
    if len(st.session_state.match_data['match_log']) > 0:
        df = pd.DataFrame(st.session_state.match_data['match_log'])
        
        # 3.1 Overall Game Summary
        st.subheader("Overall Scoreboard")
        team_scores = df.groupby('Team')['Points'].sum().reset_index()
        st.dataframe(team_scores, use_container_width=True)
        
        # 3.2 Player-wise Report
        st.subheader("Player Statistics")
        player_stats = df[df['Player'] != "TIMEOUT"].groupby(['Team', 'Player']).agg({
            'Points': 'sum',
            'Event': lambda x: list(x)
        }).reset_index()
        st.dataframe(player_stats, use_container_width=True)

        # 3.3 Quarter-wise Report
        st.subheader("Quarter-wise Breakdown")
        qtr_stats = df.pivot_table(index=['Team'], columns='Quarter', values='Points', aggfunc='sum', fill_value=0)
        st.dataframe(qtr_stats, use_container_width=True)

        # 3.4 Full Log
        with st.expander("View Full Play-by-Play Log"):
            st.dataframe(df)
            
    else:
        st.info("No match data recorded yet. Go to the Console to start the game.")
