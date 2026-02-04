import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. SMARTA ODDS-FUNKTIONER ---
@st.cache_data(ttl=600)
def fetch_odds_for_league(sport_key):
    if not ODDS_API_KEY or not sport_key: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    try:
        res = requests.get(url)
        if res.status_code == 429: return "QUOTA_EXCEEDED"
        return res.json() if res.status_code == 200 else None
    except: return None

def get_match_odds_v2(home_sheet, away_sheet, all_odds):
    if not all_odds or all_odds == "QUOTA_EXCEEDED": return None, None
    
    def normalize(name):
        name = str(name).lower()
        if "manchester united" in name or "man utd" in name: return "manchesterunited"
        if "manchester city" in name or "man city" in name: return "manchestercity"
        if "tottenham" in name: return "tottenhamhotspur"
        return "".join(filter(str.isalnum, name))

    h_s, a_s = normalize(home_sheet), normalize(away_sheet)
    
    for match in all_odds:
        h_api, a_api = normalize(match['home_team']), normalize(match['away_team'])
        if h_s == h_api and a_s == a_api:
            h2h, totals = None, None
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                for mkt in match['bookmakers'][0]['markets']:
                    if mkt['key'] == 'h2h': h2h = mkt['outcomes']
                    if mkt['key'] == 'totals': totals = mkt['outcomes']
            return h2h, totals
    return None, None

# --- 3. DATA-LADDNING & TVÄTT ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta',
        'response.goals.home', 'response.goals.away', 'response.fixture.status.short',
        'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name',
        'response.fixture.referee'
    ]
    for col in cols_to_ensure:
        if col not in data.columns: data[col] = 0
        elif col not in ['response.fixture.status.short', 'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.referee']:
            val = data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True)
            data[col] = pd.to_numeric(val, errors='coerce').fillna(0)
    
    if 'sport_key' not in data.columns: data['sport_key'] = 'soccer_epl'
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.1em;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 4. HUVUDLAYOUT ---
if df is not None:
    # --- VY: MATCH-DETALJER ---
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h1 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>", unsafe_allow_html=True)
        stat_comparison_row("xG", round(r['xG Hemma'], 2), round(r['xG Borta'], 2))
        stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
        stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    # --- VY: H2H ANALYS ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h3 style='text-align: center;'>H2H Analys: {h_team} vs {a_team}</h3>", unsafe_allow_html=True)
        
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        if not h_stats.empty and not a_stats.empty:
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("Mål snitt", round(h_stats['response.goals.home'].mean() + a_stats['response.goals.away'].mean(), 2))
            tc2.metric("xG snitt", round(h_stats['xG Hemma'].mean() + a_stats['xG Borta'].mean(), 2))
            tc3.metric("Hörnor", round(h_stats['Hörnor Hemma'].mean() + a_stats['Hörnor Borta'].mean(), 1))
            tc4.metric("Gula", round(h_stats['Gula kort Hemma'].mean() + a_stats['Gula Kort Borta'].mean(), 1))
            
            st.divider()
            league_odds = fetch_odds_for_league(m['sport_key'])
            h2h_o, totals = get_match_odds_v2(h_team, a_team, league_odds)
            
            if h2h_o:
                st.write("**Aktuella Odds**")
                oc1, oc2 = st.columns(2)
                with oc1:
                    for o in h2h_o: st.write(f"{o['name']}: **{o['price']}**")
                with oc2:
                    if totals:
                        for o in totals:
                            if o.get('point') == 2.5: st.write(f"{o['name']} 2.5: **{o['price']}**")

    # --- VY: TABBAR (HUVUDMENY) ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            st.header("Matchcenter")
            mode = st.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1.2])
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]}</div><div style="margin:0 10px; padding:2px 8px; background:#eee; border-radius:4px;">VS</div><div style="flex:1; text-align:left; font-weight:bold;">{r["response.teams.away.name"]}</div></div>', unsafe_allow_html=True)
                with c_b:
                    if st.button("Analys", key=f"btn{idx}"):
                        if mode == "Nästa 50 matcher": st.session_state.view_h2h = r
                        else: st.session_state.view_match = r
                        st.rerun()

        with tab2:
            st.header("Lagstatistik")
            all_teams = sorted(df['response.teams.home.name'].unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            t_data = df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)]
            st.dataframe(t_data.head(10))

        with tab3:
            st.header("Domaranalys")
            if 'ref_clean' in df.columns:
                ref_stats = df.groupby('ref_clean').agg({'Gula kort Hemma': 'mean', 'Gula Kort Borta': 'mean', 'ref_clean': 'count'}).rename(columns={'ref_clean': 'Matcher'})
                st.dataframe(ref_stats.sort_values('Matcher', ascending=False))

        with tab4:
            st.header("Tabell")
            if standings_df is not None: st.dataframe(standings_df)
            else: st.info("Ladda upp tabell-gid i koden för att se tabellen.")

else:
    st.error("Data kunde inte laddas.")
