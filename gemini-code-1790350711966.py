import streamlit as st
import requests
import pandas as pd
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Austin FF F1 Championship",
    page_icon="🏎️",
    layout="wide"
)

# --- CUSTOM CSS (F1 MOTORSPORT DARK THEME) ---
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* F1 Red Accents & Headers */
    h1, h2, h3 {
        color: #FF1801 !important;
        font-family: 'Titillium Web', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Driver Cards */
    .driver-card {
        background-color: #1A1D24;
        border-left: 5px solid #FF1801;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .driver-card-p1 {
        border-left: 5px solid #FFD700 !important;
        background: linear-gradient(135deg, #1A1D24 80%, rgba(255, 215, 0, 0.12));
    }
    .driver-card-p2 {
        border-left: 5px solid #C0C0C0 !important;
    }
    .driver-card-p3 {
        border-left: 5px solid #CD7F32 !important;
    }
    
    /* Metric Display Box */
    .metric-container {
        background-color: #1A1D24;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        border: 1px solid #2D3139;
    }
    .metric-val {
        font-size: 22px;
        font-weight: bold;
        color: #FF1801;
    }
    .metric-lbl {
        font-size: 12px;
        color: #A0AAB8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* F1 Badge */
    .f1-badge {
        background-color: #FF1801;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 14px;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS & API CONFIG ---
LEAGUE_ID = "92432855"
SEASON_ID = "2026"
BASE_URL = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/segments/0/leagues/{LEAGUE_ID}"

# F1 Points System (1st to 10th Place)
F1_POINTS_MAP = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

# --- LIVE DATA FETCHING ---
@st.cache_data(ttl=10)
def fetch_espn_data():
    try:
        # mBoxScore retrieves active play-by-play points during live games
        # _ts timestamp and Cache-Control headers bypass ESPN's Akamai CDN cache
        params = {
            "view": ["mMatchupScore", "mTeam", "mBoxScore", "mRoster"],
            "_ts": int(time.time())
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
        resp = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None

# --- DATA PROCESSING & F1 SCORING ---
def process_f1_standings(data):
    if not data or "teams" not in data:
        return None
        
    teams = {t["id"]: f"{t.get('location', '')} {t.get('nickname', '')}".strip() or f"Team {t['id']}" for t in data.get("teams", [])}
    team_records = {t["id"]: t.get("record", {}).get("overall", {}) for t in data.get("teams", [])}
    
    # Store weekly team scores
    weekly_scores = {}
    schedule = data.get("schedule", [])
    
    for match in schedule:
        week = match.get("matchupPeriodId")
        if not week:
            continue
            
        if week not in weekly_scores:
            weekly_scores[week] = {}
            
        for side in ["home", "away"]:
            if side in match:
                team_id = match[side].get("teamId")
                score = match[side].get("totalPoints", 0)
                if team_id:
                    if team_id not in weekly_scores[week] or score > 0:
                        weekly_scores[week][team_id] = score

    # Include weeks where games are actively being played / points are scored
    active_weeks = [w for w, scores in weekly_scores.items() if sum(scores.values()) > 0]
    
    driver_totals = {tid: {"f1_pts": 0, "total_pf": 0, "wins": 0, "losses": 0, "ties": 0} for tid in teams}
    
    for tid, rec in team_records.items():
        if tid in driver_totals:
            driver_totals[tid]["wins"] = rec.get("wins", 0)
            driver_totals[tid]["losses"] = rec.get("losses", 0)
            driver_totals[tid]["ties"] = rec.get("ties", 0)

    # Award weekly F1 points based on score rankings
    for w in active_weeks:
        scores = weekly_scores[w]
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (tid, pf) in enumerate(ranked, start=1):
            if tid in driver_totals:
                driver_totals[tid]["total_pf"] += pf
                f1_pts = F1_POINTS_MAP.get(rank, 0)
                # +1 Fastest Lap / Highest Weekly Scorer Bonus
                if rank == 1 and pf > 0:
                    f1_pts += 1
                driver_totals[tid]["f1_pts"] += f1_pts

    rows = []
    for tid, name in teams.items():
        stats = driver_totals[tid]
        rows.append({
            "Driver / Team": name,
            "F1 Points": stats["f1_pts"],
            "Total PF": round(stats["total_pf"], 2),
            "Record": f"{stats['wins']}-{stats['losses']}-{stats['ties']}"
        })
        
    df = pd.DataFrame(rows)
    if not df.empty:
        # Primary sort: F1 Points. Tiebreaker: Total Points For (PF)
        df = df.sort_values(by=["F1 Points", "Total PF"], ascending=[False, False]).reset_index(drop=True)
        df.index += 1
        
    return df

# --- APPLICATION UI ---
st.title("🏎️ Austin FF F1 Championship")
st.caption("Live Drivers' Championship Standings & Matchday Telemetry")

col_btn, col_blank = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Refresh Live Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

data = fetch_espn_data()

if data:
    df_standings = process_f1_standings(data)
    
    if df_standings is not None and not df_standings.empty:
        # Highlight Metrics
        p1_leader = df_standings.iloc[0]["Driver / Team"]
        p1_pts = df_standings.iloc[0]["F1 Points"]
        
        top_scorer_row = df_standings.sort_values(by="Total PF", ascending=False).iloc[0]
        top_scorer = top_scorer_row["Driver / Team"]
        top_pf = top_scorer_row["Total PF"]
        
        dnf_row = df_standings.iloc[-1]
        dnf_driver = dnf_row["Driver / Team"]

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-lbl">🏆 Championship Leader</div>
                <div class="metric-val">{p1_leader}</div>
                <div style="color:#A0AAB8; font-size:12px;">{p1_pts} PTS</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-lbl">⚡ Top Points Finisher</div>
                <div class="metric-val">{top_scorer}</div>
                <div style="color:#A0AAB8; font-size:12px;">{top_pf} PF</div>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-lbl">⚠️ Rear of Grid (P10)</div>
                <div class="metric-val">{dnf_driver}</div>
                <div style="color:#A0AAB8; font-size:12px;">{dnf_row['F1 Points']} PTS</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Visual Tabs
        tab1, tab2, tab3 = st.tabs(["🏎️ Driver Standings", "📊 Telemetry", "📋 Full Table"])

        with tab1:
            st.subheader("Drivers' Championship Standings")
            for rank, row in df_standings.iterrows():
                card_class = "driver-card"
                if rank == 1:
                    card_class += " driver-card-p1"
                elif rank == 2:
                    card_class += " driver-card-p2"
                elif rank == 3:
                    card_class += " driver-card-p3"

                st.markdown(f"""
                <div class="{card_class}">
                    <span class="f1-badge">{row['F1 Points']} PTS</span>
                    <h3 style="margin:0; font-size: 19px;">P{rank}. {row['Driver / Team']}</h3>
                    <div style="color: #A0AAB8; font-size: 13px; margin-top: 6px;">
                        Record: <b>{row['Record']}</b> &nbsp;|&nbsp; Total PF: <b>{row['Total PF']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with tab2:
            st.subheader("Season Telemetry & Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### F1 Championship Points")
                st.bar_chart(df_standings.set_index("Driver / Team")["F1 Points"])
            with col2:
                st.markdown("##### Total Fantasy Points Scored")
                st.bar_chart(df_standings.set_index("Driver / Team")["Total PF"])

        with tab3:
            st.subheader("Official Standings Table")
            st.dataframe(
                df_standings,
                use_container_width=True,
                column_config={
                    "F1 Points": st.column_config.NumberColumn("F1 Points 🏁", format="%d"),
                    "Total PF": st.column_config.NumberColumn("Total PF ⚡", format="%.2f"),
                }
            )
    else:
        st.warning("Connected to ESPN, but no matchup scoring data was returned.")
else:
    st.error("Unable to connect to ESPN API. Please check network status or league privacy settings.")
