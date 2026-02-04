import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & NYCKLAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# Din API-nyckel är nu integrerad
API_KEY = "6343cd4636523af501b585a1b595ad26" 
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# --- 2. LIVE ODDS-MOTOR (DIREKT FRÅN API-FOOTBALL PRO) ---
def fetch_pro_odds(fixture_id):
    """Hämtar Unibet-odds (ID 11) direkt från din PRO-kvota"""
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}&bookmaker=11"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        if not data['response'] or len(data['response']) == 0: 
            return None
        
        # Vi tar första tillgängliga oddset (Unibet)
        bookmaker_data = data['response'][0]['bookmakers'][0]
        markets = bookmaker_data['markets']
        
        results = {}
        for m in markets:
            if m['name'] == "Match Winner": results['1X2'] = m['values']
            if m['name'] == "Corners Over/Under": results['Corners'] = m['values']
            if m['name'] == "Cards Over/Under": results['Cards'] = m['values']
            if m['name'] == "Both Teams Score": results['BTTS'] = m['values']
        return results
    except:
        return None

# --- 3. DATAHANTERING (FRÅN SHEETS) ---
@st.cache_data(ttl=60)
def load_and_clean_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        if 'response.fixture.date' in data.columns:
            data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        
        # Städa numeriska värden från din Raw Data
        cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
                'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
                'response.goals.home', 'response.goals.away']
        for col in cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        return data
    except:
        return None

df = load_and_clean_data(RAW_DATA_URL)

if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.2em; font-weight:bold;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#666; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.2em; font-weight:bold;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 4. VISUALISERING ---
if df is not None:
    # --- RESULTAT-VY (HISTORIK) ---
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h1 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>", unsafe_allow_html=True)
        st.divider()
        stat_comparison_row("xG", round(r['xG Hemma'], 2), round(r['xG Borta'], 2))
        stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
        stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    # --- H2H-VY (ANALYS INFÖR MATCH MED PRO ODDS) ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        st.markdown(f"<h2 style='text-align: center;'>Analys: {h_team} vs {a_team}</h2>", unsafe_allow_html=True)
        
        # Hämtar Live Odds direkt från API-Football
        with st.spinner('Hämtar Unibet PRO-odds för hörnor & kort...'):
            live_odds = fetch_pro_odds(m.get('response.fixture.id'))

        if live_odds:
            st.markdown("<h4 style='text-align: center; color: #10c341;'>💸 Live Odds (Unibet)</h4>", unsafe_allow_html=True)
            oc1, oc2, oc3 = st.columns(3)
            with oc1:
                st.write("**Match (1X2)**")
                for o in live_odds.get('1X2', []): st.write(f"{o['value']}: **{o['odd']}**")
            with oc2:
                st.write("**Hörnor (Över/Under)**")
                for o in live_odds.get('Corners', []): 
                    if "9.5" in o['value'] or "10.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
            with oc3:
                st.write("**Kort (Över/Under)**")
                for o in live_odds.get('Cards', []):
                    if "3.5" in o['value'] or "4.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
        else:
            st.warning("Inga live-odds tillgängliga i API:et just nu för denna match.")
        
        st.divider()
        
        # Historiska snitt baserat på din Raw Data
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        if not h_stats.empty and not a_stats.empty:
            st.markdown("<h4 style='text-align: center;'>📊 Historiska Snitt</h4>", unsafe_allow_html=True)
            stat_comparison_row("xG Snitt", round(h_stats['xG Hemma'].mean(), 2), round(a_stats['xG Borta'].mean(), 2))
            stat_comparison_row("Hörnor Snitt", round(h_stats['Hörnor Hemma'].mean(), 1), round(a_stats['Hörnor Borta'].mean(), 1))
            stat_comparison_row("Kort Snitt", round(h_stats['Gula kort Hemma'].mean(), 1), round(a_stats['Gula Kort Borta'].mean(), 1))

    # --- HUVUDMENY (MATCHCENTER) ---
    else:
        st.title("Deep Stats Pro 2026")
        st.caption(f"Status: PRO-plan aktiv | 7 500 anrop/dag")
        
        tab1, tab2 = st.tabs(["📅 Kommande Matcher", "✅ Senaste Resultat"])
        
        with tab1:
            d_df = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime')
            if d_df.empty:
                st.info("Inga kommande matcher i sikte just nu.")
            for idx, r in d_df.head(25).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                h_logo = r.get('response.teams.home.logo', '')
                a_logo = r.get('response.teams.away.logo', '')

                # Rad-layout
                c_i, c_b = st.columns([5, 1.2])
                with c_i:
                    st.markdown(f'''
                        <div style="background:white; padding:12px; border-radius:10px; border:1px solid #eee; margin-bottom:8px; display:flex; align-items:center;">
                            <div style="width:75px; font-size:0.85em; color:#666;">{r["datetime"].strftime("%d %b %H:%M")}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{h_logo}" width="25"></div>
                            <div style="background:#f0f0f0; color:#333; padding:2px 15px; margin:0 20px; border-radius:5px; font-weight:bold;">VS</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{a_logo}" width="25"> {a_name}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_b:
                    if st.button("Analys", key=f"h2h_{idx}", use_container_width=True):
                        st.session_state.view_h2h = r
                        st.rerun()

        with tab2:
            r_df = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            for idx, r in r_df.head(25).iterrows():
                c_i, c_b = st.columns([5, 1.2])
                with c_i:
                    score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f'''
                        <div style="background:#f9f9f9; padding:12px; border-radius:10px; margin-bottom:8px; display:flex; align-items:center; border: 1px solid #eee;">
                            <div style="width:75px; font-size:0.85em; color:#666;">{r["datetime"].strftime("%d %b")}</div>
                            <div style="flex:1; text-align:right;">{r['response.teams.home.name']}</div>
                            <div style="background:#222; color:white; padding:2px 15px; margin:0 20px; border-radius:5px; font-weight:bold;">{score}</div>
                            <div style="flex:1; text-align:left;">{r['response.teams.away.name']}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_b:
                    if st.button("Statistik", key=f"res_{idx}", use_container_width=True):
                        st.session_state.view_match = r
                        st.rerun()
else:
    st.error("Kunde inte ansluta till din Google Sheet. Kontrollera att den är delad så att 'alla med länken kan se'.")
