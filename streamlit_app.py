import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats Pro 2026 - Diamond Edition", layout="wide")

ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"

# --- 2. ODDS-FUNKTIONER (PRECISIONS-ANROP) ---
@st.cache_data(ttl=600)
def fetch_odds_by_key(sport_key):
    """Anropar exakt liga baserat på sport_key för att spara credits."""
    if not ODDS_API_KEY or not sport_key:
        return []
    # Vi använder liganyckeln direkt i URL:en för maximal effektivitet
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    try:
        res = requests.get(url)
        if res.status_code == 429: return "QUOTA_EXCEEDED"
        return res.json() if res.status_code == 200 else []
    except:
        return []

def match_team_names(sheet_name, api_name):
    """Säkerställer att Manchester United inte blir City, och att Tottenham matchar."""
    def clean(n):
        n = str(n).lower()
        if "manchester united" in n or "man utd" in n: return "manutd"
        if "manchester city" in n or "man city" in n: return "mancity"
        if "tottenham" in n: return "spurs"
        if "nottingham" in n: return "nottinghamforest"
        return "".join(filter(str.isalnum, n))
    
    return clean(sheet_name) == clean(api_name)

# --- 3. DATA-LADDNING & TVÄTT ---
@st.cache_data(ttl=60)
def load_and_clean_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        
        # Om sport_key saknas i arket, sätt Premier League som standard
        if 'sport_key' not in data.columns:
            data['sport_key'] = 'soccer_epl'
            
        # Kraftfull tvätt av numeriska värden (Hörnor, xG etc)
        numeric_cols = ['xG Hemma', 'xG Borta', 'Hörnor Hemma', 'Hörnor Borta', 
                        'Gula kort Hemma', 'Gula Kort Borta', 'response.goals.home', 'response.goals.away',
                        'Bollinnehav Hemma', 'Bollinnehav Borta']
        
        for col in numeric_cols:
            if col in data.columns:
                # Rensar bort % och andra tecken, ersätter komma med punkt
                clean_val = data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True)
                data[col] = pd.to_numeric(clean_val, errors='coerce').fillna(0)
        
        if 'response.fixture.date' in data.columns:
            data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
            
        return data
    except Exception as e:
        st.error(f"Fel vid inläsning: {e}")
        return None

df = load_and_clean_data(RAW_DATA_URL)

# --- 4. UI-HJÄLPARE ---
def stat_row(label, v1, v2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    s = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.1em;'>{v1}{s}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{v2}{s}</div>", unsafe_allow_html=True)

# --- 5. NAVIGATION ---
if 'view' not in st.session_state: st.session_state.view = 'list'
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

# --- 6. VYER ---
if df is not None:
    # --- VY: H2H ANALYS ---
    if st.session_state.view == 'h2h' and st.session_state.selected_match is not None:
        if st.button("← Tillbaka"):
            st.session_state.view = 'list'
            st.rerun()
            
        m = st.session_state.selected_match
        h_t, a_t = m['response.teams.home.name'], m['response.teams.away.name']
        s_key = m['sport_key']
        
        st.markdown(f"<h1 style='text-align: center;'>{h_t} vs {a_t}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray;'>Liga: {s_key}</p>", unsafe_allow_html=True)

        # Statistik-beräkning
        h_h = df[(df['response.teams.home.name'] == h_t) & (df['response.fixture.status.short'] == 'FT')]
        a_h = df[(df['response.teams.away.name'] == a_t) & (df['response.fixture.status.short'] == 'FT')]

        if not h_h.empty and not a_h.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mål snitt", round(h_h['response.goals.home'].mean() + a_h['response.goals.away'].mean(), 2))
            c2.metric("xG snitt", round(h_h['xG Hemma'].mean() + a_h['xG Borta'].mean(), 2))
            c3.metric("Hörnor snitt", round(h_h['Hörnor Hemma'].mean() + a_h['Hörnor Borta'].mean(), 1))
            c4.metric("Gula Kort snitt", round(h_h['Gula kort Hemma'].mean() + a_h['Gula Kort Borta'].mean(), 1))

        st.divider()

        # Odds-hämtning
        st.subheader("Marknadsodds (Unibet)")
        league_odds = fetch_odds_by_key(s_key)
        
        if league_odds == "QUOTA_EXCEEDED":
            st.error("API-kvoten är slut.")
        elif not league_odds:
            st.warning(f"Inga odds hittades för {s_key}.")
        else:
            match_data = next((lo for lo in league_odds if match_team_names(h_t, lo['home_team']) and match_team_names(a_t, lo['away_team'])), None)
            
            if match_data and match_data['bookmakers']:
                oc1, oc2 = st.columns(2)
                for mkt in match_data['bookmakers'][0]['markets']:
                    if mkt['key'] == 'h2h':
                        with oc1:
                            st.write("**1X2 Odds**")
                            for o in mkt['outcomes']: st.write(f"{o['name']}: **{o['price']}**")
                    if mkt['key'] == 'totals':
                        with oc2:
                            st.write("**Över/Under 2.5**")
                            for o in mkt['outcomes']:
                                if o.get('point') == 2.5:
                                    st.write(f"{o['name']}: **{o['price']}**")
            else:
                st.info("Hittade matchen i API:et men inga odds är satta ännu.")

    # --- VY: LISTA ---
    else:
        st.header("Kommande Matcher")
        search = st.text_input("Sök lag...", "")
        
        upcoming = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime')
        if search:
            upcoming = upcoming[(upcoming['response.teams.home.name'].str.contains(search, case=False)) | 
                                (upcoming['response.teams.away.name'].str.contains(search, case=False))]

        for idx, r in upcoming.head(30).iterrows():
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div style="background:white; padding:12px; border-radius:8px; border:1px solid #eee; display:flex; align-items:center; margin-bottom:8px;">
                    <div style="width:110px; color:gray; font-size:0.8em;">{r['datetime'].strftime('%d %b %H:%M') if pd.notnull(r['datetime']) else ''}</div>
                    <div style="flex:1; text-align:right; font-weight:bold;">{r['response.teams.home.name']}</div>
                    <div style="margin:0 15px; font-weight:bold; color:#555;">VS</div>
                    <div style="flex:1; text-align:left; font-weight:bold;">{r['response.teams.away.name']}</div>
                    <div style="margin-left:20px; font-size:0.7em; color:blue;">{r['sport_key']}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("Analysera", key=f"btn_{idx}", use_container_width=True):
                    st.session_state.selected_match = r
                    st.session_state.view = 'h2h'
                    st.rerun()
else:
    st.error("Kunde inte ladda data.")
