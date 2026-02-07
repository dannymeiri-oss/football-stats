import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. KONFIGURATION (PERFEKT LAYOUT - RÖR EJ) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")
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
.bet-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 10px; }
.good-bet { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.bad-bet { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
/* DOMARE INFO I H2H */
.referee-box { text-align: center; background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 20px; font-weight: bold; color: #333; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=712668345"

# --- 2. DATAHANTERING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

def get_rolling_card_avg(team_name, full_df, n=10):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name))].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 2.0
    cards = []
    for _, r in team_matches.iterrows():
        if r['response.teams.home.name'] == team_name:
            cards.append(float(r.get('Gula kort Hemma', 0)))
        else:
            cards.append(float(r.get('Gula Kort Borta', 0)))
    return sum(cards) / len(cards)

def get_referee_stats(ref_name, full_df, n=10):
    if not ref_name or "Okänd" in ref_name: return 4.0
    raw_name = ref_name.replace("Domare: ", "")
    ref_matches = full_df[full_df['response.fixture.referee'].str.contains(raw_name, na=False, case=False)].sort_values('datetime', ascending=False).head(n)
    if ref_matches.empty: return 4.0
    total_cards = ref_matches['Gula kort Hemma'].fillna(0) + ref_matches['Gula Kort Borta'].fillna(0)
    return total_cards.mean()

def format_referee(name):
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None", ""]:
        return "Domare: Okänd"
    return f"Domare: {str(name).split(',')[0].strip()}"

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce').dt.tz_localize(None)
    needed_cols = ['Gula kort Hemma', 'Gula Kort Borta', 'xG Hemma', 'xG Borta']
    for col in needed_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, x1, x2, is_pct=False, precision=2):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    v1 = f"{x1:.{precision}f}" if not pd.isna(x1) else "0.0"
    v2 = f"{x2:.{precision}f}" if not pd.isna(x2) else "0.0"
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{v1}</div><div style='color:#ccc; margin:0 10px;'>|</div><div style='flex:1; text-align:left;'>{v2}</div></div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode == "h2h_detail":
        if st.button("← Tillbaka"):
            st.session_state.view_mode = "main"
            st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        # DOMARINFO ÖVERST
        ref_name = m['ref_clean']
        ref_avg = get_referee_stats(ref_name, df)
        st.markdown(f"<div class='referee-box'>{ref_name} (Snitt: {ref_avg:.2f} gula)</div>", unsafe_allow_html=True)

        # AI CARD PREDICTIONS SEKTION
        st.markdown("<div class='section-header'>AI CARD PREDICTIONS</div>", unsafe_allow_html=True)
        
        h_card_avg = get_rolling_card_avg(h_team, df)
        a_card_avg = get_rolling_card_avg(a_team, df)
        
        # Prediktion per lag: (Lagets snitt + (Domarsnitt / 2)) / 2  (En balanserad viktning)
        h_pred = (h_card_avg + (ref_avg / 2)) / 2
        a_pred = (a_card_avg + (ref_avg / 2)) / 2
        
        stat_comparison_row("PREDIKTERADE KORT", h_pred, a_pred)
        
        col1, col2 = st.columns(2)
        with col1:
            if h_pred >= 2.0:
                st.markdown(f"<div class='bet-box good-bet'>BRA SPEL: {h_team} ÖVER 1.5/2.0 KORT</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bet-box bad-bet'>INGET BRA SPEL PÅ {h_team}</div>", unsafe_allow_html=True)
        with col2:
            if a_pred >= 2.0:
                st.markdown(f"<div class='bet-box good-bet'>BRA SPEL: {a_team} ÖVER 1.5/2.0 KORT</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bet-box bad-bet'>INGET BRA SPEL PÅ {a_team}</div>", unsafe_allow_html=True)

        # SEASON AVERAGES
        st.markdown("<div class='section-header'>SEASON AVERAGES COMPARISON</div>", unsafe_allow_html=True)
        stat_comparison_row("EXPECTED GOALS (xG)", df[df['response.teams.home.name'] == h_team]['xG Hemma'].mean(), df[df['response.teams.away.name'] == a_team]['xG Borta'].mean())
        stat_comparison_row("GULA KORT (SNITT)", h_card_avg, a_card_avg)

    else:
        st.markdown("<div class='section-header'>DAGENS MATCHER</div>", unsafe_allow_html=True)
        for idx, row in df.head(15).iterrows():
            if st.button(f"{row['response.teams.home.name']} vs {row['response.teams.away.name']}", key=f"btn_{idx}"):
                st.session_state.selected_match = row
                st.session_state.view_mode = "h2h_detail"
                st.rerun()
