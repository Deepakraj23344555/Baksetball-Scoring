import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE CONFIGURATION ---
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
        'team_a': {'name': 'LAKERS', 'score': 0, 'fouls': 0, 'timeouts': 5},
        'team_b': {'name': 'CELTICS', 'score': 0, 'fouls': 0, 'timeouts': 5},
        'quarter': 1,
        'time_remaining': 720, # Default 12 mins
        'quarter_length_mins': 12, 
        'is_running': False,
        'logs': [],
        # Roster: List of dicts
        'roster_a': [], 
        'roster_b': [],
        # On Court: List of player INDICES
        'on_court_a': [],
        'on_court_b': []
    }

# --- 4. HELPER FUNCTIONS ---
def format_clock(seconds):
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

def record_stat(team_key, player_idx, stat_type, val):
    # Update Player Stats
    roster_key = f'roster_{team_key[-1]}'
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

# >>> SIDEBAR: SETUP <<<
with st.sidebar:
    st.header("⚙️ Game Setup")
    
    # RESET BUTTON (Fixes the timeout update issue)
    if st.button("⚠️ NEW GAME / RESET", type="primary"):
        st.session_state.clear()
        st.rerun()

    # TIMER SETTINGS
    st.subheader("⏱ Timer Settings")
    # Using session state to persist preference
    if 'config_qtr_len' not in st.session_state:
        st.session_state.config_qtr_len = 12

    qtr_len = st.number_input("Quarter Duration (Minutes)", min_value=1, max_value=20, value=st.session_state.config_qtr_len)
    
    if qtr_len != st.session_state.config_qtr_len:
        st.session_state.config_qtr_len = qtr_len
        st.session_state.game_state['quarter_length_mins'] = qtr_len
        # Auto-update current time if game hasn't really started
        if st.session_state.game_state['time_remaining'] == 720: 
             st.session_state.game_state['time_remaining'] = qtr_len * 60
             st.rerun()
    
    if st.button("Reset Clock to Full Quarter"):
        st.session_state.game_state['time_remaining'] = qtr_len * 60
        st.session_state.game_state['is_running'] = False
        st.rerun()

    st.divider()

    # TEAM NAMES
    # Re-initialize if cleared
    if 'game_state' not in st.session_state: st.rerun()
    
    st.session_state.game_state['team_a']['name'] = st.text_input("Home Team", st.session_state.game_state['team_a']['name']).upper()
    st.session_state.game_state['team_b']['name'] = st.text_input("Away Team", st.session_state.game_state['team_b']['name']).upper()
    
    st.divider()
    
    # ROSTER MANAGEMENT
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

