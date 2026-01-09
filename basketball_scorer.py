import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE CONFIGURATION (NBA STYLE) ---
st.set_page_config(
    page_title="COURTSIDE PRO | Official Scorer",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
    <style>
    /* Digital Scoreboard Style */
    .scoreboard {
        background-color: #1e1e1e;
        color: #ff3b30; /* LED Red */
        font-family: 'Courier New', Courier, monospace;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #333;
        margin-bottom: 20px;
    }
    .score-big { font-size: 80px; font-weight: bold; color: #fff; }
    .team-name { font-size: 24px; color: #888; text-transform: uppercase; letter-spacing: 2px; }
    .timer-display { font-size: 60px; font-weight: bold; color: #ffcc00; }
    .qtr-display { font-size: 20px; color: #aaa; }
    
    /* Action Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE INITIALIZATION ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'team_a': {'name': 'LAKERS', 'score': 0, 'fouls': 0, 'timeouts': 7},
        'team_b': {'name': 'CELTICS', 'score': 0, 'fouls': 0, 'timeouts': 7},
        'quarter': 1,
        'time_remaining': 720, # 12 mins
        'is_running': False,
        'logs': [],
        # Roster Structure: List of dicts {'name': 'LeBron', 'num': 23, 'stats': {pts, fouls}}
        'roster_a': [], 
        'roster_b': [],
        # On Court: List of player INDICES from the roster list
        'on_court_a': [],
        'on_court_b': []
    }

# --- 4. HELPER FUNCTIONS ---
def format_clock(seconds):
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

def record_stat(team_key, player_idx, stat_type, val):
    # Update Player Stats
    roster_key = f'roster_{team_key[-1]}' # roster_a or roster_b
    player = st.session_state.game_state[roster_key][player_idx]
    
    if stat_type == 'PTS':
        player['stats']['pts'] += val
        st.session_state.game_state[team_key]['score'] += val
        evt_desc = f"+{val} PTS"
    elif stat_type == 'FOUL':
        player['stats']['fouls'] += 1
        st.session_state.game_state[team_key]['fouls'] += 1
        evt_desc = "PERSONAL FOUL"
    
    # Log Event
    st.session_state.game_state['logs'].insert(0, {
        "QTR": st.session_state.game_state['quarter'],
        "Time": format_clock(st.session_state.game_state['time_remaining']),
        "Team": st.session_state.game_state[team_key]['name'],
        "Player": f"#{player['num']} {player['name']}",
        "Event": evt_desc
    })

# --- 5. MAIN INTERFACE ---

# >>> SIDEBAR: SETUP & CONFIGURATION <<<
with st.sidebar:
    st.header("⚙️ Game Setup")
    
    # Team Naming
    st.session_state.game_state['team_a']['name'] = st.text_input("Home Team", st.session_state.game_state['team_a']['name']).upper()
    st.session_state.game_state['team_b']['name'] = st.text_input("Away Team", st.session_state.game_state['team_b']['name']).upper()
    
    st.divider()
    
    # Quick Roster Builder
    st.subheader("Roster Management")
    target_team = st.radio("Select Team to Edit", ["Home", "Away"])
    
    with st.form("add_player"):
        p_name = st.text_input("Player Name")
        p_num = st.number_input("Jersey #", 0, 99)
        if st.form_submit_button("Add to Roster"):
            t_key = 'roster_a' if target_team == "Home" else 'roster_b'
            st.session_state.game_state[t_key].append({
                'name': p_name, 
                'num': p_num, 
                'stats': {'pts': 0, 'fouls': 0}
            })
            st.success(f"Added #{p_num} {p_name}")

# >>> MAIN AREA: SCOREBOARD <<<
# Custom HTML Scoreboard
col_sb1, col_sb2, col_sb3 = st.columns([2, 1.5, 2])

with col_sb1:
    st.markdown(f"""
        <div class="scoreboard">
            <div class="team-name">{st.session_state.game_state['team_a']['name']}</div>
            <div class="score-big">{st.session_state.game_state['team_a']['score']}</div>
            <div style="color:red">FOULS: {st.session_state.game_state['team_a']['fouls']}</div>
        </div>
    """, unsafe_allow_html=True)

with col_sb2:
    st.markdown(f"""
        <div class="scoreboard" style="border-color: #444;">
            <div class="qtr-display">QTR {st.session_state.game_state['quarter']}</div>
            <div class="timer-display">{format_clock(st.session_state.game_state['time_remaining'])}</div>
            <div>MATCH 001</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Timer Controls
    c1, c2 = st.columns(2)
    if c1.button("Start/Stop"):
        st.session_state.game_state['is_running'] = not st.session_state.game_state['is_running']
    if c2.button("Nxt QTR"):
        st.session_state.game_state['quarter'] += 1
        st.session_state.game_state['time_remaining'] = 720

with col_sb3:
    st.markdown(f"""
        <div class="scoreboard">
            <div class="team-name">{st.session_state.game_state['team_b']['name']}</div>
            <div class="score-big">{st.session_state.game_state['team_b']['score']}</div>
            <div style="color:red">FOULS: {st.session_state.game_state['team_b']['fouls']}</div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# >>> ACTIVE FLOOR CONSOLE <<<

# Selector for Starters (If less than 5 selected)
r_a = st.session_state.game_state['roster_a']
r_b = st.session_state.game_state['roster_b']

if len(r_a) < 5 or len(r_b) < 5:
    st.warning("⚠️ Please add at least 5 players to each roster in the Sidebar to unlock the court.")
else:
    # --- SUB MODE TOGGLE ---
    sub_mode = st.checkbox("🔄 SUBSTITUTION MODE (Check this to swap players)")

    col_court_a, col_court_b = st.columns(2)

    # --- TEAM A COURT ---
    with col_court_a:
        st.subheader(f"🏀 {st.session_state.game_state['team_a']['name']} - ON COURT")
        
        # If starters not set, allow selection
        if len(st.session_state.game_state['on_court_a']) != 5:
            st.info("Select Starting 5:")
            # Create a list of names for multiselect
            opts = [f"{p['name']} (#{p['num']})" for p in r_a]
            sel = st.multiselect("Pick 5 Starters", range(len(r_a)), format_func=lambda x: f"{r_a[x]['name']} (#{r_a[x]['num']})", max_selections=5, key="start_a")
            if len(sel) == 5:
                if st.button("Confirm Starters A"):
                    st.session_state.game_state['on_court_a'] = sel
                    st.rerun()
        else:
            # RENDER ACTIVE PLAYERS
            for i in st.session_state.game_state['on_court_a']:
                player = r_a[i]
                
                # Check substitution
                if sub_mode:
                    sub_col1, sub_col2 = st.columns([3, 1])
                    sub_col1.markdown(f"**#{player['num']} {player['name']}**")
                    if sub_col2.button("SUB OUT", key=f"sub_a_{i}"):
                         st.session_state.game_state['on_court_a'].remove(i)
                         st.rerun()
                else:
                    # SCORING CONTROLS
                    p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns([2, 1, 1, 1, 1])
                    p_c1.markdown(f"**#{player['num']} {player['name']}**")
                    if p_c2.button("+1", key=f"ft_a_{i}"): record_stat('team_a', i, 'PTS', 1); st.rerun()
                    if p_c3.button("+2", key=f"fg_a_{i}"): record_stat('team_a', i, 'PTS', 2); st.rerun()
                    if p_c4.button("+3", key=f"3p_a_{i}"): record_stat('team_a', i, 'PTS', 3); st.rerun()
                    if p_c5.button("FL", key=f"fl_a_{i}", type="primary"): record_stat('team_a', i, 'FOUL', 0); st.rerun()
            
            # If sub happened and we have < 5 players, show dropdown to add
            if len(st.session_state.game_state['on_court_a']) < 5:
                 avail_indices = [x for x in range(len(r_a)) if x not in st.session_state.game_state['on_court_a']]
                 new_p = st.selectbox("Sub In:", avail_indices, format_func=lambda x: f"{r_a[x]['name']} (#{r_a[x]['num']})", key="new_sub_a")
                 if st.button("Confirm Sub A"):
                     st.session_state.game_state['on_court_a'].append(new_p)
                     st.rerun()

    # --- TEAM B COURT ---
    with col_court_b:
        st.subheader(f"🏀 {st.session_state.game_state['team_b']['name']} - ON COURT")
        
        if len(st.session_state.game_state['on_court_b']) != 5:
            st.info("Select Starting 5:")
            opts_b = [f"{p['name']} (#{p['num']})" for p in r_b]
            sel_b = st.multiselect("Pick 5 Starters", range(len(r_b)), format_func=lambda x: f"{r_b[x]['name']} (#{r_b[x]['num']})", max_selections=5, key="start_b")
            if len(sel_b) == 5:
                if st.button("Confirm Starters B"):
                    st.session_state.game_state['on_court_b'] = sel_b
                    st.rerun()
        else:
            for i in st.session_state.game_state['on_court_b']:
                player = r_b[i]
                
                if sub_mode:
                    sub_col1, sub_col2 = st.columns([3, 1])
                    sub_col1.markdown(f"**#{player['num']} {player['name']}**")
                    if sub_col2.button("SUB OUT", key=f"sub_b_{i}"):
                         st.session_state.game_state['on_court_b'].remove(i)
                         st.rerun()
                else:
                    p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns([2, 1, 1, 1, 1])
                    p_c1.markdown(f"**#{player['num']} {player['name']}**")
                    if p_c2.button("+1", key=f"ft_b_{i}"): record_stat('team_b', i, 'PTS', 1); st.rerun()
                    if p_c3.button("+2", key=f"fg_b_{i}"): record_stat('team_b', i, 'PTS', 2); st.rerun()
                    if p_c4.button("+3", key=f"3p_b_{i}"): record_stat('team_b', i, 'PTS', 3); st.rerun()
                    if p_c5.button("FL", key=f"fl_b_{i}", type="primary"): record_stat('team_b', i, 'FOUL', 0); st.rerun()
            
            if len(st.session_state.game_state['on_court_b']) < 5:
                 avail_indices_b = [x for x in range(len(r_b)) if x not in st.session_state.game_state['on_court_b']]
                 new_p_b = st.selectbox("Sub In:", avail_indices_b, format_func=lambda x: f"{r_b[x]['name']} (#{r_b[x]['num']})", key="new_sub_b")
                 if st.button("Confirm Sub B"):
                     st.session_state.game_state['on_court_b'].append(new_p_b)
                     st.rerun()

st.divider()

# >>> LIVE PLAY-BY-PLAY FEED <<<
st.subheader("📜 Live Play-by-Play")
if st.session_state.game_state['logs']:
    df_logs = pd.DataFrame(st.session_state.game_state['logs'])
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    st.caption("Waiting for tip-off...")

# --- 6. REPORT GENERATION ---
with st.expander("📊 Generate Official Box Score"):
    if st.button("Generate Report"):
        # Combine rosters and stats
        report_data = []
        for p in st.session_state.game_state['roster_a']:
            report_data.append({'Team': st.session_state.game_state['team_a']['name'], 'Name': p['name'], 'PTS': p['stats']['pts'], 'PF': p['stats']['fouls']})
        for p in st.session_state.game_state['roster_b']:
            report_data.append({'Team': st.session_state.game_state['team_b']['name'], 'Name': p['name'], 'PTS': p['stats']['pts'], 'PF': p['stats']['fouls']})
            
        df_rep = pd.DataFrame(report_data)
        st.table(df_rep)
