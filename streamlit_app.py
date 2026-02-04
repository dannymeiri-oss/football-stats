import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import numpy as np

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    .alert-container { display: flex; align-items: center; justify-content: flex-start; gap: 10px; }
    .bell-icon { font-size: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "6343cd4636523af501b585a1b595ad26" 
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "1363673756" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. ODDS-MOTOR ---
@st.cache_data(ttl=600)
def fetch_api_football_odds(fixture_id):
    if not fixture_id: return None
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}&bookmaker=11"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        if not data['response']: return None
        markets = data['response'][0]['bookmakers'][0]['markets']
        odds_dict = {}
        for m in markets:
            if m['name'] == "Match Winner": odds_dict['1X2'] = m['values']
            if m['name'] == "Both Teams Score": odds_dict['BTTS'] = m['values']
            if m['name'] == "Corners Over/Under": odds_dict['Corners'] = m['values']
            if m['name'] == "Cards Over/Under": odds_dict['Cards'] = m['values']
            if m['name'] == "Goals Over/Under": odds_dict['Totals'] = m['values']
        return odds_dict
    except: return None

# --- 3. DATAHANTERING ---
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
    cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
            'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
            'response.goals.home', 'response.goals.away']
    for col in cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
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
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 4. VISUALISERING ---
if df is not None:
    # --- RESULTAT-VY ---
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

    # --- ANALYS-VY (H2H) ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h2 style='text-align: center;'>{h_team} vs {a_team}</h2>", unsafe_allow_html=True)
        
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        # Metrics & Jämförelse
        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Mål snitt", round(h_stats['response.goals.home'].mean() + a_stats['response.goals.away'].mean(), 2))
        tc2.metric("xG snitt", round(h_stats['xG Hemma'].mean() + a_stats['xG Borta'].mean(), 2))
        tc3.metric("Hörnor snitt", round(h_stats['Hörnor Hemma'].mean() + a_stats['Hörnor Borta'].mean(), 1))
        tc4.metric("Gula snitt", round(h_stats['Gula kort Hemma'].mean() + a_stats['Gula Kort Borta'].mean(), 1))
        
        st.write("") 
        stat_comparison_row("Mål/Match", round(h_stats['response.goals.home'].mean(), 2), round(a_stats['response.goals.away'].mean(), 2))
        stat_comparison_row("xG/Match", round(h_stats['xG Hemma'].mean(), 2), round(a_stats['xG Borta'].mean(), 2))
        stat_comparison_row("Hörnor snitt", round(h_stats['Hörnor Hemma'].mean(), 1), round(a_stats['Hörnor Borta'].mean(), 1))
        
        st.divider()

        # ODDS
        st.markdown("<h4 style='text-align: center;'>💸 Live Odds (API-Football)</h4>", unsafe_allow_html=True)
        odds = fetch_api_football_odds(m.get('response.fixture.id'))
        if odds:
            o1, o2, o3 = st.columns(3)
            with o1:
                if '1X2' in odds:
                    st.write("**1X2**")
                    for o in odds['1X2']: st.write(f"{o['value']}: **{o['odd']}**")
            with o2:
                if 'Corners' in odds:
                    st.write("**Hörnor 9.5**")
                    for o in odds['Corners']: 
                        if "9.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
            with o3:
                if 'Cards' in odds:
                    st.write("**Kort 3.5**")
                    for o in odds['Cards']:
                        if "3.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
        
        st.divider()

        # INBÖRDES
        st.markdown("<h3 style='text-align: center;'>Inbördes Möten</h3>", unsafe_allow_html=True)
        h2h_matches = df[
            ((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
            ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))
        ].copy()
        
        if not h2h_matches.empty:
            h2h_matches = h2h_matches[h2h_matches['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            h2h_display = h2h_matches[['datetime', 'response.teams.home.name', 'response.goals.home', 'response.goals.away', 'response.teams.away.name']].copy()
            h2h_display['datetime'] = h2h_display['datetime'].dt.strftime('%d %b %Y')
            h2h_display.columns = ['Datum', 'Hemmalag', ' ', '  ', 'Bortalag']
            
            _, center_col, _ = st.columns([1, 6, 1])
            with center_col:
                st.dataframe(h2h_display, hide_index=True, use_container_width=True)
        else:
            st.info("Inga tidigare möten hittades.")

    # --- HUVUDMENY ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🏆 Tabell", "🛡️ Laganalys", "⚖️ Domare"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(40).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                h_logo, a_logo = r.get('response.teams.home.logo', ''), r.get('response.teams.away.logo', '')
                
                show_alert = False
                if mode == "Nästa matcher":
                    h_c = df[df['response.teams.home.name'] == h_name]['Gula kort Hemma'].mean()
                    a_c = df[df['response.teams.away.name'] == a_name]['Gula Kort Borta'].mean()
                    if (np.nan_to_num(h_c) + np.nan_to_num(a_c)) >= 3.4: show_alert = True

                c_i, c_b = st.columns([4, 2]) # Justerad bredd för att få plats med båda
                score_text = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Resultat" else "VS"
                
                with c_i:
                    st.markdown(f'''
                        <div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                            <div style="width:80px; font-size:0.8em; color:gray;">{r["datetime"].strftime("%d %b")}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{h_logo}" width="22"></div>
                            <div style="background:#222; color:white; padding:2px 12px; margin:0 15px; border-radius:4px; font-weight:bold; min-width:65px; text-align:center;">{score_text}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{a_logo}" width="22"> {a_name}</div>
                            <div style="margin-left:10px; font-size:0.7em; color:blue; width:100px;">{r.get("response.league.name", "")}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_b:
                    # Klockan till HÖGER om knappen
                    col_btn, col_bell = st.columns([3, 1])
                    with col_btn:
                        if st.button("H2H", key=f"btn{idx}", use_container_width=True):
                            if mode=="Nästa matcher": st.session_state.view_h2h = r
                            else: st.session_state.view_match = r
                            st.rerun()
                    with col_bell:
                        if show_alert and mode == "Nästa matcher":
                            st.markdown("<div style='padding-top:5px; font-size:1.5rem;'>🔔</div>", unsafe_allow_html=True)

        with tab2:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True)
        with tab3:
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team: st.dataframe(df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)].head(15))
        with tab4:
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                st.metric("Gula/Match (Snitt)", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                st.dataframe(r_df)
else:
    st.error("Kunde inte ladda data.")
