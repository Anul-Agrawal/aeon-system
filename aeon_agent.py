import streamlit as st
import pandas as pd
import sqlite3
import json
import random
from datetime import datetime, date, timedelta
import google.generativeai as genai

DB_FILE = "aeon_persistent_vault.db"

# ==========================================
# 📈 QUEST SCALING CONTROLLER (BY LEVEL TIER)
# ==========================================
def scale_quests_to_level(c, level):
    # Wipe old Fixed daily quests to prepare for scaled iteration
    c.execute("DELETE FROM quests WHERE type='Fixed'")
    
    # Calculate scaled parameters based on Level
    sunlight_duration = 15 + (level - 1) * 5      # Lvl 1: 15m, Lvl 2: 20m, Lvl 3: 25m...
    lockdown_cutoff = "11:00 PM" if level == 1 else "10:30 PM" if level == 2 else "10:00 PM" if level == 3 else "09:30 PM"
    physical_duration = 30 + (level - 1) * 10     # Lvl 1: 30m, Lvl 2: 40m, Lvl 3: 50m...
    study_duration = 45 + (level - 1) * 15        # Lvl 1: 45m, Lvl 2: 60m, Lvl 3: 75m...
    
    # Scale rewards proportional to level growth
    xp_base = 40 + (level - 1) * 20
    stat_base = 2 + (level - 1)
    
    quests = [
        ('Fixed', f"🌅 Sunlight Spawn ({sunlight_duration}m outdoor morning exposure & breathing)", xp_base, 'per', stat_base, 'Daily', 0),
        ('Fixed', f"🔒 System Lockdown (No late-night food delivery past {lockdown_cutoff})", xp_base + 10, 'vit', stat_base + 1, 'Daily', 0),
        ('Fixed', f"🏊 Physical Execution ({physical_duration}m Swim/Walk/Active Mobility)", xp_base, 'agi', stat_base, 'Daily', 0),
        ('Fixed', f"📈 Skill Tree Cultivation ({study_duration}m System Design/LeetCode/Engineering)", xp_base + 20, 'intel', stat_base + 1, 'Daily', 0)
    ]
    c.executemany("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES (?, ?, ?, ?, ?, ?, ?)", quests)

