import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date
import google.generativeai as genai

DB_FILE = "aeon_persistent_vault.db"

# ==========================================
# DATABASE INITIALIZATION LAYER
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS character 
                 (id INTEGER PRIMARY KEY, level INTEGER, xp INTEGER, 
                  str INTEGER, agi INTEGER, vit INTEGER, intel INTEGER, per INTEGER, wealth INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quests 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, 
                  xp_reward INTEGER, stat_type TEXT, stat_reward INTEGER, deadline TEXT, completed INTEGER)''')
    
    c.execute("SELECT COUNT(*) FROM character")
    if c.fetchone()[0] == 0:
        # Starting profile: Level 1 baseline metrics
        c.execute("INSERT INTO character VALUES (1, 1, 0, 10, 10, 10, 10, 10, 10)")
        # Core Default Fixed Objectives
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '🌅 Sunlight Spawn (15m outdoor morning exposure)', 25, 'per', 2, 'Daily', 0)")
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '🔒 System Lockdown (No late-night food apps past 11 PM)', 30, 'vit', 3, 'Daily', 0)")
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '🏊 Physical Execution (Swim/Walk/Active Mobility)', 25, 'agi', 2, 'Daily', 0)")
        c.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Fixed', '📈 Skill Tree Cultivation (45m Corporate/Engineering Study)', 50, 'intel', 4, 'Daily', 0)")
    conn.commit()
    conn.close()

init_db()

# ==========================================
# APP UI ENGINE STYLING
# ==========================================
st.set_page_config(page_title="AEON: Autonomous System", page_icon="⚡", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #060913; color: #E2E8F0; }
    .stApp { background-color: #060913; }
    .status-frame { background-color: #0F1322; padding: 25px; border-radius: 12px; border: 1px solid #1E293B; }
    .stat-indicator { background-color: #161C2E; padding: 12px; border-radius: 8px; border-left: 4px solid #38BDF8; margin-bottom: 8px; }
    .quest-card { background-color: #111625; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #1E293B; }
    .system-speech { background-color: #1E1B4B; border-left: 4px solid #818CF8; padding: 15px; border-radius: 6px; font-family: monospace; color: #E0E7FF; }
    h1, h2, h3 { font-family: 'Courier New', monospace; color: #F8FAFC; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ AEON // COGNITIVE EVOLUTION ARCHITECTURE")
st.caption("Target Identity Layer: ANUL AGRAWAL | Operational Environment: Verified Synchronization")

# Read Current State Matrix
conn = sqlite3.connect(DB_FILE)
char_data = pd.read_sql_query("SELECT * FROM character WHERE id=1", conn).iloc[0]
xp_needed = int(char_data['level'] * 1000)
stat_gate = int(char_data['level'] * 10)
conn.close()

# Evaluate System Level-Up Gates
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
    st.success(f"✨ BREAKTHROUGH ACCELERATED: AEON Core reached Level {char_data['level'] + 1}!")
    st.rerun()

# Interface Split Layout
col_left, col_right = st.columns([1, 1.2])

# ==========================================
# LEFT PANEL: LIVE GAME STATUS MATRIX
# ==========================================
with col_left:
    st.markdown("<div class='status-frame'>", unsafe_allow_html=True)
    st.header(f"👤 STATUS FRAME // LVL {char_data['level']}")
    
    xp_progress = min(float(char_data['xp'] / xp_needed), 1.0)
    st.write(f"**Required Progress Vector (XP):** {char_data['xp']} / {xp_needed}")
    st.progress(xp_progress)
    
    st.markdown("### 📊 SYSTEM ATTRIBUTE COEFFICIENTS")
    st.caption(f"Current Baseline Level Gating Threshold: **{stat_gate}**")
    
    def render_stat(label, score, gate):
        status = "🟢 MET" if score >= gate else "🔴 LOCKED"
        st.markdown(f"""
        <div class='stat-indicator'>
            <table style='width:100%; border:none; margin:0; padding:0;'>
                <tr style='background:none; border:none;'>
                    <td style='text-align:left; font-weight:bold; color:#94A3B8; border:none; padding:0;'>{label}</td>
                    <td style='text-align:center; font-weight:bold; color:#F1F5F9; border:none; padding:0;'>{score}</td>
                    <td style='text-align:right; font-size:12px; font-weight:bold; border:none; padding:0;'>{status}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    render_stat("🏋️ STRENGTH (STR)", char_data['str'], stat_gate)
    render_stat("⚡ AGILITY (AGI)", char_data['agi'], stat_gate)
    render_stat("❤️ VITALITY (VIT)", char_data['vit'], stat_gate)
    render_stat("🧠 INTELLIGENCE (INT)", char_data['intel'], stat_gate)
    render_stat("👁️ PERCEPTION (PER)", char_data['per'], stat_gate)
    render_stat("🪙 WEALTH CAPACITY (WTH)", char_data['wealth'], stat_gate)
    
    if not all_stats_met:
        st.warning(f"⚠️ EVOLUTION DEADLOCK: Core attributes below level requirement parameter ({stat_gate}). Level-up parameters restricted.")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# RIGHT PANEL: TRUE AI INTEGRATION TERMINAL
# ==========================================
with col_right:
    st.header("📋 UNCOMPLETED MATRIX DIRECTIVES")
    
    conn = sqlite3.connect(DB_FILE)
    active_quests = pd.read_sql_query("SELECT * FROM quests WHERE completed=0", conn)
    conn.close()
    
    for _, q in active_quests.iterrows():
        st.markdown("<div class='quest-card'>", unsafe_allow_html=True)
        q_col1, q_col2 = st.columns([3, 1])
        with q_col1:
            st.markdown(f"**[{q['type']}]** {q['title']}")
            st.markdown(f"<span style='font-size:12px; color:#A1A1AA;'>Rewards: +{q['xp_reward']} XP | +{q['stat_reward']} {q['stat_type'].upper()}</span>", unsafe_allow_html=True)
        with q_col2:
            if q['deadline'] == 'Daily':
                st.info("⏱️ Daily")
            else:
                try:
                    target = datetime.strptime(q['deadline'], "%Y-%m-%d").date()
                    delta = (target - date.today()).days
                    if delta < 0:
                        st.markdown(f"<span style='color:#F43F5E; font-weight:bold;'>💥 OVERDUE ({abs(delta)}d)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:#F59E0B; font-weight:bold;'>⏳ {delta} Days</span>", unsafe_allow_html=True)
                except:
                    st.text(f"📅 {q['deadline']}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🔮 AEON COGNITIVE PROCESSING INTERFACE")
    
    # Enter API credentials directly into web view securely
    api_key_input = st.text_input("Input Secret Access Token (Gemini API Key)", type="password")
    raw_dump = st.text_area("Plow your evening raw narrative text entry here:", height=130, placeholder="Vent freely about expenditures, physical habits, training runs, learning progressions, or late night behavioral slips...")
    
    if st.button("Activate Neural Processing Cycle"):
        if not api_key_input:
            st.error("Authentication Token Missing. Paste your Google AI Studio API Key to enable processing.")
        elif not raw_dump:
            st.error("Input interface registry empty. Provide text parameters to continue.")
        else:
            with st.spinner("AEON cognitive cycles initializing... Reading contextual frameworks..."):
                try:
                    genai.configure(api_key=api_key_input)
                    current_stats_payload = {
                        "level": int(char_data['level']), "xp": int(char_data['xp']), "str": int(char_data['str']),
                        "agi": int(char_data['agi']), "vit": int(char_data['vit']), "intel": int(char_data['intel']),
                        "per": int(char_data['per']), "wealth": int(char_data['wealth']), "stat_gate": stat_gate
                    }
                    
                    master_prompt = f"""
                    You are AEON, an absolute autonomous system voice guiding a user named Anul Agrawal on a strict self-reformation loop. You speak directly, sharply, and with the complete authority of the Solo Leveling System interface.
                    
                    CURRENT SYSTEM LOGISTICS DATA:
                    {json.dumps(current_stats_payload)}
                    
                    USER NATURAL LANGUAGE INGESTION TEXT:
                    "{raw_dump}"
                    
                    INSTRUCTIONS:
                    1. Read the user log context dynamically. Deduce relative points (+ or - ranges from 1 to 5) across STR, AGI, VIT, INT, PER, WTH based on user behaviors. 
                    2. If they hit professional study/coding goals, significantly reward INT and award +50 XP. If they hit mutual fund goals, reward WTH.
                    3. Assess structural vulnerability damage. If they log a pelvic/masturbation relapse or a late-night screen loop pattern, penalize VIT harshly (-4 to -6) and drop total XP.
                    4. DYNAMIC SIDE QUEST GENERATION: Look for long-term targets, micro-stagnations, or skill limits mentioned in their statement. If found, generate a "new_side_quest" object with an actionable title, realistic expiration deadline string (YYYY-MM-DD), and an associated attribute path.
                    
                    Return output strictly as a standardized JSON structure matching this signature:
                    {{
                        "stat_changes": {{"str": 0, "agi": 2, "vit": -4, "intel": 4, "per": -1, "wealth": 0}},
                        "xp_modification": 50,
                        "new_side_quest": {{
                            "triggered": true,
                            "title": "Clear Microservice Registry Challenge",
                            "xp_reward": 150,
                            "stat_type": "intel",
                            "deadline": "{date.today().replace(day=date.today().day+4).strftime('%Y-%m-%d')}"
                        }},
                        "system_directive": "Your protective, assertive system warning / feedback message here."
                    }}
                    """
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(master_prompt)
                    
                    # Clean and secure output streams
                    cleaned_txt = response.text.strip()
                    if "```json" in cleaned_txt:
                        cleaned_txt = cleaned_txt.split("```json")[1].split("```")[0].strip()
                    elif "```" in cleaned_txt:
                        cleaned_txt = cleaned_txt.split("```")[1].split("```")[0].strip()
                        
                    ai_payload = json.loads(cleaned_txt)
                    mods = ai_payload["stat_changes"]
                    
                    # Execute math metrics transformation
                    f_xp = max(0, char_data['xp'] + ai_payload["xp_modification"])
                    f_str = max(0, char_data['str'] + mods.get("str", 0))
                    f_agi = max(0, char_data['agi'] + mods.get("agi", 0))
                    f_vit = max(0, char_data['vit'] + mods.get("vit", 0))
                    f_int = max(0, char_data['intel'] + mods.get("intel", 0))
                    f_per = max(0, char_data['per'] + mods.get("per", 0))
                    f_wth = max(0, char_data['wealth'] + mods.get("wealth", 0))
                    
                    # SYSTEM REGRESSION CHECK
                    # If Vitality falls below 50% of the active Level Gate requirement: Level Regresses.
                    floor_threshold = max(4, int(stat_gate / 2))
                    regressed = False
                    active_lvl = int(char_data['level'])
                    
                    if f_vit < floor_threshold and active_lvl > 1:
                        active_lvl -= 1
                        f_xp = 0
                        f_vit = floor_threshold + 3
                        regressed = True
                    
                    # Commit updates to localized storage blocks
                    conn = sqlite3.connect(DB_FILE)
                    db_cursor = conn.cursor()
                    db_cursor.execute("""UPDATE character SET level=?, xp=?, str=?, agi=?, vit=?, intel=?, per=?, wealth=? WHERE id=1""",
                                      (active_lvl, f_xp, f_str, f_agi, f_vit, f_int, f_per, f_wth))
                    
                    # Inject dynamic side quests generated by the LLM
                    sq = ai_payload.get("new_side_quest", {})
                    if sq.get("triggered", False):
                        db_cursor.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Side', ?, ?, ?, 5, ?, 0)",
                                          (sq["title"], sq["xp_reward"], sq["stat_type"], sq["deadline"]))
                    
                    conn.commit()
                    conn.close()
                    
                    # Render AI Output Reports
                    st.markdown("### 🛰️ TRANSMISSION RESOLVED FROM SYSTEM CORE")
                    st.markdown(f"<div class='system-speech'><b>[AEON SYSTEM VOICE]:</b> {ai_payload['system_directive']}</div>", unsafe_allow_html=True)
                    
                    if regressed:
                        st.error(f"🚨 ALERT: CRITICAL LOSS OF VITALITY RECORDED. SYSTEM MATRIX REGRESSED TO LEVEL {active_lvl}.")
                    else:
                        st.success("State metrics updated into internal long-term sectors.")
                    
                    st.button("Synchronize Display Panels")
                    
                except Exception as err:
                    st.error(f"Cognitive Pipeline Failure: Parse verification error. Clear raw telemetry and try again. Details: {err}")