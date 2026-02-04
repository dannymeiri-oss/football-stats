import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# Din API-nyckel för API-Football (PRO) som du gav mig
API_KEY = "6343cd4636523af501b585a1b595ad26" 
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "1363673756" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. ODDS-MOTOR (API-FOOTBALL PRO) ---
@st.cache_data(ttl=600)
def fetch_api_football_odds(fixture_id):
    """Hämtar odds för 1X2, Hörnor och Kort från Unibet (Bookmaker ID 11)"""
    if not fixture_id: return None
    
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}&bookmaker=11"
    headers = {"x-apisports-key": API_KEY}
    
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        if not data['response']: return None
        
        # Vi hämtar marknader från den första tillgängliga bookmakern (Unibet)
        markets = data['response'][0]['bookmakers'][0]['markets']
        odds_dict = {}
        for m in markets:
            if m['name'] == "Match Winner": odds_dict['1X2'] = m['values']
            if m['name'] == "Both Teams Score": odds_dict['BTTS'] = m['values']
            if m['name'] == "Corners Over/Under": odds_dict['Corners'] = m['values']
            if m['name'] == "Cards Over/Under": odds_dict['Cards'] = m['values']
            if m['name'] == "Goals Over/Under": odds_dict['Totals'] = m['values']
        return odds_dict
    except:
        return None

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
    cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 'response.goals.home', 'response.goals.away']
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

    # --- H2H ANALYS (MED API-FOOTBALL ODDS) ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h1 style='text-align: center;'>H2H: {h_team} vs {a_team}</h1>", unsafe_allow_html=True)
        
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        if not h_stats.empty and not a_stats.empty:
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("Mål snitt", round(h_stats['response.goals.home'].mean() + a_stats['response.goals.away'].mean(), 2))
            tc2.metric("xG snitt", round(h_stats['xG Hemma'].mean() + a_stats['xG Borta'].mean(), 2))
            tc3.metric("Hörnor", round(h_stats['Hörnor Hemma'].mean() + a_stats['Hörnor Borta'].mean(), 1))
            tc4.metric("Gula", round(h_stats['Gula kort Hemma'].mean() + a_stats['Gula Kort Borta'].mean(), 1))
            
            st.divider()
            
            st.markdown("<h4 style='text-align: center;'>💸 Live Odds (Unibet via API-Football)</h4>", unsafe_allow_html=True)
            with st.spinner('Hämtar marknader...'):
                odds = fetch_api_football_odds(m.get('response.fixture.id'))
            
            if odds:
                o1, o2, o3 = st.columns(3)
                with o1:
                    if '1X2' in odds:
                        st.write("**1X2 Odds**")
                        for o in odds['1X2']: st.write(f"{o['value']}: **{o['odd']}**")
                with o2:
                    if 'Corners' in odds:
                        st.write("**Hörnor (Ö/U)**")
                        for o in odds['Corners']: 
                            if "9.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
                    if 'BTTS' in odds:
                        st.write("**Båda lagen gör mål**")
                        for o in odds['BTTS']: st.write(f"{o['value']}: **{o['odd']}**")
                with o3:
                    if 'Cards' in odds:
                        st.write("**Kort (Ö/U)**")
                        for o in odds['Cards']:
                            if "3.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
                    if 'Totals' in odds:
                        st.write("**Mål (Ö/U 2.5)**")
                        for o in odds['Totals']:
                            if "2.5" in o['value']: st.write(f"{o['value']}: **{o['odd']}**")
            else:
                st.info("Inga live-odds tillgängliga för denna match just nu.")

            st.divider()
            stat_comparison_row("Mål", round(h_stats['response.goals.home'].mean(), 2), round(a_stats['response.goals.away'].mean(), 2))
            stat_comparison_row("xG", round(h_stats['xG Hemma'].mean(), 2), round(a_stats['xG Borta'].mean(), 2))
            stat_comparison_row("Hörnor", round(h_stats['Hörnor Hemma'].mean(), 1), round(a_stats['Hörnor Borta'].mean(), 1))
            stat_comparison_row("Gula Kort", round(h_stats['Gula kort Hemma'].mean(), 1), round(a_stats['Gula Kort Borta'].mean(), 1))

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
                    if (pd.Series(h_c).fillna(0).iloc[0] + pd.Series(a_c).fillna(0).iloc[0]) >= 3.4: show_alert = True

                c_i, c_b = st.columns([5, 1.5])
                score_text = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Resultat" else "VS"
                
                with c_i:
                    st.markdown(f'''
                        <div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                            <div style="width:70px; font-size:0.8em; color:gray;">{r["datetime"].strftime("%d %b") if pd.notnull(r["datetime"]) else ""}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{h_logo}" width="22"></div>
                            <div style="background:#222; color:white; padding:2px 12px; margin:0 15px; border-radius:4px; font-weight:bold; min-width:65px; text-align:center;">{score_text}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{a_logo}" width="22"> {a_name}</div>
                            <div style="margin-left:10px; font-size:0.7em; color:blue; width:100px;">{r.get("response.league.name", "")}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_b:
                    btn_col, bell_col = st.columns([1, 0.3])
                    with btn_col:
                        if st.button("Analys" if mode=="Nästa matcher" else "Statistik", key=f"btn{idx}", use_container_width=True):
                            if mode=="Nästa matcher": st.session_state.view_h2h = r
                            else: st.session_state.view_match = r
                            st.rerun()
                    with bell_col:
                        if show_alert: st.markdown("<div style='font-size:1.6em; margin-top:2px;'>🔔</div>", unsafe_allow_html=True)

        with tab2:
            st.header("🏆 Ligatabell")
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True)

        with tab3:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                st.dataframe(df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)].head(10))

        with tab4:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                st.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
else:
    st.error("Kunde inte ladda data.")
