import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURATION (PERFEKT LAYOUT - RÖR EJ) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# FILNAMN FÖR DATABAS
DB_FILE = "bet_history.csv"

# Initiera session state
if 'ai_threshold' not in st.session_state: st.session_state.ai_threshold = 2.5
if 'btts_threshold' not in st.session_state: st.session_state.btts_threshold = 2.5
if 'scanned_matches' not in st.session_state: st.session_state.scanned_matches = [] # För att spara listan

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

# --- 2. DATAHANTERING & DATABAS ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

# --- DATABAS FUNKTIONER ---
def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        # Skapar tom struktur om filen inte finns
        return pd.DataFrame(columns=["Datum", "Match", "Typ", "Score", "Odds", "Insats", "Status", "FixtureID"])

def save_db(df):
    df.to_csv(DB_FILE, index=False)

def add_bet(row_data):
    df = load_db()
    new_row = pd.DataFrame([row_data])
    df = pd.concat([df, new_row], ignore_index=True)
    save_db(df)

@st.cache_data(ttl=600)
def get_odds_by_fixture_id(fixture_id):
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
        bookie = next((b for b in bookmakers if b['id'] == 11), None)
        if bookie:
            for bet in bookie.get('bets', []):
                if bet['id'] == 15: # Hörnor
                    vals = bet['values']
                    lines = sorted(list(set([v['value'].split(' ')[1] for v in vals if ' ' in v['value']])))
                    table = []
                    for L in lines:
                        o = next((v['odd'] for v in vals if v['value'] == f"Over {L}"), "-")
                        u = next((v['odd'] for v in vals if v['value'] == f"Under {L}"), "-")
                        table.append({"Lina": L, "Över": o, "Exakt": "-", "Under": u})
                    res["corners"] = pd.DataFrame(table)
                if bet['id'] == 45: # Kort
                    vals = bet['values']
                    lines = sorted(list(set([v['value'].split(' ')[1] for v in vals if ' ' in v['value']])))
                    table = []
                    for L in lines:
                        o = next((v['odd'] for v in vals if v['value'] == f"Over {L}"), "-")
                        u = next((v['odd'] for v in vals if v['value'] == f"Under {L}"), "-")
                        table.append({"Lina": L, "Över": o, "Exakt": "-", "Under": u})
                    res["cards"] = pd.DataFrame(table)
                if bet['id'] == 8: # BLGM
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

# --- STATISTIK FUNKTIONER ---
def get_rolling_card_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    cards = [r['Gula kort Hemma'] if r['response.teams.home.name'] == team_name else r['Gula Kort Borta'] for _, r in team_matches.iterrows()]
    return sum(cards) / len(cards)

def get_rolling_foul_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    fouls = [r['Fouls Hemma'] if r['response.teams.home.name'] == team_name else r['Fouls Borta'] for _, r in team_matches.iterrows()]
    return sum(fouls) / len(fouls)

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
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce').dt.tz_localize(None)
    else:
        data['datetime'] = pd.Timestamp.now().replace(tzinfo=None)
    if 'Säsong' not in data.columns:
        data['Säsong'] = data['datetime'].dt.year.astype(str)
    needed_cols = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'Fouls Hemma', 'Fouls Borta', 'Straffar Hemma', 'Straffar Borta',
        'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
        'Skott totalt Hemma', 'Skott totalt Borta', 'Röda kort Hemma', 'Röda kort Borta',
        'Räddningar Hemma', 'Räddningar Borta', 'Offside Hemma', 'Offside Borta',
        'response.goals.home', 'response.goals.away',
        'Skott utanför Hemma', 'Skott utanför Borta', 'Blockerade skott Hemma', 'Blockerade skott Borta',
        'Skott i straffområdet Hemma', 'Skott i straffområdet Borta', 'Skott utanför straffområdet Hemma', 'Skott utanför straffområdet Borta',
        'Passningar totalt Hemma', 'Passningar totalt Borta',
        'response.fixture.id'
    ]
    for col in needed_cols:
        if col not in data.columns: data[col] = 0.0
        else:
            if col == 'response.fixture.id':
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            else:
                data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    data['Speltid'] = data['datetime'].dt.strftime('%d %b %Y')
    return data

