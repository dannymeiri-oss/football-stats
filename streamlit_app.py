import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. DATA-LADDNING ---
@st.cache_data(ttl=600) # Sparar Google Sheets data i 10 min
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

# --- 3. ODDS-MOTOR (OPTIMERAD FÖR CREDITS) ---
@st.cache_data(ttl=600) # VIKTIGT: Detta sparar 1 credit i 10 minuter!
def fetch_all_odds():
    """Hämtar alla odds för en liga i ETT anrop istället för per match"""
    if not ODDS_API_KEY:
        return None
    
    # Vi hämtar Premier League som exempel. Du kan ändra 'soccer_epl' till 'soccer' för fler, 
    # men specifika ligor är ofta säkrare för matchning.
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_match_odds_from_cache(home_sheet, away_sheet, all_odds):
    """Letar upp rätt match i den redan hämtade listan (kostar 0 credits)"""
    if not all_odds:
        return None, None
    
    def normalize(name):
        return "".join(filter(str.isalnum, name.lower()))

    h_s = normalize(home_sheet)
    a_s = normalize(away_sheet)
    
    for match in all_odds:
        h_api = normalize(match['home_team'])
        a_api = normalize(match['away_team'])
        
        if (h_s in h_api or h_api in h_s) and (a_s in a_api or a_api in a_s):
            h2h = None
            totals = None
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                for market in match['bookmakers'][0]['markets']:
                    if market['key'] == 'h2h': h2h = market['outcomes']
                    if market['key'] == 'totals': totals = [o for o in market['outcomes'] if o['point'] == 2.5]
            return h2h, totals
    return None, None

# --- 4. STATISTIK-RENSNING ---
def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    # (Samma kolumner som tidigare...)
    cols_to_ensure = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 'Gula kort Hemma', 'Gula Kort Borta', 'response.goals.home', 'response.goals.away', 'response.fixture.status.short', 'response.teams.home.name', 'response.teams.away.name', 'response.teams.home.logo', 'response.teams.away.logo', 'response.fixture.referee']
    for col in cols_to_ensure:
        if col not in data.columns: data[col] = 0
    
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

# --- 5. APP-LOGIK ---
df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left;'>{val2}{suffix}</div>", unsafe_allow_html=True)

if df is not None:
    # VY: H2H (Här används API-anropet)
    if st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"):
            st.session_state.view_h2h = None
            st.rerun()
        
        m = st.session_state.view_h2h
        h_team = m['response.teams.home.name']
        a_team = m['response.teams.away.name']
        
        st.title(f"{h_team} vs {a_team}")
        
        # HÄR SPARAR VI CREDITS: Hämtar alla odds en gång, sen letar vi i minnet
        with st.spinner('Hämtar marknadsodds...'):
            all_market_odds = fetch_all_odds()
            h2h, totals = get_match_odds_from_cache(h_team, a_team, all_market_odds)

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Odds (Unibet)")
            if h2h:
                for o in h2h: st.write(f"{o['name']}: **{o['price']}**")
            else: st.info("Inga odds tillgängliga i cachen.")
            
        with col_right:
            st.subheader("Över/Under 2.5")
            if totals:
                for o in totals: st.write(f"{o['name']}: **{o['price']}**")
            else: st.info("-")

        st.divider()
        # Statistik-jämförelse
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        if not h_stats.empty and not a_stats.empty:
            stat_comparison_row("xG Snitt", round(h_stats['xG Hemma'].mean(),2), round(a_stats['xG Borta'].mean(),2))
            stat_comparison_row("Mål Snitt", round(h_stats['response.goals.home'].mean(),2), round(a_stats['response.goals.away'].mean(),2))

    # VY: HUVUDMENY
    else:
        tab1, tab2 = st.tabs(["📅 Matcher", "🏆 Tabell"])
        with tab1:
            mode = st.radio("Visa:", ["Kommande matcher", "Resultat"], horizontal=True)
            status = 'NS' if mode == "Kommande matcher" else 'FT'
            d_df = df[df['response.fixture.status.short'] == status].sort_values('datetime')
            
            for idx, r in d_df.head(30).iterrows(): # Vi begränsar till 30 matcher
                col_m, col_b = st.columns([5, 1])
                col_m.write(f"{r['datetime'].strftime('%d %b')} | {r['response.teams.home.name']} - {r['response.teams.away.name']}")
                if col_b.button("Analys", key=f"btn{idx}"):
                    if status == 'NS':
                        st.session_state.view_h2h = r
                    else:
                        st.session_state.view_match = r
                    st.rerun()

        with tab2:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True)
