import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# API-NYCKEL
ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. DATA-LADDNING & CACHE (Sparar Credits & Tid) ---
@st.cache_data(ttl=600)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

@st.cache_data(ttl=600) # Detta gör att vi bara använder 1 credit per 10 minuter
def fetch_all_odds():
    if not ODDS_API_KEY: return None
    # Hämtar hela Premier League (EPL) för att spara credits
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    try:
        res = requests.get(url)
        return res.json() if res.status_code == 200 else None
    except: return None

def get_match_odds_from_cache(home_sheet, away_sheet, all_odds):
    if not all_odds: return None, None
    def normalize(name): return "".join(filter(str.isalnum, name.lower()))
    h_s, a_s = normalize(home_sheet), normalize(away_sheet)
    for match in all_odds:
        h_api, a_api = normalize(match['home_team']), normalize(match['away_team'])
        if (h_s in h_api or h_api in h_s) and (a_s in a_api or a_api in a_s):
            h2h, totals = None, None
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                for mkt in match['bookmakers'][0]['markets']:
                    if mkt['key'] == 'h2h': h2h = mkt['outcomes']
                    if mkt['key'] == 'totals': totals = [o for o in mkt['outcomes'] if o['point'] == 2.5]
            return h2h, totals
    return None, None

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Röda Kort Hemma', 'Röda Kort Borta',
        'Skott på mål Hemma', 'Skott på mål Borta', 'Hörnor Hemma', 'Hörnor Borta',
        'Fouls Hemma', 'Fouls Borta', 'Total Skott Hemma', 'Total Skott Borta',
        'Skott Utanför Hemma', 'Skott Utanför Borta', 'Blockerade Skott Hemma', 'Blockerade Skott Borta',
        'Skott i Box Hemma', 'Skott i Box Borta', 'Skott utanför Box Hemma', 'Skott utanför Box Borta',
        'Passningar Hemma', 'Passningar Borta', 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta',
        'Offside Hemma', 'Offside Borta', 'Räddningar Hemma', 'Räddningar Borta',
        'Straffar Hemma', 'Straffar Borta',
        'response.goals.home', 'response.goals.away', 'response.fixture.status.short',
        'response.teams.home.logo', 'response.teams.away.logo', 'response.fixture.referee',
        'response.teams.home.name', 'response.teams.away.name'
    ]
    for col in cols_to_ensure:
        if col not in data.columns: data[col] = 0
        elif col not in ['response.fixture.referee', 'response.fixture.status.short', 'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name']:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

# --- 3. LADDA DATA ---
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
    years = sorted(df['Säsong'].unique(), reverse=True)
    year_options = ["Alla säsonger"] + [str(y) for y in years]

    # VY: STATISTIK (RESULTAT)
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h1 style='text-align:center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Anfall")
            stat_comparison_row("xG", r['xG Hemma'], r['xG Borta'])
            stat_comparison_row("Skott på mål", int(r['Skott på mål Hemma']), int(r['Skott på mål Borta']))
            stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        with col2:
            st.subheader("Matchfakta")
            stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
            stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    # VY: H2H & ODDS (KOMMANDE)
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h1 style='text-align:center;'>H2H: {h_team} vs {a_team}</h1>", unsafe_allow_html=True)
        
        # ODDS-HÄMTNING (OPTIMAL)
        all_market_odds = fetch_all_odds()
        h2h, totals = get_match_odds_from_cache(h_team, a_team, all_market_odds)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💸 Odds (1X2)")
            if h2h:
                for o in sorted(h2h, key=lambda x: x['name'] == 'Draw'): st.write(f"{o['name']}: **{o['price']}**")
            else: st.info("Inga odds i cachen.")
        with c2:
            st.subheader("⚽ Över/Under 2.5")
            if totals:
                for o in totals:
                    lbl = "Över" if o['name'].lower() == "over" else "Under"
                    st.write(f"{lbl} 2.5: **{o['price']}**")
            else: st.info("-")
        
        st.divider()
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        if not h_stats.empty and not a_stats.empty:
            st.markdown("<h3 style='text-align:center;'>📊 Historiska Snitt</h3>", unsafe_allow_html=True)
            cols = [("Mål", 'response.goals.home', 'response.goals.away'), ("xG", 'xG Hemma', 'xG Borta'), ("Hörnor", 'Hörnor Hemma', 'Hörnor Borta')]
            for label, hc, ac in cols: stat_comparison_row(label, round(h_stats[hc].mean(), 2), round(a_stats[ac].mean(), 2))

    # VY: HUVUDTABBAR
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            st.header("Matchcenter")
            m_col, s_col = st.columns(2)
            mode = m_col.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            search = s_col.text_input("Sök lag:", "")
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            if search:
                d_df = d_df[(d_df['response.teams.home.name'].str.contains(search, case=False)) | (d_df['response.teams.away.name'].str.contains(search, case=False))]
            
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1.2])
                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Senaste resultaten" else "VS"
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]} <img src="{r["response.teams.home.logo"]}" width="18"></div><div style="background:#222; color:white; padding:2px 8px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div><div style="flex:1; text-align:left; font-weight:bold;"><img src="{r["response.teams.away.logo"]}" width="18"> {r["response.teams.away.name"]}</div></div>', unsafe_allow_html=True)
                with c_b:
                    label = "H2H" if mode == "Nästa 50 matcher" else "Statistik"
                    if st.button(label, key=f"btn{idx}"):
                        if mode == "Nästa 50 matcher": st.session_state.view_h2h = r
                        else: st.session_state.view_match = r
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            f1, f2 = st.columns(2)
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = f1.selectbox("Välj lag:", all_teams)
            sel_year = f2.selectbox("Säsong:", year_options)
            t_df = df if sel_year == "Alla säsonger" else df[df['Säsong'] == int(sel_year)]
            h_df = t_df[(t_df['response.teams.home.name'] == sel_team) & (t_df['response.fixture.status.short'] == 'FT')]
            a_df = t_df[(t_df['response.teams.away.name'] == sel_team) & (t_df['response.fixture.status.short'] == 'FT')]
            if not h_df.empty or not a_df.empty:
                col_h, col_a = st.columns(2)
                with col_h:
                    st.subheader("🏠 HEMMA")
                    for lbl, col in [("Mål", 'response.goals.home'), ("xG", 'xG Hemma'), ("Hörnor", 'Hörnor Hemma')]:
                        st.metric(lbl, round(h_df[col].mean(), 2))
                with col_a:
                    st.subheader("✈️ BORTA")
                    for lbl, col in [("Mål", 'response.goals.away'), ("xG", 'xG Borta'), ("Hörnor", 'Hörnor Borta')]:
                        st.metric(lbl, round(a_df[col].mean(), 2))

        with tab3:
            st.header("⚖️ Domaranalys")
            d1, d2 = st.columns(2)
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = d1.selectbox("Domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                c1, c2, c3 = st.columns(3)
                c1.metric("Matcher", len(r_df))
                c2.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                c3.metric("Fouls/Match", round((r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean(), 2))

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True)
else:
    st.error("Kunde inte ladda data.")
