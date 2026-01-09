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
        'time_remaining': 720, # 12 mins in seconds
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
    
    st.session_state.game_state['team_a']['name'] = st.text_input("Home Team", st.session_state.game_state['team_a']['name']).upper()
    st.session_state.game_state['team_b']['name'] = st.text_input("Away Team", st.session_state.game_state['team_b']['name']).upper()
    
    st.divider()
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
    sub_mode = st.checkbox("🔄 SUBSTITUTION MODE")
    col_court_a, col_court_b = st.columns(2)

    # TEAM A ACTIONS
    with col_court_a:
        st.subheader(f"🏀 {st.session_state.game_state['team_a']['name']}")
        if len(st.session_state.game_state['on_court_a']) != 5:
            st.info("Select Starting 5:")
            sel = st.multiselect("Pick 5 Starters (Home)", range(len(r_a)), format_func=lambda x: f"{r_a[x]['name']} (#{r_a[x]['num']})", max_selections=5, key="start_a")
            if len(sel) == 5 and st.button("Confirm Starters A"):
                st.session_state.game_state['on_court_a'] = sel
                st.rerun()
        else:
            for i in st.session_state.game_state['on_court_a']:
                player = r_a[i]
                if sub_mode:
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**#{player['num']} {player['name']}**")
                    if c2.button("SUB", key=f"sub_a_{i}"):
                         st.session_state.game_state['on_court_a'].remove(i)
                         st.rerun()
                else:
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                    c1.markdown(f"**#{player['num']}**")
                    if c2.button("+1", key=f"ft_a_{i}"): record_stat('team_a', i, 'PTS', 1); st.rerun()
                    if c3.button("+2", key=f"fg_a_{i}"): record_stat('team_a', i, 'PTS', 2); st.rerun()
                    if c4.button("+3", key=f"3p_a_{i}"): record_stat('team_a', i, 'PTS', 3); st.rerun()
                    if c5.button("FL", key=f"fl_a_{i}", type="primary"): record_stat('team_a', i, 'FOUL', 0); st.rerun()
            
            if len(st.session_state.game_state['on_court_a']) < 5:
                 avail = [x for x in range(len(r_a)) if x not in st.session_state.game_state['on_court_a']]
                 new_p = st.selectbox("Sub In:", avail, format_func=lambda x: f"{r_a[x]['name']} (#{r_a[x]['num']})", key="new_sub_a")
                 if st.button("Confirm Sub A"):
                     st.session_state.game_state['on_court_a'].append(new_p)
                     st.rerun()

    # TEAM B ACTIONS
    with col_court_b:
        st.subheader(f"🏀 {st.session_state.game_state['team_b']['name']}")
        if len(st.session_state.game_state['on_court_b']) != 5:
            st.info("Select Starting 5:")
            sel_b = st.multiselect("Pick 5 Starters (Away)", range(len(r_b)), format_func=lambda x: f"{r_b[x]['name']} (#{r_b[x]['num']})", max_selections=5, key="start_b")
            if len(sel_b) == 5 and st.button("Confirm Starters B"):
                st.session_state.game_state['on_court_b'] = sel_b
                st.rerun()
        else:
            for i in st.session_state.game_state['on_court_b']:
                player = r_b[i]
                if sub_mode:
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**#{player['num']} {player['name']}**")
                    if c2.button("SUB", key=f"sub_b_{i}"):
                         st.session_state.game_state['on_court_b'].remove(i)
                         st.rerun()
                else:
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                    c1.markdown(f"**#{player['num']}**")
                    if c2.button("+1", key=f"ft_b_{i}"): record_stat('team_b', i, 'PTS', 1); st.rerun()
                    if c3.button("+2", key=f"fg_b_{i}"): record_stat('team_b', i, 'PTS', 2); st.rerun()
                    if c4.button("+3", key=f"3p_b_{i}"): record_stat('team_b', i, 'PTS', 3); st.rerun()
                    if c5.button("FL", key=f"fl_b_{i}", type="primary"): record_stat('team_b', i, 'FOUL', 0); st.rerun()
            
            if len(st.session_state.game_state['on_court_b']) < 5:
                 avail_b = [x for x in range(len(r_b)) if x not in st.session_state.game_state['on_court_b']]
                 new_p_b = st.selectbox("Sub In:", avail_b, format_func=lambda x: f"{r_b[x]['name']} (#{r_b[x]['num']})", key="new_sub_b")
                 if st.button("Confirm Sub B"):
                     st.session_state.game_state['on_court_b'].append(new_p_b)
                     st.rerun()

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
        st.info("No stats yet.")

with tab_qtr:
    if st.session_state.game_state['logs']:
        df_log = pd.DataFrame(st.session_state.game_state['logs'])
        df_scores = df_log[df_log['Event'].str.contains("PTS", na=False)].copy()
        if not df_scores.empty:
            df_scores['Points'] = df_scores['Event'].str.extract(r'(\d+)').astype(int)
            qtr_report = df_scores.pivot_table(index='Team', columns='QTR', values='Points', aggfunc='sum', fill_value=0)
            st.table(qtr_report)
        else:
            st.write("No scoring events.")

with tab_log:
    if st.session_state.game_state['logs']:
        st.dataframe(pd.DataFrame(st.session_state.game_state['logs']), use_container_width=True)

# --- 6. AUTO-TIMER LOGIC (MUST BE AT END) ---
if st.session_state.game_state['is_running']:
    time.sleep(1) # Wait 1 second
    if st.session_state.game_state['time_remaining'] > 0:
        st.session_state.game_state['time_remaining'] -= 1
        st.rerun() # Refresh screen
    else:
        st.session_state.game_state['is_running'] = False # Stop at 0
        st.rerun()