# --- SMART PREDICTION FUNCTIONS ---
def calculate_smart_prediction(h_team, a_team, ref_name, history_df):
    h_card = get_rolling_card_avg(h_team, history_df, n=20)
    a_card = get_rolling_card_avg(a_team, history_df, n=20)
    
    ref_val = 4.0
    if ref_name not in ["Domare: Okänd", "0", "Okänd", "nan", None]:
        r_hist = history_df[(history_df['ref_clean'] == ref_name)].sort_values('datetime', ascending=False).head(10)
        if not r_hist.empty:
            ref_val = (r_hist['Gula kort Hemma'].sum() + r_hist['Gula Kort Borta'].sum()) / len(r_hist)
    
    h_foul = get_rolling_foul_avg(h_team, history_df, n=20)
    a_foul = get_rolling_foul_avg(a_team, history_df, n=20)
    h_foul_factor = max(0, (h_foul - 10) * 0.1) 
    a_foul_factor = max(0, (a_foul - 10) * 0.1)

    h2h = history_df[((history_df['response.teams.home.name'] == h_team) & (history_df['response.teams.away.name'] == a_team)) | 
                     ((history_df['response.teams.home.name'] == a_team) & (history_df['response.teams.away.name'] == h_team))]
    derby_boost = 0.0
    if not h2h.empty:
        avg_h2h = (h2h['Gula kort Hemma'] + h2h['Gula Kort Borta']).mean()
        if avg_h2h > (h_card + a_card):
            derby_boost = 0.5 

    pred_h = (h_card * 0.6) + (ref_val * 0.15) + (h_foul_factor * 0.2) + (derby_boost * 0.5)
    pred_a = (a_card * 0.6) + (ref_val * 0.15) + (a_foul_factor * 0.2) + (derby_boost * 0.5)
    
    return pred_h, pred_a, ref_val

