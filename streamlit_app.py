import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. KONFIGURATION & NYCKLAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide", initial_sidebar_state="collapsed")

API_KEY = "6343cd4636523af501b585a1b595ad26"
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# --- 2. ODDS-MOTOR (DIREKT FRÅN API-FOOTBALL) ---
def fetch_pro_odds(fixture_id):
    """Hämtar Unibet-odds (ID 11) direkt via din PRO-kvota"""
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}&bookmaker=11"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        if not data['response']: return None
        
        markets = data['response'][0]['bookmakers'][0]['markets']
        results = {}
        for m in markets:
            if m['name'] == "Match Winner": results['1X2'] = m['values']
            if m['name'] == "Corners Over/Under": results['Corners'] = m['values']
            if m['name'] == "Cards Over/Under": results['Cards'] = m['values']
            if m['name'] == "Both Teams Score": results['BTTS'] = m['values']
        return results
    except:
        return None

# --- 3. DATAHANTERING (GULD-LOGIK FRÅN SHEETS) ---
@st.cache_data(ttl=60)
def load_and_clean_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        if 'response.fixture.date' in data.columns:
            data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        
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

# --- 4. GULD-LAYOUT KOMPONENTER ---
def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.2em; font-weight:bold;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-size:0.9em; padding-top:5px;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.2em; font-weight:bold;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 5. HUVUDMENY & VISUALISERING ---
if df is not None:
    # --- VY: STATISTIK (SPELADE MATCHER) ---
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

    # --- VY: ANALYS (KOMMANDE MATCHER MED DIREKT-ODDS) ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        st.markdown(f"<h1 style='text-align: center;'>{h_team} vs {a_team}</h1>", unsafe_allow_html=True)
        
        # HÄMTA ODDS DIREKT FRÅN API
        with st.spinner('Hämtar Unibet PRO-odds...'):
            live_odds = fetch_pro_odds(m.get('response.fixture.id'))

        if live_odds:
            st.markdown("<div style='background:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
            oc1, oc2, oc3 = st.columns(3)
            with oc1:
                st.write("**1X2 (Unibet)**")
                for o in live_odds.get('1X2', []): st.write(f"{o['value']}: **{o['odd']}**")
            with oc2:
                st.write("**Hörnor (Ö 9.5)**")
                for o in live_odds.get('Corners', []): 
                    if "9.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
            with oc3:
                st.write("**Kort (Ö 3.5)**")
                for o in live_odds.get('Cards', []):
                    if "3.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        if not h_hist.empty and not a_hist.empty:
            stat_comparison_row("xG Snitt", round(h_hist['xG Hemma'].mean(), 2), round(a_hist['xG Borta'].mean(), 2))
            stat_comparison_row("Hörnor Snitt", round(h_hist['Hörnor Hemma'].mean(), 1), round(a_hist['Hörnor Borta'].mean(), 1))
            stat_comparison_row("Kort Snitt", round(h_hist['Gula kort Hemma'].mean(), 1), round(a_hist['Gula Kort Borta'].mean(), 1))

    # --- VY: MATCHCENTER ---
    else:
        st.title("Deep Stats Pro 2026")
        tab1, tab2 = st.tabs(["📅 Kommande", "✅ Resultat"])
        
        with tab1:
            future_df = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime')
            for idx, r in future_df.head(25).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                
                # Logik för varningsklocka
                h_c_avg = df[df['response.teams.home.name'] == h_name]['Gula kort Hemma'].mean()
                a_c_avg = df[df['response.teams.away.name'] == a_name]['Gula Kort Borta'].mean()
                show_alert = (np.nan_to_num(h_c_avg) + np.nan_to_num(a_c_avg)) >= 3.4

                c_info, c_btn = st.columns([5, 1.2])
                with c_info:
                    st.markdown(f'''
                        <div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                            <div style="width:70px; font-size:0.8em; color:gray;">{r["datetime"].strftime("%H:%M")}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{r.get('response.teams.home.logo','')}" width="22"></div>
                            <div style="background:#f0f0f0; color:#333; padding:2px 12px; margin:0 15px; border-radius:4px; font-weight:bold;">VS</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{r.get('response.teams.away.logo','')}" width="22"> {a_name}</div>
                            <div style="width:30px; text-align:center;">{"🔔" if show_alert else ""}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_btn:
                    if st.button("Analys", key=f"h2h_{idx}", use_container_width=True):
                        st.session_state.view_h2h = r
                        st.rerun()

        with tab2:
            past_df = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            for idx, r in past_df.head(25).iterrows():
                c_info, c_btn = st.columns([5, 1.2])
                with c_info:
                    score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f'''
                        <div style="background:#f9f9f9; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                            <div style="width:70px; font-size:0.8em; color:gray;">{r["datetime"].strftime("%d %b")}</div>
                            <div style="flex:1; text-align:right;">{r['response.teams.home.name']}</div>
                            <div style="background:#222; color:white; padding:2px 12px; margin:0 15px; border-radius:4px; font-weight:bold;">{score}</div>
                            <div style="flex:1; text-align:left;">{r['response.teams.away.name']}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_btn:
                    if st.button("Statistik", key=f"res_{idx}", use_container_width=True):
                        st.session_state.view_match = r
                        st.rerun()
