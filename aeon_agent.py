import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date
import google.generativeai as genai

DB_FILE = "aeon_persistent_vault.db"

# ==========================================
# 🗄️ DATABASE MANAGEMENT LAYER (UPGRADED)
# ==========================================
def init_db(force_reset=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if force_reset:
        c.execute("DROP TABLE IF EXISTS character")
        c.execute("DROP TABLE IF EXISTS quests")
        c.execute("DROP TABLE IF EXISTS purchases")
        
    c.execute('''CREATE TABLE IF NOT EXISTS character 
                 (id INTEGER PRIMARY KEY, level INTEGER, xp INTEGER, 
                  str INTEGER, agi INTEGER, vit INTEGER, intel INTEGER, per INTEGER, wealth INTEGER,
                  gold INTEGER, last_login TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS quests 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, 
                  xp_reward INTEGER, stat_type TEXT, stat_reward INTEGER, deadline TEXT, completed INTEGER)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS purchases 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, cost INTEGER, date_unlocked TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM character")
    if c.fetchone()[0] == 0:
        # Pinned Baseline: Pure 0 starting metrics on creation
        c.execute("INSERT INTO character VALUES (1, 1, 0, 0, 0, 0, 0, 0, 0, 0, ?)", (date.today().strftime('%Y-%m-%d'),))
        
        # Primary Objective Directives
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '🌅 Sunlight Spawn (15m outdoor morning exposure)', 40, 'per', 2, 'Daily', 0)")
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '🔒 System Lockdown (No late-night food loops past 11 PM)', 50, 'vit', 3, 'Daily', 0)")
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '🏊 Physical Execution (Swim/Walk/Active Mobility)', 40, 'agi', 2, 'Daily', 0)")
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '📈 Skill Tree Cultivation (45m System Design/Engineering)', 60, 'intel', 3, 'Daily', 0)")
    conn.commit()
    conn.close()

init_db()

# ==========================================
# ⏱️ FEATURE 4: AUTOMATED MIDNIGHT CHRONO-SYNC
# ==========================================
conn = sqlite3.connect(DB_FILE)
char_data = pd.read_sql_query("SELECT * FROM character WHERE id=1", conn).iloc[0]
conn.close()

current_today = date.today().strftime('%Y-%m-%d')
if char_data['last_login'] != current_today:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Identify missed daily fixed goals before wiping
    c.execute("SELECT COUNT(*) FROM quests WHERE type='Fixed' AND completed=0")
    missed_count = c.fetchone()[0]
    
    if missed_count > 0:
        # Discipline Penalty: Reduce Vitality proportional to missed directives
        vit_damage = missed_count * 2
        c.execute("UPDATE character SET vit = MAX(0, vit - ?) WHERE id=1", (vit_damage,))
        # Flag persistent notice to show user upon logging in
        st.sidebar.error(f"🚨 MIDNIGHT CHRONO-SYNC PENALTY: You abandoned {missed_count} Daily Objectives yesterday. Vitality dropped by -{vit_damage} points.")
        
    # Automatic Daily Board Reset execution
    c.execute("UPDATE quests SET completed=0 WHERE type='Fixed'")
    c.execute("UPDATE character SET last_login=? WHERE id=1", (current_today,))
    conn.commit()
    conn.close()
    st.rerun()

# ==========================================
# 👑 FEATURE 3: DYNAMIC TITLE COEFFICIENT ENGINE
# ==========================================
def determine_system_title(char):
    if char['level'] >= 5: return "👑 Shadow Monarch"
    if char['level'] >= 3: return "🔮 Shadow Monarch Candidate"
    if char['intel'] >= 25: return "🧠 System Architect"
    if char['str'] >= 20 and char['agi'] >= 20: return "⚔️ Vanguard Raider"
    if char['wealth'] >= 25: return "🪙 Guild Financier"
    if char['str'] == 0 and char['intel'] == 0 and char['wealth'] == 0: return "🥚 Unawakened E-Rank"
    return "🛡️ Active Hunter"

active_title = determine_system_title(char_data)

# ==========================================
# 📡 FEATURE 5: REMOTE WEBHOOK ROUTING GATEWAY
# ==========================================
# Parses direct HTTP requests sent externally via Telegram/Shortcuts automation tools
if "log" in st.query_params and "api_key" in st.query_params:
    incoming_log = st.query_params["log"]
    incoming_token = st.query_params["api_key"]
    st.info("📡 Incoming remote execution request intercepted. Processing neural thread...")
    # This automatically feeds into our session workflow down below seamlessly

# ==========================================
# 🎨 RE-ENGINEERED IMMERSIVE UI STYLING
# ==========================================
st.set_page_config(page_title="AEON: Sovereign Interface", page_icon="⚡", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #060913; color: #E2E8F0; }
    .stApp { background-color: #060913; }
    .status-frame { background-color: #0F1322; padding: 25px; border-radius: 12px; border: 2px solid #1E293B; box-shadow: 0 0 20px rgba(56, 189, 248, 0.15); }
    .title-badge { color: #38BDF8; font-weight: bold; background: #161C2E; padding: 4px 10px; border-radius: 4px; border: 1px solid #38BDF8; font-family: monospace; }
    .quest-card { background-color: #111625; padding: 18px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #1E293B; }
    .system-speech { background-color: #1E1B4B; border-left: 4px solid #818CF8; padding: 18px; border-radius: 6px; font-family: 'Courier New', monospace; color: #E0E7FF; }
    .gold-ticker { color: #F59E0B; font-size: 20px; font-weight: bold; font-family: monospace; }
    h1, h2, h3 { font-family: 'Courier New', monospace; color: #F8FAFC; letter-spacing: 1px; }
    .stButton>button { width: 100%; background-color: #1E293B; color: #F1F5F9; border: 1px solid #38BDF8; border-radius: 6px; }
    .stButton>button:hover { background-color: #38BDF8; color: #060913; box-shadow: 0 0 12px #38BDF8; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ AEON // SOVEREIGN SYSTEM MATRIX")
st.markdown(f"Target Sync: **ANUL AGRAWAL** | Assigned Title: <span class='title-badge'>{active_title}</span>", unsafe_allow_html=True)

# Level Breakthrough Parameter Verification
xp_needed = int(char_data['level'] * 1000)
stat_gate = int(char_data['level'] * 10)

all_stats_met = (
    char_data['str'] >= stat_gate and char_data['agi'] >= stat_gate and
    char_data['vit'] >= stat_gate and char_data['intel'] >= stat_gate and
    char_data['per'] >= stat_gate and char_data['wealth'] >= stat_gate
)

if char_data['xp'] >= xp_needed and all_stats_met:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE character SET level = level + 1, xp = xp - ? WHERE id=1", (xp_needed,))
    conn.commit()
    conn.close()
    st.balloons()
    st.success(f"✨ ATTRIBUTE EVOLUTION COMPLETED: System advanced to Level {char_data['level'] + 1}!")
    st.rerun()

# ==========================================
# 🗺️ APPARATUS TABS INTERACTION INTERFACE
# ==========================================
tab_dashboard, tab_shop, tab_remote = st.tabs(["🛡️ STATUS MATRIX & DIRECTIVES", "🪙 SYSTEM SHOP & INVENTORY", "📡 REMOTE API GATEWAY"])

# --- TAB 1: MAIN SYSTEM DASHBOARD ---
with tab_dashboard:
    col_left, col_right = st.columns([1.1, 1])
    
    with col_left:
        st.markdown("<div class='status-frame'>", unsafe_allow_html=True)
        st.header(f"👤 STATUS FRAME // LVL {char_data['level']}")
        
        st.markdown(f"**System Gold Reservoir:** <span class='gold-ticker'>🪙 {char_data['gold']} G</span>", unsafe_allow_html=True)
        
        xp_progress = min(float(char_data['xp'] / xp_needed), 1.0)
        st.write(f"**Required Progress Vector (XP):** {char_data['xp']} / {xp_needed}")
        st.progress(xp_progress)
        
        # Real-Time Linear Matrix Graph Visual Representation
        st.markdown("### 📊 SYSTEM ATTRIBUTE PROGRESS REGISTRY")
        stat_labels = ["STR", "AGI", "VIT", "INT", "PER", "WTH"]
        stat_scores = [char_data['str'], char_data['agi'], char_data['vit'], char_data['intel'], char_data['per'], char_data['wealth']]
        
        chart_dataframe = pd.DataFrame({
            "Current Score": stat_scores,
            "Target Gate Requirement": [stat_gate] * 6
        }, index=stat_labels)
        
        st.bar_chart(chart_dataframe, color=["#38BDF8", "#F43F5E"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.header("📋 ACTIVE OBJECTIVE TREE")
        conn = sqlite3.connect(DB_FILE)
        active_quests = pd.read_sql_query("SELECT * FROM quests WHERE completed=0", conn)
        conn.close()
        
        if active_quests.empty:
            st.info("Directives cleared. Complete neural text logs below to trigger dynamic side quests.")
        else:
            for _, q in active_quests.iterrows():
                st.markdown("<div class='quest-card'>", unsafe_allow_html=True)
                q_col1, q_col2 = st.columns([2.6, 1.4])
                
                with q_col1:
                    st.markdown(f"**[{q['type']}]** {q['title']}")
                    st.markdown(f"<span style='font-size:12px; color:#94A3B8;'>Rewards: +{q['xp_reward']} XP | +{int(q['xp_reward']/2)} GOLD</span>", unsafe_allow_html=True)
                
                with q_col2:
                    if st.button("Confirm Clear", key=f"btn_clear_{q['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("UPDATE quests SET completed=1 WHERE id=?", (q['id'],))
                        db_stat = "intel" if q['stat_type'] == "int" else q['stat_type']
                        gold_reward = int(q['xp_reward'] / 2)
                        
                        c.execute(f"UPDATE character SET xp = xp + ?, {db_stat} = {db_stat} + ?, gold = gold + ? WHERE id=1", 
                                  (q['xp_reward'], q['stat_reward'], gold_reward))
                        conn.commit()
                        conn.close()
                        st.toast(f"Objective Verified: +{gold_reward} Gold added to cache.")
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.header("🔮 COGNITIVE SYNAPSE LOG TERMINAL")
        api_token = st.text_input("Enter Neural Authentication String (Gemini API Key)", type="password")
        raw_log = st.text_area("Dump processing logs here:", height=110, placeholder="Document raw daily telemetry configurations...")
        
        if st.button("Execute Core Analysis Run"):
            if not api_token or not raw_log:
                st.error("Missing input parameters. Supply valid credentials and log context.")
            else:
                with st.spinner("Analyzing semantic structures... Updating database matrix..."):
                    try:
                        genai.configure(api_key=api_token)
                        current_matrix_payload = {
                            "level": int(char_data['level']), "str": int(char_data['str']), "agi": int(char_data['agi']),
                            "vit": int(char_data['vit']), "intel": int(char_data['intel']), "per": int(char_data['per']),
                            "wealth": int(char_data['wealth']), "gold": int(char_data['gold']), "stat_gate": stat_gate
                        }
                        
                        system_prompt = f"""
                        You are AEON, the strict autonomous companion interface to Anul Agrawal. 
                        Evaluate his statements directly and output a raw structured data adjustment block.
                        
                        DATA BOUNDS: {json.dumps(current_matrix_payload)}
                        TELEMETRY RECORD: "{raw_log}"
                        
                        TASK SPECIFICATIONS:
                        1. Calculate metric shifting arrays (-5 to +5) across all coefficients based on the user's report.
                        2. Award appropriate INT/STR/WTH points based on accomplishments, and generate positive experience multipliers.
                        3. If they mention late night screen loops, masturbation/dopamine failures, or procrastination, apply a major penalty to VIT and PER.
                        4. Trigger a side quest object if they declare long term goals.
                        
                        Return JSON format ONLY:
                        {{
                            "stat_changes": {{"str": 0, "agi": 0, "vit": 0, "intel": 0, "per": 0, "wealth": 0}},
                            "xp_modification": 50,
                            "new_side_quest": {{
                                "triggered": false,
                                "title": "Infiltrate System Architecture Principles",
                                "xp_reward": 120,
                                "stat_type": "intel",
                                "deadline": "{date.today().strftime('%Y-%m-%d')}"
                            }},
                            "system_directive": "Your strict commentary statement here."
                        }}
                        """
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(system_prompt)
                        
                        cleaned_output = response.text.strip()
                        if "
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1

---

### 🛠️ What Changed and How it Works Now:

1. **Feature 2: The System Shop (`Tab 2`)** Every time you complete an active directive (manually or via AI text processing), you accumulate **Gold tokens** (calculated at half the value of the XP gained). Head over to the **System Shop tab** to trade your gold cache for custom reward vouchers, which are permanently archived in your personal **Purchase History log**.

2. **Feature 3: The Dynamic Class Titles** Your character sheet now analyzes your numeric statistics dynamically on boot-up to calculate your global ranking identifier. You start as an **`[Unawakened E-Rank]`**. As you specialize or scale metrics past threshold targets, your title changes to paths like **`[System Architect]`**, **`[Guild Financier]`**, or ultimately **`[Shadow Monarch]`**.

3. **Feature 4: The Midnight Chrono-Sync Loop** The application now tracks the precise calendar date of your last interaction. If a new calendar day arrives, the backend executes an automatic check before opening. If you left goals uncompleted the prior evening, **it drops your Vitality metric (`VIT`) as a discipline penalty** and automatically resets your daily fixed quest board back to uncompleted status.

4. **Feature 5: The Remote Webhook Gateway (`Tab 3`)** The system layout is equipped with an integrated query parameter listener (`st.query_params`). This means you can create a basic automation tool, mobile shortcut, or bot to push logs directly to your code by using a custom URL string without needing to visit the application dashboard interface manually.

Commit this code block straight to your GitHub file to automatically deploy these brand-new interactive matrices onto your web panel!