def calculate_btts_prediction(h_team, a_team, history_df):
    h_scored, h_conceded = get_rolling_goals_stats(h_team, history_df, n=20)
    a_scored, a_conceded = get_rolling_goals_stats(a_team, history_df, n=20)
    exp_h_goals = (h_scored + a_conceded) / 2
    exp_a_goals = (a_scored + h_conceded) / 2
    base_score = exp_h_goals + exp_a_goals
    consistency_bonus = 0.0
    if h_scored > 1.0 and h_conceded > 1.0: consistency_bonus += 0.2
    if a_scored > 1.0 and a_conceded > 1.0: consistency_bonus += 0.2
    return base_score + consistency_bonus

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
            
            ref_avg_val = 0.0
            display_ref = "N/A"
            if referee_name not in ["Domare: Okänd", "0", "Okänd", "nan", None]:
                ref_last_10 = df[(df['ref_clean'] == referee_name) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                if not ref_last_10.empty:
                    ref_avg_val = (ref_last_10['Gula kort Hemma'].sum() + ref_last_10['Gula Kort Borta'].sum()) / len(ref_last_10)
                    display_ref = f"{ref_avg_val:.2f}"
            
            st.markdown("<br><div class='section-header'>📊 MARKNADSODDS (UNIBET)</div>", unsafe_allow_html=True)
            odds_dfs = get_odds_by_fixture_id(m.get('response.fixture.id'))
            oc1, oc2, oc3 = st.columns(3)
            with oc1:
                st.markdown("<div class='odds-table-header'>🚩 Corners Over/Under</div>", unsafe_allow_html=True)
                if odds_dfs["corners"] is not None: st.dataframe(odds_dfs["corners"], hide_index=True, use_container_width=True)
                else: st.info("Inga odds")
            with oc2:
                st.markdown("<div class='odds-table-header'>🟨 Cards Over/Under</div>", unsafe_allow_html=True)
                if odds_dfs["cards"] is not None: st.dataframe(odds_dfs["cards"], hide_index=True, use_container_width=True)
                else: st.info("Inga odds")
            with oc3:
                st.markdown("<div class='odds-table-header'>⚽ Both Teams Score</div>", unsafe_allow_html=True)
                if odds_dfs["btts"] is not None: st.dataframe(odds_dfs["btts"], hide_index=True, use_container_width=True)
                else: st.info("Inga odds")

            st.markdown("<div class='section-header'>🤖 DEEP STATS AI PREDICTION (L20)</div>", unsafe_allow_html=True)
            h2h_past = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                          ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            h2h_past = h2h_past[h2h_past['response.fixture.status.short'] == 'FT']
            
            h_card_pred, a_card_pred, ref_val_used = calculate_smart_prediction(h_team, a_team, referee_name, df[df['datetime'] < m['datetime']])
            total_cards_pred = h_card_pred + a_card_pred
            
            h_corn_avg = get_rolling_corner_avg(h_team, df, n=20)
            a_corn_avg = get_rolling_corner_avg(a_team, df, n=20)
            
            btts_val = calculate_btts_prediction(h_team, a_team, df[df['datetime'] < m['datetime']])
            btts_text = "JA (Troligt)" if btts_val > 2.6 else "NEJ"
            btts_color = "green" if btts_val > 2.6 else "red"

            conclusion_paragraphs = [
                f"**🟨 Kort & Intensitet:** Smart AI-prognos på **{total_cards_pred:.1f} kort**. Domare: {referee_name} ({ref_val_used:.1f})",
                f"**⚽ BLGM-Score:** {btts_val:.2f} (Över 2.6 indikerar hög sannolikhet)."
            ]
            final_conclusion_html = "<br><br>".join(conclusion_paragraphs)

            c1, c2, c3 = st.columns(3)
            c1.metric("Hemmalag (xCards)", f"{h_card_pred:.2f}")
            c2.metric("TOTALT (xCards)", f"{total_cards_pred:.2f}")
            c3.metric("Bortalag (xCards)", f"{a_card_pred:.2f}")
            
            current_threshold = st.session_state.ai_threshold
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown("<div class='odds-label'>Kort Prognos</div>", unsafe_allow_html=True)
                if h_card_pred >= current_threshold: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {h_team} ÖVER {current_threshold} KORT</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {h_team} UNDER {current_threshold} KORT</div>", unsafe_allow_html=True)
            with col_b2:
                st.markdown("<div class='odds-label'>Kort Prognos</div>", unsafe_allow_html=True)
                if a_card_pred >= current_threshold: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {a_team} ÖVER {current_threshold} KORT</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {a_team} UNDER {current_threshold} KORT</div>", unsafe_allow_html=True)

            stat_comparison_row("AI HÖRNOR PREDIKTION", h_corn_avg, a_corn_avg)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if h_corn_avg >= 5.5: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {h_team} ÖVER 5.5 HÖRNOR</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {h_team} UNDER 5.5 HÖRNOR</div>", unsafe_allow_html=True)
            with col_c2:
                if a_corn_avg >= 5.5: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {a_team} ÖVER 5.5 HÖRNOR</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {a_team} UNDER 5.5 HÖRNOR</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='text-align:center; font-weight:bold; margin-top: 15px;'>BÅDA LAGEN GÖR MÅL (BLGM)? <span style='color:{btts_color}; font-size:1.2em;'>{btts_text}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ai-text-box'><b>🎙️ AI-Analys & Slutsats:</b><br><br>{final_conclusion_html}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='text-align:center; margin-top:20px; color:#333;'>SEASON AVERAGES COMPARISON</h3>", unsafe_allow_html=True)
            stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
            stat_comparison_row("EXPECTED GOALS (XG)", h_hist['xG Hemma'].mean(), h_hist['xG Borta'].mean())
            stat_comparison_row("BOLLINNEHAV", h_hist['Bollinnehav Hemma'].mean(), h_hist['Bollinnehav Borta'].mean(), is_pct=True, precision=0)
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)
            stat_comparison_row("RÖDA KORT / MATCH", h_hist['Röda kort Hemma'].mean(), h_hist['Röda kort Borta'].mean(), precision=2)
            
            st.markdown("<br>### ⚔️ Senaste inbördes möten", unsafe_allow_html=True)
            h2h = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                     ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            h2h = h2h[h2h['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            if not h2h.empty:
                h2h_display = h2h.rename(columns={'response.teams.home.name': 'Hemmalag', 'response.teams.away.name': 'Bortalag', 'response.goals.home': 'Mål H', 'response.goals.away': 'Mål B'})
                st.dataframe(h2h_display[['Speltid', 'Hemmalag', 'Mål H', 'Mål B', 'Bortalag']], use_container_width=True, hide_index=True)

        elif st.session_state.view_mode == "match_detail":
            st.markdown("<h2 style='text-align:center; color:#ddd; margin-bottom:20px;'>MATCH STATISTICS</h2>", unsafe_allow_html=True)
            stats_to_show = [("Ball Possession", 'Bollinnehav Hemma', 'Bollinnehav Borta', True), ("Shot on Target", 'Skott på mål Hemma', 'Skott på mål Borta', False), ("Expected Goals (xG)", 'xG Hemma', 'xG Borta', False), ("Pass Accuracy", 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', True), ("Corner Kicks", 'Hörnor Hemma', 'Hörnor Borta', False), ("Fouls", 'Fouls Hemma', 'Fouls Borta', False), ("Yellow Cards", 'Gula kort Hemma', 'Gula Kort Borta', False)]
            for label, h_col, a_col, is_pct in stats_to_show:
                h_val, a_val = m[h_col], m[a_col]
                suffix = "%" if is_pct else ""
                st.markdown(f'<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;"><div style="width: 80px; text-align: right; font-size: 1.4rem; font-weight: bold; color: black; padding-right: 15px;">{h_val}{suffix}</div><div style="width: 220px; background: #e63946; color: white; text-align: center; padding: 6px; font-weight: bold; font-size: 0.85rem; border-radius: 2px; text-transform: uppercase;">{label}</div><div style="width: 80px; text-align: left; font-size: 1.4rem; font-weight: bold; color: black; padding-left: 15px;">{a_val}{suffix}</div></div>', unsafe_allow_html=True)
    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell", "📊 Topplista", "🧪 Bet Simulator", "📝 Spelhistorik"])
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True, key="mc_mode")
            if mode == "Nästa matcher":
                now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now + timedelta(days=7)
                subset = df[(df['response.fixture.status.short'] == 'NS') & (df['datetime'] >= now) & (df['datetime'] <= end_date)]
            else:
                subset = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False).head(30)
            
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                l_name = r['response.league.name']
                h_pos = get_team_pos(h_name, l_name, standings_df)
                a_pos = get_team_pos(a_name, l_name, standings_df)
                
                if mode == "Nästa matcher":
                    h_val = get_rolling_card_avg(h_name, df, n=20)
                    a_val = get_rolling_card_avg(a_name, df, n=20)
                    h_disp = f"{h_val:.2f}"
                    a_disp = f"{a_val:.2f}"
                else:
                    h_val = r['Gula kort Hemma']
                    a_val = r['Gula Kort Borta']
                    h_disp = f"{int(h_val)}"
                    a_disp = f"{int(a_val)}"

                h_color = "#28a745" if h_val >= 2.00 else "black"
                a_color = "#28a745" if a_val >= 2.00 else "black"
                
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""
                        <div class="match-row" style="flex-direction: column; align-items: stretch; padding: 10px 15px;">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <div style="width:130px; font-size:0.8em; color:gray;">{r['Speltid']}</div>
                                <div style="flex:1; text-align:right; font-weight:bold;">
                                    <span class="pos-tag">{h_pos}</span> {h_name} 
                                    <img src="{r['response.teams.home.logo']}" width="20">
                                </div>
                                <div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div>
                                <div style="flex:1; text-align:left; font-weight:bold;">
                                    <img src="{r['response.teams.away.logo']}" width="20"> 
                                    {a_name} <span class="pos-tag">{a_pos}</span>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 5px; padding-top: 4px; border-top: 1px solid #fcfcfc;">
                                <div style="width:130px;"></div>
                                <div style="flex:1; text-align:right; padding-right: 25px;">
                                    <span style="font-size: 0.75rem; color: {h_color}; font-weight:bold;"><span style="color: #e6b800;">🟨</span> {h_disp}</span>
                                </div>
                                <div style="width:70px;"></div>
                                <div style="flex:1; text-align:left; padding-left: 25px;">
                                    <span style="font-size: 0.75rem; color: {a_color}; font-weight:bold;"><span style="color: #e6b800;">🟨</span> {a_disp}</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    if st.button("H2H" if mode == "Nästa matcher" else "Analys", key=f"btn_m_{idx}", use_container_width=True):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            all_seasons = sorted(df['Säsong'].unique(), reverse=True)
            f1, f2 = st.columns(2)
            with f1: sel_team = st.selectbox("Välj lag:", all_teams, key="laganalys_team")
            with f2: sel_season = st.selectbox("Välj säsong:", ["Alla"] + all_seasons, key="laganalys_season")
            if sel_team:
                team_df = df if sel_season == "Alla" else df[df['Säsong'] == sel_season]
                h_df = team_df[(team_df['response.teams.home.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                a_df = team_df[(team_df['response.teams.away.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                tot_m = len(h_df) + len(a_df)
                if tot_m > 0:
                    st.markdown("<div class='total-header'>TOTAL PRESTATION (SNITT)</div>", unsafe_allow_html=True)
                    t1, t2, t3, t4, t5, t6 = st.columns(6)
                    t1.metric("Matcher", tot_m); t2.metric("Mål", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/tot_m, 2)); t3.metric("xG", round((h_df['xG Hemma'].sum() + a_df['xG Borta'].sum())/tot_m, 2)); t4.metric("Hörnor", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/tot_m, 1)); t5.metric("Gula Kort", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/tot_m, 1)); t6.metric("Bollinnehav", f"{int((h_df['Bollinnehav Hemma'].sum() + a_df['Bollinnehav Borta'].sum())/tot_m)}%")
                    col_h, col_a = st.columns(2)
                    with col_h:
                        st.markdown("<div class='section-header'>🏠 Hemma</div>", unsafe_allow_html=True)
                        if not h_df.empty:
                            c1, c2 = st.columns(2)
                            c1.metric("Mål", round(h_df['response.goals.home'].mean(), 2)); c2.metric("xG", round(h_df['xG Hemma'].mean(), 2))
                            c1.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%"); c2.metric("Hörnor", round(h_df['Hörnor Hemma'].mean(), 1))
                            c1.metric("Gula Kort", round(h_df['Gula kort Hemma'].mean(), 1)); c2.metric("Röda Kort", round(h_df['Röda kort Hemma'].mean(), 2))
                    with col_a:
                        st.markdown("<div class='section-header'>✈️ Borta</div>", unsafe_allow_html=True)
                        if not a_df.empty:
                            c1, c2 = st.columns(2)
                            c1.metric("Mål", round(a_df['response.goals.away'].mean(), 2)); c2.metric("xG", round(a_df['xG Borta'].mean(), 2))
                            c1.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%"); c2.metric("Hörnor", round(a_df['Hörnor Borta'].mean(), 1))
                            c1.metric("Gula Kort", round(a_df['Gula Kort Borta'].mean(), 1)); c2.metric("Röda Kort", round(a_df['Röda kort Borta'].mean(), 2))
                    
                    with st.expander("📂 Djupanalys (Alla Datapunkter)", expanded=False):
                        st.dataframe(team_df.sort_values('datetime', ascending=False), use_container_width=True)

                    st.divider(); st.subheader(f"📅 Senaste 10 matcher för {sel_team}")
                    last_10 = team_df[((team_df['response.teams.home.name'] == sel_team) | (team_df['response.teams.away.name'] == sel_team)) & (team_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                    if not last_10.empty:
                        for idx, r in last_10.iterrows():
                            h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                            l_name = r['response.league.name']
                            h_pos = get_team_pos(h_name, l_name, standings_df)
                            a_pos = get_team_pos(a_name, l_name, standings_df)
                            h_avg = get_rolling_card_avg(h_name, df, n=20)
                            a_avg = get_rolling_card_avg(a_name, df, n=20)
                            h_color = "#28a745" if h_avg >= 2.00 else "black"
                            a_color = "#28a745" if a_avg >= 2.00 else "black"
                            col_info, col_btn = st.columns([4.5, 1.5])
                            with col_info:
                                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                                st.markdown(f"""
                                    <div class="match-row" style="flex-direction: column; align-items: stretch; padding: 10px 15px;">
                                        <div style="display: flex; align-items: center; justify-content: space-between;">
                                            <div style="width:100px; font-size:0.75rem; color:gray;">{r['Speltid']}</div>
                                            <div style="flex:1; text-align:right; font-weight:bold; font-size: 0.95rem;">
                                                <span class="pos-tag">{h_pos}</span> {h_name} 
                                                <img src="{r['response.teams.home.logo']}" width="18">
                                            </div>
                                            <div style="background:#222; color:white; padding:2px 8px; margin:0 12px; border-radius:4px; min-width:45px; text-align:center; font-weight: bold;">{score}</div>
                                            <div style="flex:1; text-align:left; font-weight:bold; font-size: 0.95rem;">
                                                <img src="{r['response.teams.away.logo']}" width="18"> 
                                                {a_name} <span class="pos-tag">{a_pos}</span>
                                            </div>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            with col_btn:
                                if st.button("Analys", key=f"btn_la_{idx}", use_container_width=True):
                                    st.session_state.selected_match = r
                                    st.session_state.view_mode = "match_detail"
                                    st.rerun()
        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["Domare: Okänd", "0", "Okänd", "nan"]])
            rf1, rf2 = st.columns(2)
            with rf1: sel_ref = st.selectbox("Välj domare:", ["Välj domare..."] + refs, key="domaranalys_ref")
            with rf2: sel_ref_season = st.selectbox("Välj säsong för domare:", ["Alla"] + all_seasons, key="domaranalys_season")
            if sel_ref != "Välj domare...":
                ref_df = df if sel_ref_season == "Alla" else df[df['Säsong'] == sel_ref_season]
                r_df = ref_df[ref_df['ref_clean'] == sel_ref]
                if not r_df.empty:
                    m_count = len(r_df); gula_tot = r_df['Gula kort Hemma'].sum() + r_df['Gula Kort Borta'].sum()
                    d1, d2 = st.columns(2)
                    d1.metric("Antal Matcher", m_count); d2.metric("Gula Kort (Snitt)", round(gula_tot / m_count, 2) if m_count > 0 else 0)
                    for idx_r, row_r in r_df.sort_values('datetime', ascending=False).iterrows():
                        st.markdown(f"<div class='match-row'>{row_r['Speltid']} | {row_r['response.teams.home.name']} {int(row_r['Gula kort Hemma'])}-{int(row_r['Gula Kort Borta'])} {row_r['response.teams.away.name']}</div>", unsafe_allow_html=True)
        with tab4:
            st.header("🏆 Ligatabell")
            if standings_df is not None:
                liga_col = standings_df.columns[0]
                available_leagues = sorted(standings_df[liga_col].dropna().unique().tolist())
                sel_league_stand = st.selectbox("Välj liga:", available_leagues, key="stand_sel")
                display_table = standings_df[standings_df[liga_col] == sel_league_stand].copy()
                st.dataframe(display_table.iloc[:, 1:], use_container_width=True, hide_index=True)
        with tab5:
            st.header("📊 Topplista")
            top_cat = st.radio("Välj kategori:", ["Lag", "Domare", "Heta Kortmatcher (Kommande)"], horizontal=True)
            c1, c2 = st.columns(2)
            with c1: num_matches = st.slider("Antal senaste matcher (Kriterium):", 1, 40, 20)
            with c2: 
                all_leagues = ["Alla"] + sorted(df['response.league.name'].unique().tolist()) if 'response.league.name' in df.columns else ["Alla"]
                sel_league = st.selectbox("Välj liga:", all_leagues, key="top_league_filter")
            filtered_df = df[df['response.fixture.status.short'] == 'FT']
            if sel_league != "Alla":
                filtered_df = filtered_df[filtered_df['response.league.name'] == sel_league]
            if top_cat == "Lag":
                team_stats = []
                teams = sorted(pd.concat([filtered_df['response.teams.home.name'], filtered_df['response.teams.away.name']]).unique())
                for t in teams:
                    t_avg = get_rolling_card_avg(t, df, n=num_matches)
                    team_stats.append({'Lag': t, 'Snitt Kort': round(t_avg, 2), 'Matcher': num_matches})
                if team_stats: st.dataframe(pd.DataFrame(team_stats).sort_values('Snitt Kort', ascending=False), use_container_width=True, hide_index=True)
            elif top_cat == "Domare":
                ref_stats = []
                for r in filtered_df['ref_clean'].unique():
                    if r in ["Domare: Okänd", "0", "Okänd", "nan"]: continue
                    r_matches = filtered_df[filtered_df['ref_clean'] == r].sort_values('datetime', ascending=False)
                    if len(r_matches) >= num_matches:
                        recent = r_matches.head(num_matches)
                        avg = (recent['Gula kort Hemma'].sum() + recent['Gula Kort Borta'].sum()) / len(recent)
                        ref_stats.append({'Domare': r, 'Snitt Kort': round(avg, 2), 'Matcher': len(recent)})
                if ref_stats: st.dataframe(pd.DataFrame(ref_stats).sort_values('Snitt Kort', ascending=False), use_container_width=True, hide_index=True)
            else:
                upcoming = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime', ascending=True)
                now_check = datetime.now().replace(tzinfo=None)
                end_check = now_check + timedelta(days=7)
                upcoming = upcoming[(upcoming['datetime'] >= now_check) & (upcoming['datetime'] <= end_check)]
                if sel_league != "Alla": upcoming = upcoming[upcoming['response.league.name'] == sel_league]
                analysis_results = []
                for _, row in upcoming.iterrows():
                    h_team, a_team = row['response.teams.home.name'], row['response.teams.away.name']
                    h_avg = get_rolling_card_avg(h_team, df, n=num_matches)
                    a_avg = get_rolling_card_avg(a_team, df, n=num_matches)
                    ref_avg_val = "N/A"
                    if row['ref_clean'] not in ["Domare: Okänd", "0", "Okänd", "nan"]:
                        r_matches = filtered_df[filtered_df['ref_clean'] == row['ref_clean']].sort_values('datetime', ascending=False).head(num_matches)
                        if not r_matches.empty:
                            ref_avg_val = round((r_matches['Gula kort Hemma'].sum() + r_matches['Gula Kort Borta'].sum()) / len(r_matches), 2)
                    analysis_results.append({'Match': f"{h_team} vs {a_team}", 'Kombinerat (Lagen)': round(h_avg + a_avg, 2), 'Domare (Snitt)': ref_avg_val, 'Liga': row['response.league.name']})
                if analysis_results: st.dataframe(pd.DataFrame(analysis_results).sort_values('Kombinerat (Lagen)', ascending=False), use_container_width=True, hide_index=True)
        
        with tab6:
            st.header("🧪 Bet Simulator & Optimizer (90 Dagar)")
            
            sim_mode = st.radio("Välj Strategi:", ["🟨 Kort", "⚽ BLGM"], horizontal=True)
            
            # --- OPTIMERAREN ---
            st.markdown("### 🎯 Hitta din optimala strategi")
            target_win_rate = st.slider("Vilken vinstprocent siktar du på?", 50, 100, 75, step=5)
            
            if st.button("Kör Optimering (High Performance)"):
                now = datetime.now()
                mask = (df['datetime'] < now) & (df['datetime'] >= now - timedelta(days=90)) & (df['response.fixture.status.short'] == 'FT')
                candidates = df[mask].sort_values('datetime', ascending=False)
                
                if candidates.empty:
                    st.warning("Ingen historisk data tillgänglig för perioden.")
                else:
                    simulated_predictions = []
                    
                    with st.spinner("Analyserar historisk data & simulerar matcher..."):
                        for _, match in candidates.iterrows():
                            match_date = match['datetime']
                            history_df = df[df['datetime'] < match_date]
                            if history_df.empty: continue

                            h_team = match['response.teams.home.name']
                            a_team = match['response.teams.away.name']
                            
                            if sim_mode == "🟨 Kort":
                                ref_name = match['ref_clean']
                                pred_h, pred_a, _ = calculate_smart_prediction(h_team, a_team, ref_name, history_df)
                                actual_h = match['Gula kort Hemma']
                                actual_a = match['Gula Kort Borta']
                                simulated_predictions.append({
                                    "val": (pred_h, pred_a),
                                    "win": (actual_h >= 2 and actual_a >= 2)
                                })
                            else: # BLGM
                                pred_btts = calculate_btts_prediction(h_team, a_team, history_df)
                                actual_btts = (match['response.goals.home'] > 0 and match['response.goals.away'] > 0)
                                simulated_predictions.append({
                                    "val": pred_btts,
                                    "win": actual_btts
                                })
                    
                    results_data = []
                    my_bar = st.progress(0, text="Optimerar...")
                    
                    test_ranges = [round(x * 0.1, 1) for x in range(20, 36)] if sim_mode == "🟨 Kort" else [round(x * 0.1, 1) for x in range(15, 45)]
                    
                    for i, threshold in enumerate(test_ranges):
                        wins = 0
                        bets = 0
                        for sim in simulated_predictions:
                            is_bet = False
                            if sim_mode == "🟨 Kort":
                                if sim["val"][0] >= threshold and sim["val"][1] >= threshold: is_bet = True
                            else: # BLGM
                                if sim["val"] >= threshold: is_bet = True
                            
                            if is_bet:
                                bets += 1
                                if sim["win"]: wins += 1
                        
                        current_hit_rate = (wins / bets * 100) if bets > 0 else 0
                        results_data.append({"Threshold": threshold, "Hit Rate %": round(current_hit_rate, 1), "Bets": bets})
                        my_bar.progress((i + 1) / len(test_ranges))
                    
                    my_bar.empty()
                    
                    res_df = pd.DataFrame(results_data)
                    qualified = res_df[res_df["Hit Rate %"] >= target_win_rate]
                    
                    st.divider()
                    
                    if not qualified.empty:
                        winner = qualified.iloc[0]
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Rekommenderad Gräns", f"{winner['Threshold']}")
                        c2.metric("Förväntad Hit Rate", f"{winner['Hit Rate %']}%")
                        c3.metric("Antal Bets (90d)", f"{int(winner['Bets'])}")
                        
                        st.success(f"✅ För att nå **{target_win_rate}% vinst** ({sim_mode}) bör du sätta gränsen på **{winner['Threshold']}**.")
                        
                        if st.button(f"Sätt {sim_mode}-Threshold till {winner['Threshold']}"):
                            if sim_mode == "🟨 Kort": st.session_state.ai_threshold = winner['Threshold']
                            else: st.session_state.btts_threshold = winner['Threshold']
                            st.rerun()
                    else:
                        best_possible = res_df.loc[res_df['Hit Rate %'].idxmax()]
                        st.error(f"❌ Kunde inte nå {target_win_rate}% med nuvarande data.")
                        st.info(f"Högsta möjliga just nu är **{best_possible['Hit Rate %']}%** vid gränsen **{best_possible['Threshold']}**.")

                    st.markdown("### 📊 Analys av alla nivåer")
                    st.line_chart(res_df.set_index("Threshold")["Hit Rate %"])
                    st.dataframe(res_df.style.highlight_max(axis=0, subset=["Hit Rate %"]), use_container_width=True)
            
            st.divider()
            curr_thresh = st.session_state.ai_threshold if sim_mode == "🟨 Kort" else st.session_state.btts_threshold
            st.markdown(f"### 🔮 Kommande Matcher ({sim_mode} | Gräns: {curr_thresh})")
            
            if 'scanned_matches' not in st.session_state:
                st.session_state.scanned_matches = []

            if st.button("Scanna Kommande Matcher"):
                now = datetime.now()
                upcoming = df[(df['response.fixture.status.short'] == 'NS') & (df['datetime'] > now)].sort_values('datetime')
                
                found_bets = []
                with st.spinner("Scannar marknaden..."):
                    for idx, row in upcoming.iterrows():
                        hist_df = df[df['datetime'] < row['datetime']]
                        
                        h_team = row['response.teams.home.name']
                        a_team = row['response.teams.away.name']
                        is_match = False
                        display_val = ""
                        
                        if sim_mode == "🟨 Kort":
                            ph, pa, _ = calculate_smart_prediction(h_team, a_team, row['ref_clean'], hist_df)
                            if ph >= curr_thresh and pa >= curr_thresh:
                                is_match = True
                                display_val = f"H:{ph:.2f} B:{pa:.2f}"
                        else: # BLGM
                            pb = calculate_btts_prediction(h_team, a_team, hist_df)
                            if pb >= curr_thresh:
                                is_match = True
                                display_val = f"{pb:.2f}"
                        
                        if is_match:
                            found_bets.append({
                                "id": row['response.fixture.id'],
                                "match": f"{h_team} - {a_team}",
                                "datum": row['Speltid'],
                                "score": display_val,
                                "type": sim_mode
                            })
                
                st.session_state.scanned_matches = found_bets
            
            if st.session_state.scanned_matches:
                st.success(f"Visar {len(st.session_state.scanned_matches)} matcher.")
                for item in st.session_state.scanned_matches:
                    with st.form(key=f"form_{item['id']}"):
                        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                        with c1: 
                            st.write(f"**{item['match']}**")
                            st.caption(item['datum'])
                        with c2: 
                            st.write(f"**Score:** {item['score']}")
                        with c3: 
                            odds_val = st.text_input("Odds", key=f"odds_{item['id']}")
                        with c4:
                            stake_val = st.text_input("Insats", key=f"stake_{item['id']}")
                        with c5:
                            submitted = st.form_submit_button("SPELA")
                            if submitted:
                                final_odds = odds_val.replace(',', '.') if odds_val else "-"
                                bet_entry = {
                                    "Datum": item['datum'],
                                    "Match": item['match'],
                                    "Typ": item['type'],
                                    "Score": item['score'],
                                    "Odds": final_odds,
                                    "Insats": stake_val if stake_val else "0",
                                    "Status": "Öppen",
                                    "FixtureID": item['id']
                                }
                                add_bet(bet_entry)
                                st.success("Sparad!")
            else:
                st.info("Listan är tom. Tryck på 'Scanna' för att hitta matcher.")

        with tab7:
            st.header("📝 Spelhistorik")
            history_df = load_db()
            
            if history_df.empty:
                st.info("Inga spel registrerade ännu.")
            else:
                updated = False
                for index, row in history_df.iterrows():
                    if row['Status'] == "Öppen":
                        match_res = df[df['response.fixture.id'] == int(row['FixtureID'])]
                        if not match_res.empty and match_res.iloc[0]['response.fixture.status.short'] == 'FT':
                            res_row = match_res.iloc[0]
                            win = False
                            if row['Typ'] == "🟨 Kort":
                                win = (res_row['Gula kort Hemma'] >= 2 and res_row['Gula Kort Borta'] >= 2)
                            else: # BLGM
                                win = (res_row['response.goals.home'] > 0 and res_row['response.goals.away'] > 0)
                            
                            history_df.at[index, 'Status'] = "✅ VINST" if win else "❌ FÖRLUST"
                            updated = True
                
                if updated:
                    save_db(history_df)
                    st.rerun()

                st.markdown("Du kan redigera värden eller radera rader (markera och tryck Delete).")
                edited_df = st.data_editor(history_df, num_rows="dynamic", use_container_width=True, key="history_editor")
                
                if not edited_df.equals(history_df):
                    save_db(edited_df)
                    st.rerun()

else:
    st.error("Kunde inte ladda data.")
