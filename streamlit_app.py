import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# API-NYCKEL (Din personliga nyckel)
ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. DATA-LADDNING MED CACHE (Sparar laddningstid) ---
@st.cache_data(ttl=600)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

# --- 3. ODDS-MOTOR (SPARAR CREDITS) ---
@st.cache_data(ttl=600) # Sparar resultatet i 10 minuter = Max 6 anrop i timmen oavsett klick
def fetch_all_odds():
    """Hämtar alla odds för Premier League i ett svep (1 credit totalt)"""
    if not ODDS_API_KEY:
        return None
    
    # Vi fokuserar på Premier League för att spara credits. 
    # Ändra 'soccer_epl' om du vill byta liga.
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_match_odds_from_cache(home_sheet, away_sheet, all_odds):
    """Letar upp rätt match i den cachade listan utan att göra nytt API-anrop"""
    if not all_odds:
        return None, None
    
    def normalize(name):
        return "".join(filter(str.isalnum, name.lower()))

    h_s = normalize(home_sheet)
    a_s = normalize(away_sheet)
    
    for match in all_odds:
        h_api = normalize(match['home_team'])
        a_api = normalize(match['away_team'])
        
        # Dubbelkoll: Båda lagen måste matcha för att undvika Man Utd vs Man City fel
        if (h_s in h_api or h_api in h_s) and (a_s in a_api or a_api in a_s):
            h2h = None
            totals = None
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                for market in match['bookmakers'][0]['markets']:
                    if market['key'] == 'h2h': h2h = market['outcomes']
                    if market['key'] == 'totals': totals = [o for o in market['outcomes'] if o['point'] == 2.5]
            return h2h, totals
    return None, None

# --- 4. RENSA STATISTIK ---
def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'response.goals.home', 'response.goals.away', 
        'response.fixture.status.short', 'response.teams.home.name', 'response.teams.away.name',
        'response.teams.home.logo', 'response.teams.away.logo', 'response.fixture.referee'
    ]
    for col in cols_to_ensure:
        if col not in data.columns: data[col] = 0
            
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

# --- 5. LOGIK FÖR APPEN ---
df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- VY: H2H & ODDS ---
if st.session_state.view_h2h is not None:
    if st.button("← Tillbaka"):
        st.session_state.view_h2h = None
        st.rerun()
    
    m = st.session_state.view_h2h
    h_team = m['response.teams.home.name']
    a_team = m['response.teams.away.name']
    
    st.title(f"{h_team} vs {a_team}")
    
    # Hämtar alla odds (Cachat)
    all_market_odds = fetch_all_odds()
    h2h, totals = get_match_odds_from_cache(h_team, a_team, all_market_odds)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Matchodds (1X2)")
        if h2h:
            for o in sorted(h2h, key=lambda x: x['name'] == 'Draw'):
                st.write(f"{o['name']}: **{o['price']}**")
        else: st.info("Inga odds i cachen.")
    with col2:
        st.subheader("Över/Under 2.5")
        if totals:
            for o in totals:
                lbl = "Över" if o['name'].lower() == "over" else "Under"
                st.write(f"{lbl} 2.5: **{o['price']}**")
        else: st.info("-")

    st.divider()
    # Historisk statistik
    h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
    a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
    if not h_stats.empty and not a_stats.empty:
        stat_comparison_row("xG Snitt", round(h_stats['xG Hemma'].mean(),2), round(a_stats['xG Borta'].mean(),2))
        stat_comparison_row("Mål Snitt", round(h_stats['response.goals.home'].mean(),2), round(a_stats['response.goals.away'].mean(),2))

# --- VY: HUVUDLISTA ---
elif df is not None:
    tab1, tab2, tab3 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "🏆 Tabell"])
    
    with tab1:
        st.header("Matchcenter")
        mode = st.radio("Visa:", ["Kommande (Max 30)", "Resultat"], horizontal=True)
        status = 'NS' if mode == "Kommande (Max 30)" else 'FT'
        
        d_df = df[df['response.fixture.status.short'] == status].sort_values('datetime', ascending=(status=='NS'))
        
        for idx, r in d_df.head(30).iterrows():
            c_m, c_b = st.columns([5, 1])
            with c_m:
                st.markdown(f"{r['datetime'].strftime('%d %b')} | **{r['response.teams.home.name']} - {r['response.teams.away.name']}**")
            with c_b:
                if st.button("Analys", key=f"btn{idx}"):
                    if status == 'NS': st.session_state.view_h2h = r
                    else: st.session_state.view_match = r
                    st.rerun()

    with tab2:
        st.write("Välj en match i listan för att se djupare lagstatistik.")
    
    with tab3:
        if standings_df is not None: st.dataframe(standings_df, use_container_width=True)

else:
    st.error("Kunde inte ladda data från Google Sheets.")
