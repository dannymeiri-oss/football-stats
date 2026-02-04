import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# --- 2. LIGA-MAPPNING ---
def get_sport_key(league_name):
    ln = str(league_name).lower()
    mapping = {
        "premier league": "soccer_epl",
        "allsvenskan": "soccer_sweden_allsvenskan",
        "la liga": "soccer_spain_la_liga",
        "serie a": "soccer_italy_serie_a",
        "bundesliga": "soccer_germany_bundesliga",
        "ligue 1": "soccer_france_ligue_1",
        "superettan": "soccer_sweden_superettan"
    }
    return mapping.get(ln, "soccer_epl")

# --- 3. OPTIMERAD ODDS-MOTOR ---
@st.cache_data(ttl=600)
def fetch_odds_safe(sport_key):
    # Vi kör bara h2h (1X2) för att vara 100% säkra på att undvika felkod 422
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&bookmakers=unibet"
    try:
        res = requests.get(url)
        if res.status_code == 200: return res.json(), url
        return f"ERROR_{res.status_code}", url
    except Exception as e:
        return f"ERROR_{str(e)}", url

def find_match_in_odds(h_sheet, a_sheet, odds_list):
    if not isinstance(odds_list, list): return None, "Inget API-svar"
    
    def simplify(name):
        # Tar bort allt utom bokstäver och gör små bokstäver
        name = str(name).lower()
        for word in ["united", "utd", "city", "wanderers", "town", "fc", "afc"]:
            name = name.replace(word, "")
        return "".join(filter(str.isalpha, name))

    h_s, a_s = simplify(h_sheet), simplify(a_sheet)
    
    for match in odds_list:
        h_api, a_api = simplify(match['home_team']), simplify(match['away_team'])
        # Matchar om namnen liknar varandra
        if (h_s in h_api or h_api in h_s) and (a_s in a_api or a_api in a_s):
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                return match['bookmakers'][0]['markets'][0]['outcomes'], "MATCH_FOUND"
    
    return None, f"Hittade ingen match för '{h_s}' vs '{a_s}' i API-listan"

# --- 4. DATAHANTERING ---
@st.cache_data(ttl=60)
def get_data():
    try:
        df = pd.read_csv(RAW_DATA_URL)
        df.columns = [c.strip() for c in df.columns]
        if 'response.fixture.date' in df.columns:
            df['datetime'] = pd.to_datetime(df['response.fixture.date'], errors='coerce')
        # Tvätta siffror
        cols = ['xG Hemma', 'xG Borta', 'Hörnor Hemma', 'Hörnor Borta', 'Gula kort Hemma', 'Gula Kort Borta']
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        return df
    except: return None

df = get_data()

# --- 5. GUI ---
if df is not None:
    if 'view' not in st.session_state: st.session_state.view = "list"
    if 'selected_match' not in st.session_state: st.session_state.selected_match = None

    if st.session_state.view == "h2h":
        if st.button("← Tillbaka"):
            st.session_state.view = "list"
            st.rerun()
            
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        st.markdown(f"<h1 style='text-align:center;'>{h_team} vs {a_team}</h1>", unsafe_allow_html=True)
        
        # Hämta Odds
        s_key = get_sport_key(m.get('response.league.name', ''))
        api_data, debug_url = fetch_odds_safe(s_key)
        odds, match_status = find_match_in_odds(h_team, a_team, api_data)
        
        # Visa Odds
        st.subheader("💸 Marknadsodds (Unibet 1X2)")
        if odds:
            c1, c2, c3 = st.columns(3)
            for o in odds:
                if o['name'] == h_team or simplify(o['name']) in simplify(h_team): c1.metric("1", o['price'])
                elif o['name'] == "Draw": c2.metric("X", o['price'])
                else: c3.metric("2", o['price'])
        else:
            st.info("Odds ej tillgängliga just nu.")

        st.divider()
        
        # Historik-snitt
        h_hist = df[df['response.teams.home.name'] == h_team]
        a_hist = df[df['response.teams.away.name'] == a_team]
        
        st.subheader("📊 Historiska Snitt")
        col1, col2, col3 = st.columns(3)
        col1.metric("xG Match", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2))
        col2.metric("Hörnor Match", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1))
        col3.metric("Gula Kort Match", round(h_hist['Gula kort Hemma'].mean() + a_hist['Gula Kort Borta'].mean(), 1))

        # DEBUG CONSOLE
        with st.expander("🛠️ Debut Console: API & Matchning"):
            st.write(f"**Anropad Liga:** {s_key}")
            st.write(f"**API Status:** {'✅ OK' if isinstance(api_data, list) else f'❌ {api_data}'}")
            st.write(f"**Matchning Status:** {match_status}")
            st.write(f"**Antal matcher i svar:** {len(api_data) if isinstance(api_data, list) else 0}")
            if isinstance(api_data, list):
                st.write("**Lag i API:et just nu:**")
                st.write([f"{x['home_team']} vs {x['away_team']}" for x in api_data[:5]])

    else:
        st.title("📅 Matchcenter")
        # Filtrera bara kommande matcher (där status inte är FT)
        upcoming = df[df['response.fixture.status.short'] != 'FT'].sort_values('datetime')
        
        for idx, r in upcoming.head(20).iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; border:1px solid #eee; margin-bottom:10px;">
                    <span style="color:gray; font-size:0.8em;">{r['datetime'].strftime('%d %b %H:%M')}</span><br>
                    <b>{r['response.teams.home.name']} vs {r['response.teams.away.name']}</b><br>
                    <span style="color:blue; font-size:0.7em;">{r.get('response.league.name', 'Liga')}</span>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("Analys", key=f"btn_{idx}"):
                    st.session_state.selected_match = r
                    st.session_state.view = "h2h"
                    st.rerun()
else:
    st.error("Kunde inte ladda data från kalkylbladet.")