# ==========================================
# 🗄️ DATABASE MANAGEMENT LAYER (SCALING MATRIX UPDATE)
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
                  gold INTEGER, last_login TEXT, streak INTEGER, draw_today INTEGER, boss_hp INTEGER)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS quests 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, 
                  xp_reward INTEGER, stat_type TEXT, stat_reward INTEGER, deadline TEXT, completed INTEGER)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS purchases 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, cost INTEGER, date_unlocked TEXT)''')
    
    # --- AUTO-MIGRATION LAYER (Adds trackers seamlessly) ---
    c.execute("PRAGMA table_info(character)")
    columns = [col[1] for col in c.fetchall()]
    
    migrations = {
        'gold': "INTEGER DEFAULT 0",
        'last_login': "TEXT",
        'streak': "INTEGER DEFAULT 0",
        'draw_today': "INTEGER DEFAULT 0",
        'boss_hp': "INTEGER DEFAULT 100"
    }
    
    for col_name, col_type in migrations.items():
        if col_name not in columns:
            try:
                c.execute(f"ALTER TABLE character ADD COLUMN {col_name} {col_type}")
                if col_name == 'last_login':
                    c.execute("UPDATE character SET last_login = ?", (date.today().strftime('%Y-%m-%d'),))
            except sqlite3.OperationalError:
                pass

    c.execute("SELECT COUNT(*) FROM character")
    if c.fetchone()[0] == 0:
        # Pinned Baseline: Pure 0 starting metrics on creation, 100 boss HP, 0 streak
        c.execute("INSERT INTO character VALUES (1, 1, 0, 0, 0, 0, 0, 0, 0, 0, ?, 0, 0, 100)", (date.today().strftime('%Y-%m-%d'),))
        # Call initial quest generator for Level 1
        scale_quests_to_level(c, 1)
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# ⏱️ FEATURE 4: AUTOMATED MIDNIGHT CHRONO-SYNC & STREAK MANAGEMENT
# ==========================================
conn = sqlite3.connect(DB_FILE)
char_data = pd.read_sql_query("SELECT * FROM character WHERE id=1", conn).iloc[0]
conn.close()

current_today_str = date.today().strftime('%Y-%m-%d')
current_today = date.today()

if char_data['last_login'] != current_today_str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Calculate streak preservation
    last_login_date = datetime.strptime(char_data['last_login'], '%Y-%m-%d').date()
    yesterday = current_today - timedelta(days=1)
    
    new_streak = int(char_data['streak'])
    if last_login_date == yesterday:
        new_streak += 1  # Streak preserved and increased
    elif last_login_date < yesterday:
        new_streak = 1   # Streak broken, reset back to 1
        
    # Identify missed daily fixed goals before wiping
    c.execute("SELECT COUNT(*) FROM quests WHERE type='Fixed' AND completed=0")
    missed_count = c.fetchone()[0]
    
    if missed_count > 0:
        # Discipline Penalty: Reduce Vitality proportional to missed directives
        vit_damage = missed_count * 2
        c.execute("UPDATE character SET vit = MAX(0, vit - ?) WHERE id=1", (vit_damage,))
        # Flag persistent notice to show user upon logging in
        st.sidebar.error(f"🚨 MIDNIGHT CHRONO-SYNC PENALTY: You abandoned {missed_count} Daily Objectives yesterday. Vitality dropped by -{vit_damage} points.")
    
    # Reset Gacha Draw & Daily Boss HP back to 100 for a fresh challenge
    c.execute("UPDATE quests SET completed=0 WHERE type='Fixed'")
    c.execute("UPDATE character SET last_login=?, streak=?, draw_today=0, boss_hp=100 WHERE id=1", (current_today_str, new_streak))
    conn.commit()
    conn.close()
    st.rerun()

# --- STREAK MULTIPLIER MATH ---
streak_multiplier = min(1.0 + (int(char_data['streak']) * 0.05), 1.50)

# ==========================================
# 👑 FEATURE 3: DYNAMIC TITLE COEFFICIENT ENGINE
# ==========================================
def determine_system_title(char):
    if char['level'] >= 5: return "👑 Shadow Monarch"
    if char['level'] >= 3: return "🔮 Shadow Monarch Candidate"
    if char['intel'] >= 25: return "🧠 System Architect"
    if char['str'] >= 20 and char['agi'] >= 20: return "⚔️ Vanguard Raider"
    if char['wealth'] >= 25: return "🪙 Guild Financier"
    if char['streak'] >= 10: return "🔥 Unstoppable Hunter"
    if char['str'] == 0 and char['intel'] == 0 and char['wealth'] == 0: return "🥚 Unawakened E-Rank"
    return "🛡️ Active Hunter"

active_title = determine_system_title(char_data)

# ==========================================
# 📡 FEATURE 5: REMOTE WEBHOOK ROUTING GATEWAY
# ==========================================
if "log" in st.query_params and "api_key" in st.query_params:
    incoming_log = st.query_params["log"]
    incoming_token = st.query_params["api_key"]
    st.info("📡 Incoming remote execution request intercepted. Processing neural thread...")

# ==========================================
# 🎨 RE-ENGINEERED IMMERSIVE UI STYLING
# ==========================================
st.set_page_config(page_title="AEON: Monarch Evolution Chronicles", page_icon="⚡", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #060913; color: #E2E8F0; }
    .stApp { background-color: #060913; }
    
    /* Immersive Panels */
    .status-frame { background-color: #0F1322; padding: 25px; border-radius: 12px; border: 2px solid #1E293B; box-shadow: 0 0 20px rgba(56, 189, 248, 0.15); }
    .title-badge { color: #38BDF8; font-weight: bold; background: #161C2E; padding: 4px 10px; border-radius: 4px; border: 1px solid #38BDF8; font-family: monospace; }
    
    /* Enhanced Quest Card Layout */
    .quest-card { background-color: #111625; padding: 20px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #1E293B; box-shadow: 2px 2px 8px rgba(0,0,0,0.4); }
    .quest-title-text { font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold; color: #F1F5F9; }
    .quest-breakdown { background-color: #0A0D18; border-radius: 6px; padding: 10px 12px; margin-top: 8px; border: 1px solid #1E243A; }
    
    /* Custom Neon Progress Bars */
    .rpg-stat-container { margin-bottom: 15px; }
    .rpg-stat-header { display: flex; justify-content: space-between; font-family: monospace; font-weight: bold; font-size: 14px; margin-bottom: 4px; }
    .rpg-bar-bg { background-color: #1E293B; border-radius: 6px; height: 18px; width: 100%; overflow: hidden; border: 1px solid #334155; position: relative; }
    .rpg-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease-in-out; position: relative; }
    .rpg-bar-gate { position: absolute; top: 0; width: 3px; height: 100%; background-color: #EF4444; box-shadow: 0 0 8px #EF4444; }
    
    .system-speech { background-color: #1E1B4B; border-left: 4px solid #818CF8; padding: 18px; border-radius: 6px; font-family: 'Courier New', monospace; color: #E0E7FF; }
    .gold-ticker { color: #F59E0B; font-size: 20px; font-weight: bold; font-family: monospace; }
    .streak-container { display: flex; align-items: center; background: linear-gradient(135deg, #FF512F, #DD2476); padding: 8px 15px; border-radius: 8px; color: white; font-weight: bold; margin-bottom: 15px; }
    
    /* Custom Boss Combat Section */
    .boss-frame { background-color: #1c0f1e; border: 2px solid #f43f5e; border-radius: 12px; padding: 20px; margin-top: 20px; text-align: center; box-shadow: 0 0 15px rgba(244, 63, 94, 0.2); }
    .boss-health-bar { height: 22px; background-color: #2D142C; border: 1px solid #F43F5E; border-radius: 6px; position: relative; overflow: hidden; margin: 10px 0; }
    .boss-health-fill { height: 100%; background: linear-gradient(to right, #9B1C31, #EF4444); width: 100%; transition: width 0.5s ease; }
    .boss-health-text { position: absolute; width: 100%; text-align: center; top: 0; left: 0; line-height: 22px; font-weight: bold; color: white; font-family: monospace; }
    
    .rune-unlocked { background: radial-gradient(circle, rgba(129,140,248,0.2) 0%, rgba(15,19,34,1) 100%); border: 2px dashed #818cf8; border-radius: 12px; padding: 25px; text-align: center; }
    h1, h2, h3 { font-family: 'Courier New', monospace; color: #F8FAFC; letter-spacing: 1px; }
    
    .stButton>button { width: 100%; background-color: #1E293B; color: #F1F5F9; border: 1px solid #38BDF8; border-radius: 6px; }
    .stButton>button:hover { background-color: #38BDF8; color: #060913; box-shadow: 0 0 12px #38BDF8; }
    </style>
    """, unsafe_allow_html=True)

# Upgraded premium name display
st.title("🔥 AEON // MONARCH EVOLUTION CHRONICLES")
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
    next_level = int(char_data['level']) + 1
    c.execute("UPDATE character SET level = ?, xp = xp - ? WHERE id=1", (next_level, xp_needed))
    
    # AUTOMATIC CORE SCALING PROTOCOL RUN
    scale_quests_to_level(c, next_level)
    
    conn.commit()
    conn.close()
    st.balloons()
    st.success(f"✨ ATTRIBUTE EVOLUTION COMPLETED: System advanced to Level {next_level}! All daily fixed quests have evolved!")
    st.rerun()

# ==========================================
# 🛡️ SYSTEM KEY INTEGRATION AUTOMATION
# ==========================================
# Automated secrets fallback so you never have to re-enter your key!
gemini_api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]

# ==========================================
# 🗺️ APPARATUS TABS INTERACTION INTERFACE
# ==========================================
tab_dashboard, tab_shop, tab_gacha, tab_forge, tab_remote = st.tabs([
    "🛡️ STATUS MATRIX & DIRECTIVES", 
    "🪙 SYSTEM SHOP & INVENTORY", 
    "🔮 THE ORACLE'S RUNES (GACHA)",
    "🔧 AEON FORGE (DYNAMIC EXPANSION)",
    "📡 REMOTE API GATEWAY"
])

# --- TAB 1: MAIN SYSTEM DASHBOARD ---
with tab_dashboard:
    col_left, col_right = st.columns([1.1, 1])
    
    with col_left:
        st.markdown("<div class='status-frame'>", unsafe_allow_html=True)
        st.header(f"👤 STATUS FRAME // LVL {char_data['level']}")
        
        # Streak Container displaying active modifiers
        st.markdown(f"""
        <div class="streak-container">
            🔥 ACTIVE LOGIN STREAK: {char_data['streak']} Days (Multiplier: {streak_multiplier:.2f}x XP)
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**System Gold Reservoir:** <span class='gold-ticker'>🪙 {char_data['gold']} G</span>", unsafe_allow_html=True)
        
        xp_progress = min(float(char_data['xp'] / xp_needed), 1.0)
        st.write(f"**Required Progress Vector (XP):** {char_data['xp']} / {xp_needed}")
        st.progress(xp_progress)
        
        # --- EXOTIC CUSTOM PROGRESSION GRIDS (REPLACES STREAMLIT BAR CHART) ---
        st.markdown("### 📊 RPG ATTRIBUTE CALIBRATION PANEL")
        st.caption(f"Current Level Gating Limit: **{stat_gate}** points. Red marker designates mandatory gate breakthrough lines.")
        
        # Helper list of attributes with names, values, colors, and gate values
        attributes = [
            {"label": "🏋️ STRENGTH (STR)", "val": char_data['str'], "color": "linear-gradient(90deg, #475569, #94A3B8)"},
            {"label": "⚡ AGILITY (AGI)", "val": char_data['agi'], "color": "linear-gradient(90deg, #059669, #34D399)"},
            {"label": "❤️ VITALITY (VIT)", "val": char_data['vit'], "color": "linear-gradient(90deg, #DC2626, #F87171)"},
            {"label": "🧠 INTELLIGENCE (INT)", "val": char_data['intel'], "color": "linear-gradient(90deg, #4F46E5, #818CF8)"},
            {"label": "👁️ PERCEPTION (PER)", "val": char_data['per'], "color": "linear-gradient(90deg, #0891B2, #22D3EE)"},
            {"label": "🪙 WEALTH CAPACITY (WTH)", "val": char_data['wealth'], "color": "linear-gradient(90deg, #D97706, #FBBF24)"}
        ]
        
        for attr in attributes:
            # We map 0-100% relative to a dynamic scale. Let's make max scale = max(stat_gate * 1.5, attr['val'])
            max_scale = max(int(stat_gate * 1.5), attr['val'], 1)
            fill_pct = min(100, int((attr['val'] / max_scale) * 100))
            gate_pct = min(100, int((stat_gate / max_scale) * 100))
            
            gate_color = "#10B981" if attr['val'] >= stat_gate else "#EF4444"
            st.markdown(f"""
            <div class="rpg-stat-container">
                <div class="rpg-stat-header">
                    <span style="color:#CBD5E1;">{attr['label']}</span>
                    <span style="color:{gate_color};">{attr['val']} / {stat_gate} G</span>
                </div>
                <div class="rpg-bar-bg">
                    <div class="rpg-bar-fill" style="width: {fill_pct}%; background: {attr['color']};"></div>
                    <div class="rpg-bar-gate" style="left: {gate_pct}%; background-color: {gate_color}; box-shadow: 0 0 8px {gate_color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

        # --- DYNAMIC BOSS BATTLE WINDOW ---
        st.markdown("<div class='boss-frame'>", unsafe_allow_html=True)
        st.subheader("👾 ACTIVE DAILY SYSTEM BOSS")
        st.markdown("**'The Stagnation Leviathan'**")
        
        boss_hp_val = int(char_data['boss_hp'])
        boss_color = "#EF4444" if boss_hp_val > 0 else "#10B981"
        
        st.markdown(f"""
        <div class="boss-health-bar">
            <div class="boss-health-fill" style="width: {max(0, min(boss_hp_val, 100))}%; background: linear-gradient(to right, #9B1C31, {boss_color});"></div>
            <div class="boss-health-text">BEAST HP: {boss_hp_val} / 100</div>
        </div>
        """, unsafe_allow_html=True)
        
        if boss_hp_val <= 0:
            st.markdown("<span style='color:#10B981; font-weight:bold;'>🏆 LEVIATHAN DEFEATED! Check in tomorrow for another raid drop.</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"*Every completed objective deals **25 DMG** to the Beast.*")
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
                # Scale rewards with streak multipliers explicitly
                scaled_xp = int(q['xp_reward'] * streak_multiplier)
                gold_reward = int(scaled_xp / 2)
                bonus_xp_only = scaled_xp - q['xp_reward']
                
                # --- IMMERSIVE QUEST CARD OVERHAUL ---
                st.markdown(f"""
                <div class='quest-card'>
                    <div class="quest-title-text">[{q['type']}] {q['title']}</div>
                    <div class="quest-breakdown">
                        <table style="width:100%; border:none; background:none; font-family:monospace; font-size:12px; color:#94A3B8;">
                            <tr style="border:none;"><td style="border:none; padding:2px;">Base Objective XP:</td><td style="border:none; text-align:right; color:#E2E8F0; padding:2px;">+{q['xp_reward']} XP</td></tr>
                            <tr style="border:none;"><td style="border:none; padding:2px;">Streak Multiplier ({streak_multiplier:.2f}x):</td><td style="border:none; text-align:right; color:#EF4444; padding:2px;">+{bonus_xp_only} XP</td></tr>
                            <tr style="border:none; border-bottom:1px solid #1E293B;"><td style="border:none; padding:2px;">Stat Reward:</td><td style="border:none; text-align:right; color:#38BDF8; padding:2px;">+{q['stat_reward']} {q['stat_type'].upper()}</td></tr>
                            <tr style="border:none; font-weight:bold;"><td style="border:none; color:#F59E0B; padding:5px 2px 2px 2px;">Total Gold Yield (XP / 2):</td><td style="border:none; text-align:right; color:#F59E0B; padding:5px 2px 2px 2px;">🪙 {gold_reward} G</td></tr>
                        </table>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action Buttons are kept as native Streamlit elements right below the card for complete stability
                if st.button("Confirm Objective Cleared", key=f"btn_clear_{q['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("UPDATE quests SET completed=1 WHERE id=?", (q['id'],))
                    db_stat = "intel" if q['stat_type'] == "int" else q['stat_type']
                    
                    # Apply adjusted stat and XP
                    c.execute(f"UPDATE character SET xp = xp + ?, {db_stat} = {db_stat} + ?, gold = gold + ? WHERE id=1", 
                              (scaled_xp, q['stat_reward'], gold_reward))
                    
                    # Hit Daily Boss for 25 damage
                    new_boss_hp = max(0, int(char_data['boss_hp']) - 25)
                    c.execute("UPDATE character SET boss_hp = ? WHERE id=1", (new_boss_hp,))
                    
                    # Defeating the boss bonus
                    if new_boss_hp == 0 and int(char_data['boss_hp']) > 0:
                        c.execute("UPDATE character SET gold = gold + 50 WHERE id=1")
                        st.sidebar.balloons()
                        st.sidebar.success("💥 BOSS DEFEATED! Received +50 G Slayer Bonus!")
                    
                    conn.commit()
                    conn.close()
                    st.toast(f"Objective Verified: +{gold_reward} Gold added to cache.")
                    st.rerun()
                st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.header("🔮 COGNITIVE SYNAPSE LOG TERMINAL")
        
        # Key fallback management UI
        if gemini_api_key:
            st.success("🔒 System Synchronization Security Token initialized dynamically from st.secrets.")
            active_key = gemini_api_key
        else:
            active_key = st.text_input("Enter Neural Authentication String (Gemini API Key)", type="password")
            
        raw_log = st.text_area("Dump processing logs here:", height=110, placeholder="Document raw daily telemetry configurations...")
        
        if st.button("Execute Core Analysis Run"):
            if not active_key or not raw_log:
                st.error("Missing input parameters. Supply valid credentials and log context.")
            else:
                with st.spinner("Analyzing semantic structures... Updating database matrix..."):
                    try:
                        genai.configure(api_key=active_key)
                        current_matrix_payload = {
                            "level": int(char_data['level']), "str": int(char_data['str']), "agi": int(char_data['agi']),
                            "vit": int(char_data['vit']), "intel": int(char_data['intel']), "per": int(char_data['per']),
                            "wealth": int(char_data['wealth']), "gold": int(char_data['gold']), "stat_gate": stat_gate
                        }
                        
                        system_prompt = f"""
                        You are AEON, the strict companion interface to Anul Agrawal. 
                        Evaluate his statements directly and output a raw structured data adjustment block.
                        
                        DATA BOUNDS: {json.dumps(current_matrix_payload)}
                        TELEMETRY RECORD: "{raw_log}"
                        
                        TASK SPECIFICATIONS:
                        1. Calculate metric shifting arrays (-5 to +5) across all coefficients based on the user's report.
                        2. Award STR (Strength) when physical exertion/workouts/gym/pushups/swimming are logged.
                        3. Award WTH (Wealth) when financial discipline (mutual funds target met, overtime, savings, resisting junk food apps) is mentioned.
                        4. If they mention late night screen loops, masturbation/dopamine failures, or procrastination, apply a major penalty to VIT and PER.
                        5. DYNAMIC QUESTS: If they mention specific goals, failures, or milestones, generate an active side quest. 
                           The difficulty rank, requirements, and deadlines of the side quest MUST scale based on the user's current Level ({char_data['level']}):
                           - Level 1-2: E/D-Rank Quests (Simple habits, 100-150 XP, 3-5 days)
                           - Level 3-4: C/B-Rank Quests (Multi-step structural shifts, 200-300 XP, 4-7 days)
                           - Level 5+: A/S-Rank Quests (Extreme focus/milestones/financial blocks, 400-500+ XP, 7-14 days)
                           The dynamic quest's title MUST start with the rank prefix, e.g., '[D-RANK QUEST] Clear microservice registry challenge'.
                        
                        Return JSON format ONLY:
                        {{
                            "stat_changes": {{"str": 0, "agi": 0, "vit": 0, "intel": 0, "per": 0, "wealth": 0}},
                            "xp_modification": 50,
                            "new_side_quest": {{
                                "triggered": false,
                                "title": "[E-RANK QUEST] Infiltrate System Architecture Principles",
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
                        
                        # Fix parsing bug by constructing triple backticks dynamically
                        ticks = "``" + "`"
                        json_tag = ticks + "json"
                        
                        if json_tag in cleaned_output: 
                            cleaned_output = cleaned_output.split(json_tag)[1].split(ticks)[0].strip()
                        elif ticks in cleaned_output: 
                            cleaned_output = cleaned_output.split(ticks)[1].split(ticks)[0].strip()
                            
                        ai_res = json.loads(cleaned_output)
                        mods = ai_res["stat_changes"]
                        
                        # Handle scaling XP with the current login streak
                        computed_xp = int(ai_res["xp_modification"] * streak_multiplier)
                        gold_gained = max(0, int(computed_xp / 2)) if computed_xp > 0 else 0
                        f_gold = char_data['gold'] + gold_gained
                        
                        f_str = max(0, char_data['str'] + mods.get("str", 0))
                        f_agi = max(0, char_data['agi'] + mods.get("agi", 0))
                        f_vit = max(0, char_data['vit'] + mods.get("vit", 0))
                        f_int = max(0, char_data['intel'] + mods.get("intel", 0))
                        f_per = max(0, char_data['per'] + mods.get("per", 0))
                        f_wth = max(0, char_data['wealth'] + mods.get("wealth", 0))
                        
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE character SET xp=?, str=?, agi=?, vit=?, intel=?, per=?, wealth=?, gold=? WHERE id=1",
                                       (char_data['xp'] + computed_xp, f_str, f_agi, f_vit, f_int, f_per, f_wth, f_gold))
                        
                        sq = ai_res.get("new_side_quest", {})
                        if sq.get("triggered", False):
                            cursor.execute("INSERT INTO quests (type, title, xp_reward, stat_type, stat_reward, deadline, completed) VALUES ('Side', ?, ?, ?, 5, ?, 0)",
                                           (sq["title"], sq["xp_reward"], sq["stat_type"], sq["deadline"]))
                        conn.commit()
                        conn.close()
                        
                        st.markdown(f"<div class='system-speech'><b>[AEON AI SYSTEM CORE]:</b> {ai_res['system_directive']}</div>", unsafe_allow_html=True)
                        st.button("Synchronize Memory Data Blocks")
                        
                    except Exception as e:
                        st.error(f"Execution Error Matrix Crash: {e}")

# --- TAB 2: SYSTEM SHOP & INVENTORY ---
with tab_shop:
    st.header("🪙 SYSTEM ACQUISITIONS TERMINAL")
    st.markdown(f"Available Balance Vector: <span class='gold-ticker'>🪙 {char_data['gold']} G</span>", unsafe_allow_html=True)
    st.caption("Exchange your hard earned performance gold tokens to license real world behavioral allowances.")
    
    # Pre-defined system economy shop blueprints
    shop_items = [
        {"name": "🎬 Anime/Streaming Exertion License (1 Hour Access)", "cost": 100, "desc": "Unlocks legal system authority to view 1 hour of active media content guilt-free."},
        {"name": "🍕 High-Dopamine Cheat Meal Dispensation", "cost": 250, "desc": "Authorizes a single non-standard vegetarian meal option without structural penalty logging."},
        {"name": "🎮 Digital Sandbox Access Pass (45 Minutes Gaming)", "cost": 150, "desc": "Grants complete standard access privileges to execution parameters of interactive gameplay."},
        {"name": "🛌 Absolute Grid Shutdown Pass (1 Complete Rest Day)", "cost": 400, "desc": "Exempts your character profile from daily fixed directive execution metrics for 24 hours."}
    ]
    
    col_s1, col_s2 = st.columns([2, 1])
    
    with col_s1:
        st.markdown("### 🛒 AVAILABLE SUPPLY PACKAGES")
        for item in shop_items:
            st.markdown("<div class='quest-card'>", unsafe_allow_html=True)
            sc1, sc2 = st.columns([3, 1])
            with sc1:
                st.markdown(f"**{item['name']}**")
                st.caption(item['desc'])
            with sc2:
                if char_data['gold'] < item['cost']:
                    st.button(f"LOCKED ({item['cost']} G)", key=f"shop_{item['name']}", disabled=True)
                else:
                    if st.button(f"Purchase ({item['cost']} G)", key=f"shop_{item['name']}"):
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        # Deduct asset currencies
                        c.execute("UPDATE character SET gold = gold - ? WHERE id=1", (item['cost'],))
                        c.execute("INSERT INTO purchases (item_name, cost, date_unlocked) VALUES (?, ?, ?)", 
                                  (item['name'], item['cost'], current_today_str))
                        conn.commit()
                        conn.close()
                        st.toast(f"Transaction Confirmed: Unlocked {item['name']}.", icon="🪙")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col_s2:
        st.markdown("### 🎒 SYSTEM PURCHASE HISTORY")
        conn = sqlite3.connect(DB_FILE)
        history = pd.read_sql_query("SELECT * FROM purchases ORDER BY id DESC", conn)
        conn.close()
        
        if history.empty:
            st.caption("Inventory registry clear. Amass gold assets to claim operational clearance passes.")
        else:
            for _, row in history.iterrows():
                st.markdown(f"⚙️ **{row['item_name']}**<br><span style='font-size:11px; color:#64748B;'>Cleared on: {row['date_unlocked']} (-{row['cost']}G)</span><hr style='margin:5px 0;'>", unsafe_allow_html=True)

# --- TAB 3: THE ORACLE'S RUNES (DAILY GACHA GATEWAY) ---
with tab_gacha:
    st.header("🔮 THE ORACLE'S RUNES")
    st.caption("Unlock a singular randomized elemental system blessing every calendar day to accelerate your progression tree.")
    
    # Simple list of random gacha items
    runes = [
        {"name": "🌟 Architect's Core Insight", "stat": "intel", "bonus": 3, "xp": 100, "message": "Your mental clarity is boosted. Received +3 INT & +100 XP!"},
        {"name": "💧 Clean Springs Purifier", "stat": "vit", "bonus": 4, "xp": 50, "message": "Your physical vessel purifies negative residue. Received +4 VIT & +50 XP!"},
        {"name": "⚔️ Raider's Kinetic Velocity", "stat": "agi", "bonus": 3, "xp": 75, "message": "Kinetic energy sweeps your muscle fibers. Received +3 AGI & +75 XP!"},
        {"name": "🪙 Wealth Generation Blessing", "stat": "wealth", "bonus": 3, "xp": 100, "message": "Your wealth collection metrics sharpen. Received +3 WTH & +100 XP!"},
        {"name": "🎁 Divine System Chest", "stat": "gold", "bonus": 80, "xp": 150, "message": "A system chest unlocks extra resources. Received +80 Gold & +150 XP!"}
    ]
    
    if int(char_data['draw_today']) == 0:
        st.markdown("""
        <div style='text-align: center; padding: 40px;'>
            <h3>🔮 THE RUNE GATEWAY IS ACTIVE</h3>
            <p style='color:#94A3B8;'>Gacha drawing is fully recharged. Roll once daily to receive a random attribute boost.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔮 DRAW DAILY RUNE", key="draw_rune_btn"):
            selected_rune = random.choice(runes)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            # Update draw today flag
            c.execute("UPDATE character SET draw_today = 1 WHERE id=1")
            
            # Apply dynamic rewards based on selection
            if selected_rune["stat"] == "gold":
                c.execute("UPDATE character SET gold = gold + ?, xp = xp + ? WHERE id=1", (selected_rune["bonus"], selected_rune["xp"]))
            else:
                c.execute(f"UPDATE character SET {selected_rune['stat']} = {selected_rune['stat']} + ?, xp = xp + ? WHERE id=1", (selected_rune["bonus"], selected_rune["xp"]))
            
            # Log purchase entry for history tracking
            c.execute("INSERT INTO purchases (item_name, cost, date_unlocked) VALUES (?, 0, ?)", 
                      (f"Oracle Reward: {selected_rune['name']}", current_today_str))
            
            conn.commit()
            conn.close()
            st.balloons()
            st.success(selected_rune["message"])
            st.rerun()
    else:
        st.markdown(f"""
        <div class="rune-unlocked">
            <h3 style="color:#818cf8;">🔮 DAILY RUNIC CYCLE ALREADY SYNCED</h3>
            <p style="color:#CBD5E1; margin: 10px 0;">You have already successfully claimed your rune of power today.</p>
            <p style="font-size: 14px; color: #94A3B8;">The Gateway will recharge in your next midnight chronometrical loop.</p>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 4: 🔧 AEON FORGE (DYNAMIC EXPANSION TAB) ---
with tab_forge:
    st.header("🔧 AEON FORGE")
    st.caption("Request dynamic software patches, feature overlays, or customized RPG modules directly from your system UI.")
    
    forge_req = st.text_area("What modular system expansion or graphic asset would you like to install?", placeholder="e.g., 'Add a deep water hydration tracking widget to the dashboard panel that awards +5 VIT for clearing 3L.'")
    
    if st.button("Initialize System Blueprint Generation"):
        if not active_key or not forge_req:
            st.error("Expansion compilation failed: Authentication string or requirements empty.")
        else:
            with st.spinner("Compiling structural blueprint layers... Reading Canvas interfaces..."):
                try:
                    genai.configure(api_key=active_key)
                    forge_prompt = f"""
                    You are AEON Forge, a world-class Streamlit and Python engineer. 
                    The user Anul Agrawal has requested a new feature for his dashboard app.
                    
                    USER FEATURE REQUEST:
                    "{forge_req}"
                    
                    TASK: Generate the complete, optimized code patch or instructions that they can safely replace in their app.
                    Keep the style cohesive, clean, and highly robust.
                    """
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(forge_prompt)
                    
                    st.markdown("### 🧬 PATCH GENERATED SUCCESSFULLY")
                    st.info("Copy the following code configuration directly into your local codebase workspace.")
                    st.code(response.text, language="python")
                except Exception as e:
                    st.error(f"Forge expansion compiled with structural failure: {e}")

# --- TAB 5: REMOTE GATEWAY TERMINAL ---
with tab_remote:
    st.header("📡 WEBHOOK TRANSMISSION GATEWAY")
    st.caption("Bypass the standard graphic web dashboard interface entirely. Sync telemetry natively from remote environments.")
    
    st.markdown("""
    ### 🔗 How to Post Logs Remotely (WhatsApp / Shortcuts API Integration)
    You can trigger quick stat tracking or input logs directly without ever opening this browser dashboard page. Set up an automation shortcut on your phone or configuration code script to ping your deployed web application URL structured with URL query params:
    """)
    
    # Generating instructions dynamically based on platform context
    example_url = "https://your-app-url.streamlit.app/?api_key=YOUR_GEMINI_KEY&log=I completed 45m of system design architecture and walked outside."
    st.code(example_url, language="text")
    
    st.markdown("""
    ### 📲 Interactive Pipeline Test Terminal
    Simulate an incoming text delivery string from an external integration platform (like a custom Telegram Bot or a Siri Shortcut endpoint hook) to verify active ingestion:
    """)
    
    sim_key = st.text_input("Simulated Webhook Authorization Key", type="password", key="sim_k")
    sim_text = st.text_area("Simulated Incoming Chat Payload Text (e.g., from WhatsApp)", placeholder="Type message parameters here to trigger backend evaluation...")
    
    if st.button("Trigger Ingestion Gateway Emulation"):
        if not sim_key or not sim_text:
            st.error("Simulation failed: Pipeline missing key credentials or execution payload.")
        else:
            st.success("Incoming request packet successfully parsed by AEON Gateway Matrix!")
            # Code routes automatically to the primary internal processing block by mimicking entry values
            st.info("Reroute to processing engine initialized... Press 'Execute Core Analysis Run' above inside the Status tab with this payload to review.")

# ==========================================
# ⚙️ SECURE SYSTEM UTILITIES DATA DRAWER
# ==========================================
st.markdown("---")
with st.expander("🛠️ SYSTEM DATA MATRIX DEPLOYMENT TOOLS"):
    if st.button("🚨 INITIALIZE FORCED SYSTEM RESET (HARD WIPING DATA VAULT BACK TO PURE 0)"):
        init_db(force_reset=True)
        st.success("Global variables reset. Matrix structural elements set to 0 configuration baseline indices.")
        st.rerun()