# >>> SCOREBOARD AREA <<<
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
        </div>
    """, unsafe_allow_html=True)
    
    # TIMER & TIMEOUT BUTTONS
    c1, c2, c3 = st.columns([1, 2, 1])
    
    # Team A Timeout
    with c1:
        if st.button("T.O.\n(Home)"):
            if st.session_state.game_state['team_a']['timeouts'] > 0:
                st.session_state.game_state['team_a']['timeouts'] -= 1
                st.session_state.game_state['logs'].insert(0, {"QTR": st.session_state.game_state['quarter'], "Time": format_clock(st.session_state.game_state['time_remaining']), "Team": st.session_state.game_state['team_a']['name'], "Player": "TEAM", "Event": "TIMEOUT CALLED"})
                st.rerun()
        st.caption(f"{st.session_state.game_state['team_a']['timeouts']} Left")

    # Start/Stop Timer
    with c2:
        # Visual Toggle Button
        btn_label = "⏸ PAUSE" if st.session_state.game_state['is_running'] else "▶ START"
        type_btn = "primary" if not st.session_state.game_state['is_running'] else "secondary"
        
        if st.button(btn_label, type=type_btn, use_container_width=True):
            st.session_state.game_state['is_running'] = not st.session_state.game_state['is_running']
            st.rerun()
            
        if st.button("Next QTR ⏩"):
            st.session_state.game_state['quarter'] += 1
            st.session_state.game_state['time_remaining'] = st.session_state.game_state['quarter_length_mins'] * 60
            st.session_state.game_state['is_running'] = False
            st.rerun()

    # Team B Timeout
    with c3:
        if st.button("T.O.\n(Away)"):
             if st.session_state.game_state['team_b']['timeouts'] > 0:
                st.session_state.game_state['team_b']['timeouts'] -= 1
                st.session_state.game_state['logs'].insert(0, {"QTR": st.session_state.game_state['quarter'], "Time": format_clock(st.session_state.game_state['time_remaining']), "Team": st.session_state.game_state['team_b']['name'], "Player": "TEAM", "Event": "TIMEOUT CALLED"})
                st.rerun()
        st.caption(f"{st.session_state.game_state['team_b']['timeouts']} Left")

with col_sb3:
    st.markdown(f"""
        <div class="scoreboard">
            <div class="team-name">{st.session_state.game_state['team_b']['name']}</div>
            <div class="score-big">{st.session_state.game_state['team_b']['score']}</div>
            <div style="color:red">FOULS: {st.session_state.game_state['team_b']['fouls']}</div>
        </div>
    """, unsafe_allow_html=True)

# >>> COURT ACTION AREA <<<
st.divider()
r_a = st.session_state.game_state['roster_a']
r_b = st.session_state.game_state['roster_b']

if len(r_a) < 5 or len(r_b) < 5:
    st.warning("⚠️ Please add at least 5 players to each roster in the Sidebar to unlock the court.")
else:
    sub_mode = st.checkbox("🔄 SUBSTITUTION MODE (Swap Players)")
    col_court_a, col_court_b = st.columns(2)

    # Function to render team column
    def render_team_col(team_key, roster, on_court_list, header_name):
        st.subheader(f"🏀 {header_name}")
        if len(on_court_list) != 5:
            st.info("Select Starting 5:")
            sel = st.multiselect(f"Starters ({header_name})", range(len(roster)), format_func=lambda x: f"{roster[x]['name']} (#{roster[x]['num']})", max_selections=5, key=f"start_{team_key}")
            if len(sel) == 5 and st.button(f"Confirm {header_name}"):
                if team_key == 'team_a': st.session_state.game_state['on_court_a'] = sel
                else: st.session_state.game_state['on_court_b'] = sel
                st.rerun()
        else:
            for i in on_court_list:
                p = roster[i]
                if sub_mode:
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**#{p['num']} {p['name']}**")
                    if c2.button("SUB", key=f"sub_{team_key}_{i}"):
                        on_court_list.remove(i)
                        st.rerun()
                else:
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                    c1.markdown(f"**#{p['num']}**")
                    if c2.button("+1", key=f"ft_{team_key}_{i}"): record_stat(team_key, i, 'PTS', 1); st.rerun()
                    if c3.button("+2", key=f"fg_{team_key}_{i}"): record_stat(team_key, i, 'PTS', 2); st.rerun()
                    if c4.button("+3", key=f"3p_{team_key}_{i}"): record_stat(team_key, i, 'PTS', 3); st.rerun()
                    if c5.button("FL", key=f"fl_{team_key}_{i}", type="primary"): record_stat(team_key, i, 'FOUL', 0); st.rerun()
            
            if len(on_court_list) < 5:
                 avail = [x for x in range(len(roster)) if x not in on_court_list]
                 new_p = st.selectbox("Sub In:", avail, format_func=lambda x: f"{roster[x]['name']} (#{roster[x]['num']})", key=f"new_sub_{team_key}")
                 if st.button(f"Confirm Sub {header_name}"):
                     on_court_list.append(new_p)
                     st.rerun()

    with col_court_a: render_team_col('team_a', r_a, st.session_state.game_state['on_court_a'], st.session_state.game_state['team_a']['name'])
    with col_court_b: render_team_col('team_b', r_b, st.session_state.game_state['on_court_b'], st.session_state.game_state['team_b']['name'])

# >>> REPORTS AREA <<<
st.divider()
st.header("📊 Official Game Reports")
tab_box, tab_qtr, tab_log = st.tabs(["Box Score (Overall)", "Quarter Analysis", "Full Event Log"])

with tab_box:
    def build_stats(roster, team_name):
        data = []
        for p in roster:
            if p['stats']['pts'] > 0 or p['stats']['fouls'] > 0:
                data.append({'Team': team_name, 'Player': f"#{p['num']} {p['name']}", 'PTS': p['stats']['pts'], 'PF': p['stats']['fouls']})
        return pd.DataFrame(data)

    df_a = build_stats(r_a, st.session_state.game_state['team_a']['name'])
    df_b = build_stats(r_b, st.session_state.game_state['team_b']['name'])
    
    if not df_a.empty or not df_b.empty:
        st.dataframe(pd.concat([df_a, df_b], ignore_index=True), use_container_width=True)
    else:
        st.info("No stats recorded yet.")

with tab_qtr:
    if st.session_state.game_state['logs']:
        df_log = pd.DataFrame(st.session_state.game_state['logs'])
        # Filter for points
        df_scores = df_log[df_log['Event'].str.contains("PTS", na=False)].copy()
        
        if not df_scores.empty:
            df_scores['Points'] = df_scores['Event'].str.extract(r'(\d+)').astype(int)
            qtr_report = df_scores.pivot_table(index='Team', columns='QTR', values='Points', aggfunc='sum', fill_value=0)
            st.table(qtr_report)
        else:
            st.warning("No points scored yet.")

with tab_log:
    if st.session_state.game_state['logs']:
        st.dataframe(pd.DataFrame(st.session_state.game_state['logs']), use_container_width=True)

# --- 6. AUTO-TIMER LOGIC (Must be last) ---
if st.session_state.game_state['is_running']:
    time.sleep(1) # Wait 1 second
    if st.session_state.game_state['time_remaining'] > 0:
        st.session_state.game_state['time_remaining'] -= 1
        st.rerun() # Refresh screen
    else:
        st.session_state.game_state['is_running'] = False # Stop at 0
        st.rerun()
