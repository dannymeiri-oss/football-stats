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
    
    /* DOMARE INFO I H2H */
    .referee-box { text-align: center; background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 20px; font-weight: bold; }

    /* NY CSS FÖR AI PREDICTIONS & ODDS */
    .bet-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 5px; font-size: 0.9rem; }
    .good-bet { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .bad-bet { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .odds-label { font-size: 0.8rem; color: #666; margin-bottom: 2px; text-transform: uppercase; }
    .odds-value { font-size: 1.1rem; font-weight: bold; color: #2e7d32; }
    .ai-text-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #2196F3; margin: 15px 0; font-style: italic; color: #333; font-size: 0.95rem; line-height: 1.6; }
    
    /* ODDS TABELL STYLING */
    .odds-table-header { font-weight: bold; text-align: center; background-color: #f0f0f0; padding: 5px; border-radius: 4px; margin-bottom: 5px; font-size: 0.85rem; color: #333; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=712668345"
API_KEY = "6343cd4636523af501b585a1b595ad26"
API_BASE_URL = "https://v3.football.api-sports.io"

# --- 2. DATAHANTERING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

@st.cache_data(ttl=600)
def get_odds_by_fixture_id(fixture_id):
    """Hämtar odds och returnerar DataFrame-objekt för tabeller baserat på Unibet."""
    res = {"corners": None, "cards": None, "btts": None}
    if not fixture_id or str(fixture_id) in ["0", "0.0", "nan"]: return res
    headers = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-apisports-key': API_KEY}
    try:
        fid = str(int(float(fixture_id)))
        url = f"{API_BASE_URL}/odds?fixture={fid}"
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        if not data.get('response') or len(data['response']) == 0: return res
        bookmakers = data['response'][0].get('bookmakers', [])
        bookie = next((b for b in bookmakers if b['id'] == 11), None) # Endast Unibet
        if bookie:
            for bet in bookie.get('bets', []):
                if bet['id'] == 15: # Corners Over/Under
                    vals = bet['values']
                    lines = sorted(list(set([v['value'].split(' ')[1] for v in vals])))
                    table = []
                    for L in lines:
                        o = next((v['odd'] for v in vals if v['value'] == f"Over {L}"), "-")
                        u = next((v['odd'] for v in vals if v['value'] == f"Under {L}"), "-")
                        table.append({"Lina": L, "Över": o, "Exakt": "-", "Under": u})
                    res["corners"] = pd.DataFrame(table)
                if bet['id'] == 45: # Cards Over/Under
                    vals = bet['values']
                    lines = sorted(list(set([v['value'].split(' ')[1] for v in vals])))
                    table = []
                    for L in lines:
                        o = next((v['odd'] for v in vals if v['value'] == f"Over {L}"), "-")
                        u = next((v['odd'] for v in vals if v['value'] == f"Under {L}"), "-")
                        table.append({"Lina": L, "Över": o, "Exakt": "-", "Under": u})
                    res["cards"] = pd.DataFrame(table)
                if bet['id'] == 8: # Both Teams Score
                    btts = [{"Val": "JA", "Odds": v['odd']} if v['value'] == "Yes" else {"Val": "NEJ", "Odds": v['odd']} for v in bet['values']]
                    res["btts"] = pd.DataFrame(btts)
    except: pass
    return res

def get_team_pos(team_name, league_name, standings):
    if standings is None or team_name is None: return ""
    try:
        league_col = standings.columns[0]
        pos_col = standings.columns[1]
        team_col = standings.columns[2]
        row = standings[(standings[league_col].astype(str) == str(league_name)) & 
                        (standings[team_col].astype(str) == str(team_name))]
        if not row.empty:
            val = row[pos_col].values[0]
            return f"#{int(float(val))}"
    except: pass
    return ""

def get_rolling_card_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    cards = [r['Gula kort Hemma'] if r['response.teams.home.name'] == team_name else r['Gula Kort Borta'] for _, r in team_matches.iterrows()]
    return sum(cards) / len(cards)

def get_rolling_corner_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    corners = [r['Hörnor Hemma'] if r['response.teams.home.name'] == team_name else r['Hörnor Borta'] for _, r in team_matches.iterrows()]
    return sum(corners) / len(corners)

def get_rolling_goals_stats(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0, 0.0
    scored = [r['response.goals.home'] if r['response.teams.home.name'] == team_name else r['response.goals.away'] for _, r in team_matches.iterrows()]
    conceded = [r['response.goals.away'] if r['response.teams.home.name'] == team_name else r['response.goals.home'] for _, r in team_matches.iterrows()]
    return sum(scored)/len(scored), sum(conceded)/len(conceded)

def format_referee(name):
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None"]:
        return "Domare: Okänd"
    name = str(name).split(',')[0].strip()
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name

def clean_stats(data):
    if data is None: return None
    data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce').dt.tz_localize(None) if 'response.fixture.date' in data.columns else pd.Timestamp.now().replace(tzinfo=None)
    if 'Säsong' not in data.columns: data['Säsong'] = data['datetime'].dt.year.astype(str)
    cols = ['Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 'response.goals.home', 'response.goals.away', 'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 'response.fixture.id']
    for col in cols:
        if col in data.columns:
            if col == 'response.fixture.id': data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            else: data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    data['Speltid'] = data['datetime'].dt.strftime('%d %b %Y')
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, x1, x2, is_pct=False, precision=2):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    suffix = "%" if is_pct else ""
    v1 = "N/A" if pd.isna(x1) else (f"{x1:.{precision}f}" if precision > 0 else f"{int(x1)}")
    v2 = "N/A" if pd.isna(x2) else (f"{x2:.{precision}f}" if precision > 0 else f"{int(x2)}")
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{v1}{suffix}</div><div style='color:#ccc; margin:0 10px;'>|</div><div style='flex:1; text-align:left;'>{v2}{suffix}</div></div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        l_name = m['response.league.name']
        referee_name = m['ref_clean']
        h_pos = get_team_pos(h_team, l_name, standings_df)
        a_pos = get_team_pos(a_team, l_name, standings_df)

        st.markdown(f"""
            <div style="background-color: #0e1117; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid #333;">
                <div style="color: #ffcc00; font-weight: bold; letter-spacing: 2px; font-size: 1.2rem;">{"FULL TIME" if m['response.fixture.status.short'] == 'FT' else "UPCOMING"}</div>
                <div style="display: flex; justify-content: center; align-items: center; gap: 30px; margin-top: 15px;">
                    <div style="flex: 1; text-align: right;">
                        <img src="{m['response.teams.home.logo']}" width="60"><br>
                        <span style="font-size: 1.1rem; font-weight: bold; color: white;">{h_team} <span style="color:#ffcc00;">{h_pos}</span></span>
                    </div>
                    <div style="display: flex; gap: 5px; align-items: center;">
                        <div style="background: #e63946; color: white; font-size: 2.5rem; padding: 5px 20px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.home']) if m['response.fixture.status.short'] == 'FT' else 0}</div>
                        <div style="background: #e63946; color: white; font-size: 1.2rem; padding: 15px 10px; border-radius: 5px; font-weight: bold;">{"90:00" if m['response.fixture.status.short'] == 'FT' else "VS"}</div>
                        <div style="background: #e63946; color: white; font-size: 2.5rem; padding: 5px 20px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.away']) if m['response.fixture.status.short'] == 'FT' else 0}</div>
                    </div>
                    <div style="flex: 1; text-align: left;">
                        <img src="{m['response.teams.away.logo']}" width="60"><br>
                        <span style="font-size: 1.1rem; font-weight: bold; color: white;"><span style="color:#ffcc00;">{a_pos}</span> {a_team}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.view_mode == "h2h_detail":
            h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(20)
            a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(20)
            h_card_avg = get_rolling_card_avg(h_team, df, n=20)
            a_card_avg = get_rolling_card_avg(a_team, df, n=20)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mål snitt (L20)", round(h_hist['response.goals.home'].mean() + a_hist['response.goals.away'].mean(), 2) if not h_hist.empty else "N/A")
            m2.metric("xG snitt (L20)", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2) if not h_hist.empty else "N/A")
            m3.metric("Hörnor snitt (L20)", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1) if not h_hist.empty else "N/A")
            m4.metric("Gula snitt (L20)", round(h_card_avg + a_card_avg, 1) if not h_hist.empty else "N/A")

            # --- ODDS TABELLER (NY SEKTION) ---
            st.markdown("<br><div class='section-header'>📊 MARKNADSODDS (UNIBET)</div>", unsafe_allow_html=True)
            odds_dfs = get_odds_by_fixture_id(m.get('response.fixture.id'))
            oc1, oc2, oc3 = st.columns(3)
            with oc1:
                st.markdown("<div class='odds-table-header'>🚩 Hörnor Over/Under</div>", unsafe_allow_html=True)
                if odds_dfs["corners"] is not None: st.dataframe(odds_dfs["corners"], hide_index=True, use_container_width=True)
                else: st.info("Inga odds")
            with oc2:
                st.markdown("<div class='odds-table-header'>🟨 Kort Over/Under</div>", unsafe_allow_html=True)
                if odds_dfs["cards"] is not None: st.dataframe(odds_dfs["cards"], hide_index=True, use_container_width=True)
                else: st.info("Inga odds")
            with oc3:
                st.markdown("<div class='odds-table-header'>⚽ Both Teams Score</div>", unsafe_allow_html=True)
                if odds_dfs["btts"] is not None: st.dataframe(odds_dfs["btts"], hide_index=True, use_container_width=True)
                else: st.info("Inga odds")

            st.markdown("<div class='section-header'>🤖 DEEP STATS AI PREDICTION (L20)</div>", unsafe_allow_html=True)
            h_corn_avg = get_rolling_corner_avg(h_team, df, n=20)
            a_corn_avg = get_rolling_corner_avg(a_team, df, n=20)
            h_scored, h_conceded = get_rolling_goals_stats(h_team, df, n=20)
            a_scored, a_conceded = get_rolling_goals_stats(a_team, df, n=20)
            btts_score = (h_scored + a_conceded + a_scored + h_conceded) / 2
            
            stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
            stat_comparison_row("EXPECTED GOALS (XG)", h_hist['xG Hemma'].mean(), h_hist['xG Borta'].mean())
            stat_comparison_row("BOLLINNEHAV", h_hist['Bollinnehav Hemma'].mean(), h_hist['Bollinnehav Borta'].mean(), is_pct=True, precision=0)
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)

    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell", "📊 Topplista"])
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True, key="mc_mode")
            subset = df[(df['response.fixture.status.short'] == 'NS')] if mode == "Nästa matcher" else df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False).head(30)
            for idx, r in subset.iterrows():
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info: st.markdown(f"<div class='match-row'>{r['Speltid']} | {r['response.teams.home.name']} vs {r['response.teams.away.name']}</div>", unsafe_allow_html=True)
                with col_btn:
                    if st.button("Analys", key=f"btn_m_{idx}"):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail"
                        st.rerun()
else:
    st.error("Kunde inte ladda data.")
