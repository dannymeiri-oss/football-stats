import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# DIN API-NYCKEL FÖR ODDS
ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. ODDS-FUNKTIONER (OPTIMERADE FÖR 500 CREDITS) ---
@st.cache_data(ttl=600)
def fetch_all_odds():
    """Hämtar alla odds för Premier League i ett svep för att spara credits"""
    if not ODDS_API_KEY: return None
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    try:
        res = requests.get(url)
        return res.json() if res.status_code == 200 else None
    except: return None

def get_match_odds_from_cache(home_sheet, away_sheet, all_odds):
    """Matchar lag från Sheets med API-data utan extra kostnad"""
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

# --- 3. DATA-LADDNING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

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
        if col not in data.columns:
            data[col] = 0
        elif col not in ['response.fixture.referee', 'response.fixture.status.short', 'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name']:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

# --- HJÄLPFUNKTIONER ---
def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.1em;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- HUVUDLAYOUT ---
if df is not None:
    years = sorted(df['Säsong'].unique(), reverse=True)
    year_options = ["Alla säsonger"] + [str(y) for y in years]

    # --- VY 1: STATISTIK (SPELADE) ---
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h1 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>", unsafe_allow_html=True)
        
        col_wrap = st.columns([1, 6, 1])
        with col_wrap[1]:
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

    # --- VY 2: H2H MED ODDS (KOMMANDE) ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h1 style='text-align: center;'>H2H Analys: {h_team} vs {a_team}</h1>", unsafe_allow_html=True)
        
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        main_c1, main_c2, main_c3 = st.columns([1, 5, 1])
        
        with main_c2:
            if not h_stats.empty and not a_stats.empty:
                st.markdown("<h3 style='text-align: center;'>🎯 Total Förväntad Matchstatistik</h3>", unsafe_allow_html=True)
                tc1, tc2, tc3, tc4 = st.columns(4)
                exp_goals = h_stats['response.goals.home'].mean() + a_stats['response.goals.away'].mean()
                exp_xg = h_stats['xG Hemma'].mean() + a_stats['xG Borta'].mean()
                exp_corners = h_stats['Hörnor Hemma'].mean() + a_stats['Hörnor Borta'].mean()
                exp_cards = h_stats['Gula kort Hemma'].mean() + a_stats['Gula Kort Borta'].mean()
                tc1.metric("Förväntade Mål", round(exp_goals, 2))
                tc2.metric("Förväntad xG", round(exp_xg, 2))
                tc3.metric("Hörnor", round(exp_corners, 1))
                tc4.metric("Gula Kort", round(exp_cards, 1))
                
                # --- NY ODDS SEKTION ---
                st.divider()
                st.markdown("<h3 style='text-align: center;'>💸 Marknadsodds (Unibet)</h3>", unsafe_allow_html=True)
                all_market_odds = fetch_all_odds()
                h2h, totals = get_match_odds_from_cache(h_team, a_team, all_market_odds)
                
                if h2h or totals:
                    oc1, oc2 = st.columns(2)
                    with oc1:
                        st.write("**Matchodds (1X2)**")
                        if h2h:
                            for o in sorted(h2h, key=lambda x: x['name'] == 'Draw'):
                                st.write(f"{o['name']}: **{o['price']}**")
                    with oc2:
                        st.write("**Mål Ö/U 2.5**")
                        if totals:
                            for o in totals:
                                label = "Över" if o['name'].lower() == "over" else "Under"
                                st.write(f"{label} 2.5: **{o['price']}**")
                else:
                    st.info("Inga live-odds hittades för denna match just nu.")

                st.divider()
                st.markdown("<h3 style='text-align: center;'>📊 Lagjämförelse (Snitt Hemma vs Borta)</h3>", unsafe_allow_html=True)
                cols = [
                    ("Mål", 'response.goals.home', 'response.goals.away'),
                    ("xG", 'xG Hemma', 'xG Borta'),
                    ("Bollinnehav", 'Bollinnehav Hemma', 'Bollinnehav Borta'),
                    ("Skott på mål", 'Skott på mål Hemma', 'Skott på mål Borta'),
                    ("Hörnor", 'Hörnor Hemma', 'Hörnor Borta'),
                    ("Fouls", 'Fouls Hemma', 'Fouls Borta'),
                    ("Gula Kort", 'Gula kort Hemma', 'Gula Kort Borta'),
                ]
                for label, h_col, a_col in cols:
                    is_p = "Bollinnehav" in label
                    stat_comparison_row(label, round(h_stats[h_col].mean(), 2), round(a_stats[a_col].mean(), 2), is_p)
            
            st.divider()
            st.markdown("<h3 style='text-align: center;'>📜 Senaste möten</h3>", unsafe_allow_html=True)
            h2h_matches = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            if not h2h_matches.empty:
                h2h_display = h2h_matches[['datetime', 'response.teams.home.name', 'response.goals.home', 'response.goals.away', 'response.teams.away.name']].copy()
                h2h_display['datetime'] = h2h_display['datetime'].dt.strftime('%d %b %Y %H:%M')
                h2h_display.columns = ['Datum', 'Hemmalag', ' ', '  ', 'Bortalag']
                st.dataframe(h2h_display.sort_values('Datum', ascending=False), hide_index=True, use_container_width=True)

    # --- VY 3: HUVUDTABBAR ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        with tab1:
            st.header("Matchcenter")
            m_col, s_col = st.columns(2)
            mode = m_col.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            search = s_col.text_input("Sök lag:", "", key="search_main")
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            if search:
                d_df = d_df[(d_df['response.teams.home.name'].str.contains(search, case=False)) | (d_df['response.teams.away.name'].str.contains(search, case=False))]
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1.2])
                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Senaste resultaten" else "VS"
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]} <img src="{r["response.teams.home.logo"]}" width="18"></div><div style="background:#222; color:white; padding:2px 8px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div><div style="flex:1; text-align:left; font-weight:bold;"><img src="{r["response.teams.away.logo"]}" width="18"> {r["response.teams.away.name"]}</div></div>', unsafe_allow_html=True)
                with c_b:
                    if mode == "Senaste resultaten":
                        if st.button("Statistik", key=f"s{idx}"):
                            st.session_state.view_match = r
                            st.rerun()
                    else:
                        if st.button("H2H", key=f"h{idx}"):
                            st.session_state.view_h2h = r
                            st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            f_col1, f_col2 = st.columns(2)
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = f_col1.selectbox("Välj lag:", all_teams)
            sel_year_team = f_col2.selectbox("Välj säsong (Lag):", year_options)
            if sel_team:
                t_df = df if sel_year_team == "Alla säsonger" else df[df['Säsong'] == int(sel_year_team)]
                h_df = t_df[(t_df['response.teams.home.name'] == sel_team) & (t_df['response.fixture.status.short'] == 'FT')]
                a_df = t_df[(t_df['response.teams.away.name'] == sel_team) & (t_df['response.fixture.status.short'] == 'FT')]
                st.subheader(f"📊 Totalt snitt ({sel_year_team})")
                t_m = len(h_df) + len(a_df)
                if t_m > 0:
                    tc1, tc2, tc3, tc4, tc5 = st.columns(5)
                    tc1.metric("Matcher", t_m)
                    tc2.metric("Mål snitt", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/t_m, 2))
                    tc3.metric("xG snitt", round((h_df['xG Hemma'].sum() + a_df['xG Borta'].sum())/t_m, 2))
                    tc4.metric("Hörnor snitt", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/t_m, 2))
                    tc5.metric("Gula snitt", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/t_m, 2))
                st.divider()
                col_h, col_a = st.columns(2)
                with col_h:
                    st.subheader("🏠 HEMMA")
                    if not h_df.empty:
                        for label, col in [("Matcher Hemma", 'datetime'), ("Mål", 'response.goals.home'), ("xG", 'xG Hemma'), ("Bollinnehav", 'Bollinnehav Hemma'), ("Skott på mål", 'Skott på mål Hemma'), ("Totala Skott", 'Total Skott Hemma'), ("Skott Utanför", 'Skott Utanför Hemma'), ("Blockar", 'Blockerade Skott Hemma'), ("Skott i Box", 'Skott i Box Hemma'), ("Skott utanför Box", 'Skott utanför Box Hemma'), ("Hörnor", 'Hörnor Hemma'), ("Offside", 'Offside Hemma'), ("Fouls", 'Fouls Hemma'), ("Räddningar", 'Räddningar Hemma'), ("Gula Kort", 'Gula kort Hemma'), ("Röda Kort", 'Röda Kort Hemma'), ("Passningar", 'Passningar Hemma'), ("Passnings%", 'Passningssäkerhet Hemma')]:
                            val = len(h_df) if label == "Matcher Hemma" else h_df[col].mean()
                            st.metric(label, round(val, 1) if "Passnings%" not in label and label != "Matcher Hemma" else (f"{int(val)}%" if "Passnings%" in label else int(val)))
                with col_a:
                    st.subheader("✈️ BORTA")
                    if not a_df.empty:
                        for label, col in [("Matcher Borta", 'datetime'), ("Mål", 'response.goals.away'), ("xG", 'xG Borta'), ("Bollinnehav", 'Bollinnehav Borta'), ("Skott på mål", 'Skott på mål Borta'), ("Totala Skott", 'Total Skott Borta'), ("Skott Utanför", 'Skott Utanför Borta'), ("Blockar", 'Blockerade Skott Borta'), ("Skott i Box", 'Skott i Box Borta'), ("Skott utanför Box", 'Skott utanför Box Borta'), ("Hörnor", 'Hörnor Borta'), ("Offside", 'Offside Borta'), ("Fouls", 'Fouls Borta'), ("Räddningar", 'Räddningar Borta'), ("Gula Kort", 'Gula Kort Borta'), ("Röda Kort", 'Röda Kort Borta'), ("Passningar", 'Passningar Borta'), ("Passnings%", 'Passningssäkerhet Borta')]:
                            val = len(a_df) if label == "Matcher Borta" else a_df[col].mean()
                            st.metric(label, round(val, 1) if "Passnings%" not in label and label != "Matcher Borta" else (f"{int(val)}%" if "Passnings%" in label else int(val)))

        with tab3:
            st.header("⚖️ Domaranalys")
            d_col1, d_col2 = st.columns(2)
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = d_col1.selectbox("Välj domare:", refs)
            sel_year_ref = d_col2.selectbox("Välj säsong (Domare):", year_options)
            if sel_ref:
                ref_year_df = df if sel_year_ref == "Alla säsonger" else df[df['Säsong'] == int(sel_year_ref)]
                r_df = ref_year_df[ref_year_df['ref_clean'] == sel_ref]
                if not r_df.empty:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Matcher", len(r_df))
                    c2.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                    c3.metric("Fouls/Match", round((r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean(), 2))
                    c4.metric("Straffar", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None: st.dataframe(standings_df, hide_index=True, use_container_width=True)
else:
    st.error("Kunde inte ladda data.")
