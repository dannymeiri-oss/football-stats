import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# --- 1. KONFIGURATION (PERFEKT LAYOUT - RÖR EJ) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; text-align: center; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    
    /* MATCHCENTER CSS */
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    .pos-tag { font-size: 0.75rem; color: #888; font-weight: bold; margin: 0 4px; padding: 1px 4px; background: #f0f0f0; border-radius: 3px; }
    
    /* H2H & ANALYS DESIGN */
    .stat-label-centered { color: #888; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; text-align: center; margin-top: 15px; }
    .stat-comparison { display: flex; justify-content: center; align-items: center; gap: 20px; font-size: 1.6rem; font-weight: bold; color: black; }
    
    /* SEKTIONER LAGANALYS & DOMARE */
    .section-header { text-align: center; padding: 8px; background: #222; color: white; border-radius: 5px; margin: 20px 0 15px 0; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
    .total-header { text-align: center; padding: 5px; color: #444; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #eee; }
    
    /* NY CSS FÖR AI PREDICTIONS & ODDS */
    .bet-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 5px; font-size: 0.9rem; }
    .good-bet { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .bad-bet { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .odds-label { font-size: 0.8rem; color: #666; margin-bottom: 2px; text-transform: uppercase; }
    .odds-value { font-size: 1.1rem; font-weight: bold; color: #2e7d32; }
    .ai-text-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #2196F3; margin: 15px 0; font-style: italic; color: #333; font-size: 0.95rem; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)

# API CONFIG
API_KEY = "6343cd4636523af501b585a1b595ad26"
API_BASE_URL = "https://v3.football.api-sports.io"

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=712668345"

# --- 2. DATAHANTERING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

# --- API ODDS HÄMTNING (UPPDATERAD LOGIK FÖR ATT GARANTERA HÖRNOR) ---
@st.cache_data(ttl=600)
def get_odds_by_fixture_id(fixture_id):
    res = {"btts": "-", "corners": "-", "cards": "-", "debug": ""}
    if not fixture_id or str(fixture_id) in ["0", "0.0", "nan"]: return res

    headers = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-apisports-key': API_KEY}
    try:
        fid = str(int(float(fixture_id)))
        url = f"{API_BASE_URL}/odds?fixture={fid}"
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        
        if not data.get('response'): return res
            
        bookmakers = data['response'][0].get('bookmakers', [])
        # Hitta Bet365 (ID 1) eller ta den första tillgängliga
        bookie = next((b for b in bookmakers if b['id'] == 1), bookmakers[0] if bookmakers else None)
        
        if bookie:
            for bet in bookie.get('bets', []):
                # BLGM
                if bet['id'] == 8:
                    for v in bet['values']:
                        if v['value'] == "Yes": res["btts"] = v['odd']
                
                # HÖRNOR (Här var felet - vi gör den mer tolerant för linjer)
                if bet['id'] == 15:
                    corner_map = {v['value'].replace("Over ", ""): v['odd'] for v in bet['values'] if "Over" in v['value']}
                    for lina in ["11.5", "10.5", "9.5", "8.5"]:
                        if lina in corner_map:
                            res["corners"] = f"{corner_map[lina]} (Ö{lina})"
                            break
                
                # KORT
                if bet['id'] == 45:
                    card_map = {v['value'].replace("Over ", ""): v['odd'] for v in bet['values'] if "Over" in v['value']}
                    for lina in ["3.5", "4.5", "2.5", "5.5"]:
                        if lina in card_map:
                            res["cards"] = f"{card_map[lina]} (Ö{lina})"
                            break
    except: pass
    return res

def get_team_pos(team_name, league_name, standings):
    if standings is None or team_name is None: return ""
    try:
        league_col, pos_col, team_col = standings.columns[0], standings.columns[1], standings.columns[2]
        row = standings[(standings[league_col].astype(str) == str(league_name)) & (standings[team_col].astype(str) == str(team_name))]
        if not row.empty: return f"#{int(float(row[pos_col].values[0]))}"
    except: pass
    return ""

def get_rolling_card_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | (full_df['response.teams.away.name'] == team_name)) & (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    cards = [r['Gula kort Hemma'] if r['response.teams.home.name'] == team_name else r['Gula Kort Borta'] for _, r in team_matches.iterrows()]
    return sum(cards) / len(cards)

def get_rolling_corner_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | (full_df['response.teams.away.name'] == team_name)) & (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    corners = [r['Hörnor Hemma'] if r['response.teams.home.name'] == team_name else r['Hörnor Borta'] for _, r in team_matches.iterrows()]
    return sum(corners) / len(corners)

def get_rolling_goals_stats(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | (full_df['response.teams.away.name'] == team_name)) & (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0, 0.0
    scored = [r['response.goals.home'] if r['response.teams.home.name'] == team_name else r['response.goals.away'] for _, r in team_matches.iterrows()]
    conceded = [r['response.goals.away'] if r['response.teams.home.name'] == team_name else r['response.goals.home'] for _, r in team_matches.iterrows()]
    return sum(scored)/len(scored), sum(conceded)/len(conceded)

def format_referee(name):
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None"]: return "Domare: Okänd"
    name = str(name).split(',')[0].strip()
    parts = name.split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) >= 2 else name

def clean_stats(data):
    if data is None: return None
    data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce').dt.tz_localize(None) if 'response.fixture.date' in data.columns else pd.Timestamp.now().replace(tzinfo=None)
    data['Säsong'] = data['datetime'].dt.year.astype(str)
    cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 'response.goals.home', 'response.goals.away', 'response.fixture.id']
    for c in cols:
        if c not in data.columns: data[c] = 0.0
        else: data[c] = pd.to_numeric(data[c].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    data['Speltid'] = data['datetime'].dt.strftime('%d %b %Y')
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, x1, x2, is_pct=False, precision=2):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    v1, v2 = (f"{x1:.{precision}f}" if precision > 0 else f"{int(x1)}"), (f"{x2:.{precision}f}" if precision > 0 else f"{int(x2)}")
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{v1}{'%' if is_pct else ''}</div><div style='color:#ccc; margin:0 10px;'>|</div><div style='flex:1; text-align:left;'>{v2}{'%' if is_pct else ''}</div></div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode == "h2h_detail":
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        # UI Header
        st.markdown(f"<div style='background:#0e1117; padding:20px; border-radius:10px; text-align:center; color:white;'><h2>{h_team} vs {a_team}</h2></div>", unsafe_allow_html=True)

        # Hämta Odds
        odds_data = get_odds_by_fixture_id(m['response.fixture.id'])
        
        # Stats för Metric
        h_hist = df[(df['response.teams.home.name'] == h_team)].sort_values('datetime', ascending=False).head(20)
        a_hist = df[(df['response.teams.away.name'] == a_team)].sort_values('datetime', ascending=False).head(20)
        
        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Odds (Kort)", odds_data["cards"])
        o2.metric("BLGM Odds", odds_data["btts"])
        o3.metric("Hörnor Odds", odds_data["corners"])
        o4.metric("Domare", m['ref_clean'])

        st.markdown("<div class='section-header'>📊 Säsongsstatistik (L20)</div>", unsafe_allow_html=True)
        stat_comparison_row("MÅLSNITT", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
        stat_comparison_row("HÖRNOR SNITT", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
        stat_comparison_row("GULA KORT SNITT", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)

    elif st.session_state.view_mode == "main":
        tab1, tab2 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys"])
        with tab1:
            subset = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime')
            for idx, r in subset.iterrows():
                col_info, col_btn = st.columns([5, 1])
                with col_info: st.markdown(f"<div class='match-row'>{r['Speltid']} | {r['response.teams.home.name']} vs {r['response.teams.away.name']}</div>", unsafe_allow_html=True)
                with col_btn:
                    if st.button("Analys", key=f"main_{idx}"):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail"
                        st.rerun()
