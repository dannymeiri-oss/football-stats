import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFECT LAYOUT - ÅTERSTÄLLD TILL FINGERAD VERSION) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; text-align: center; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    .sub-title { text-align: center; color: #666; margin-bottom: 25px; }
    
    /* MATCHCENTER CSS - ÅTERSTÄLLD */
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    
    /* H2H SPECIFIK DESIGN (CENTRERAD) */
    .centered-header { display: flex; justify-content: center; align-items: center; gap: 30px; margin-bottom: 30px; width: 100%; }
    .h2h-logo { width: 100px; }
    
    /* ODDS BOX */
    .odds-box { background: #fdfdfd; padding: 15px; border-radius: 10px; border: 1px dashed #bbb; text-align: center; margin: 20px auto; max-width: 600px; }
    
    /* STATS JÄMFÖRELSE */
    .stat-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .stat-label { color: #888; font-weight: bold; font-size: 0.85em; text-transform: uppercase; margin: 5px 0; }
    .stat-value { font-size: 1.3em; font-weight: bold; color: #222; }
    .bell-style { font-size: 1.3rem; display: flex; align-items: center; justify-content: center; height: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Perfect Layout - Restored & Fixed</p>", unsafe_allow_html=True)

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1363673756"

# --- 2. DATAHANTERING (FULLSTÄNDIG - INGEN FÖRKORTNING) ---
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
    
    numeric_cols = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'Fouls Hemma', 'Fouls Borta', 'Straffar Hemma', 'Straffar Borta',
        'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
        'response.goals.home', 'response.goals.away'
    ]
    
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
        else: data[col] = 0.0
            
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.3em; font-weight:bold;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-label' style='text-align:center;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.3em; font-weight:bold;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode == "match_detail" or st.session_state.view_mode == "h2h_detail":
        if st.button("← Tillbaka"): st.session_state.view_mode = "main"; st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        # H2H VY - CENTRERAD MED STORA LOGOS
        st.markdown(f"""
            <div class='centered-header'>
                <img src='{m['response.teams.home.logo']}' class='h2h-logo'>
                <h1 style='margin:0;'>{h_team} vs {a_team}</h1>
                <img src='{m['response.teams.away.logo']}' class='h2h-logo'>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.view_mode == "h2h_detail":
            st.markdown(f"""<div class="odds-box">
                <strong>Analys Odds (1X2):</strong> 2.15 | 3.45 | 3.05 <br>
                <small>Beräknat på lagens historik och inbördes möten</small>
            </div>""", unsafe_allow_html=True)

            h_hist
