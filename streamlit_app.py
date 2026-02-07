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
    .total-header { text-align: center; padding: 5px; color: #444; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #eee; }
    
    /* DOMARE INFO I H2H */
    .referee-box { text-align: center; background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 20px; font-weight: bold; }
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

def get_team_pos(team_name, league_name, standings):
    if standings is None or team_name is None: return ""
    try:
        league_col = standings.columns[0]
        pos_col = standings.columns[1]
        team_col = standings.columns[2]
        row = standings[(standings[league_col].astype(str) == str(league_name)) & 
                        (standings[team_col].astype(str) == str(team_name))]
        if not row.empty:
            val = row[pos_col].values[0]
            return f"#{int(float(val))}"
    except: pass
    return ""

def format_referee(name):
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None"]:
        return "Domare: Okänd"
    name = str(name).split(',')[0].strip()
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce').dt.tz_localize(None)
    else:
        data['datetime'] = pd.Timestamp.now().replace(tzinfo=None)
    
    if 'Säsong' not in data.columns:
        data['Säsong'] = data['datetime'].dt.year.astype(str)

    needed_cols = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'Fouls Hemma', 'Fouls Borta', 'Straffar Hemma', 'Straffar Borta',
        'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
        'Skott totalt Hemma', 'Skott totalt Borta', 'Röda kort Hemma', 'Röda kort Borta',
        'Räddningar Hemma', 'Räddningar Borta', 'Offside Hemma', 'Offside Borta',
        'response.goals.home', 'response.goals.away',
        'Skott utanför Hemma', 'Skott utanför Borta', 'Blockerade skott Hemma', 'Blockerade skott Borta',
        'Skott i straffområdet Hemma', 'Skott i straffområdet Borta', 'Skott utanför straffområdet Hemma', 'Skott utanför straffområdet Borta',
        'Passningar totalt Hemma', 'Passningar totalt Borta'
    ]
    for col in needed_cols:
        if col not in data.columns: data[col] = 0.0
        else:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
    
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    data['Speltid'] = data['datetime'].dt.strftime('%d %b %Y')
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, x1, x2, is_pct=False, precision=2):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    suffix = "%" if is_pct else ""
    v1 = "N/A" if pd.isna(x1) else (f"{x1:.{precision}f}" if precision > 0 else f"{int(x1)}")
    v2 = "N/A" if pd.isna(x2) else (f"{x2:.{precision}f}" if precision > 0 else f"{int(x2)}")
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{v1}{suffix}</div><div style='color:#ccc; margin:0 10px;'>|</div><div style='flex:1; text-align:left;'>{v2}{suffix}</div></div>", unsafe_allow_html=True)

def render_match_row_html(r, standings_df):
    """ Hjälpfunktion för att rendera en match-rad i 'Matchcenter-stil' """
    h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
    l_name = r['response.league.name']
    h_pos = get_team_pos(h_name, l_name, standings_df)
    a_pos = get_team_pos(a_name, l_name, standings_df)
    score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
    
    return f"""
        <div class="match-row">
            <div style="width:100px; font-size:0.75em; color:gray;">{r['Speltid']}</div>
            <div style="flex:1; text-align:right; font-weight:bold; font-size:0.9em;">
                <span class="pos-tag">{h_pos}</span> {h_name} 
            </div>
            <div style="background:#222; color:white; padding:1px 8px; margin:0 8px; border-radius:4px; min-width:40px; text-align:center; font-size:0.85em;">{score}</div>
            <div style="flex:1; text-align:left; font-weight:bold; font-size:0.9em;">
                {a_name} <span class="pos-tag">{a_pos}</span>
            </div>
        </div>
    """

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        l_name = m['response.league.name']
        referee_name = m['ref_clean']
        h_pos = get_team_pos(h_team, l_name, standings_df)
        a_pos = get_team_pos(a_team, l_name, standings_df)

        st.markdown(f"""
            <div style="background-color: #0e1117; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid #333;">
                <div style="color: #ffcc00; font-weight: bold; letter-spacing: 2px; font-size: 1.2rem;">{"FULL TIME" if m['response.fixture.status.short'] == 'FT' else "UPCOMING"}</div>
                <div style="display: flex; justify-content: center; align-items: center; gap: 30px; margin-top: 15px;">
                    <div style="flex: 1; text-align: right;">
                        <img src="{m['response.teams.home.logo']}" width="60"><br>
                        <span style="font-size: 1.1rem; font-weight: bold; color: white;">{h_team} <span style="color:#ffcc00;">{h_pos}</span></span>
                    </div>
                    <div style="display: flex; gap: 5px; align-items: center;">
                        <div style="background: #e63946; color: white; font-size: 2.5rem; padding: 5px 20px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.home']) if m['response.fixture.status.short'] == 'FT' else 0}</div>
                        <div style="background: #e63946; color: white; font-size: 1.2rem; padding: 15px 10px; border-radius: 5px; font-weight: bold;">{"90:00" if m['response.fixture.status.short'] == 'FT' else "VS"}</div>
                        <div style="background: #e63946; color: white; font-size: 2.5rem; padding: 5px 20px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.away']) if m['response.fixture.status.short'] == 'FT' else 0}</div>
                    </div>
                    <div style="flex: 1; text-align: left;">
                        <img src="{m['response.teams.away.logo']}" width="60"><br>
                        <span style="font-size: 1.1rem; font-weight: bold; color: white;"><span style="color:#ffcc00;">{a_pos}</span> {a_team}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.view_mode == "h2h_detail":
            h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
            a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
            
            # --- DOMARE (ÖVERST ENLIGT INSTRUKTION) ---
            if referee_name not in ["Domare: Okänd", "0", "Okänd", "nan", None]:
                ref_last_10 = df[(df['ref_clean'] == referee_name) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                ref_avg = (ref_last_10['Gula kort Hemma'].sum() + ref_last_10['Gula Kort Borta'].sum()) / len(ref_last_10) if not ref_last_10.empty else 0
                st.markdown(f"<div class='referee-box'>⚖️ Domare: {referee_name} | Snitt Gula Kort (Senaste 10): {ref_avg:.2f}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='referee-box'>⚖️ Domare: Okänd</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='text-align:center; margin-top:20px; color:#333;'>SEASON AVERAGES COMPARISON</h3>", unsafe_allow_html=True)
            stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
            stat_comparison_row("EXPECTED GOALS (XG)", h_hist['xG Hemma'].mean(), a_hist['xG Borta'].mean())
            stat_comparison_row("BOLLINNEHAV", h_hist['Bollinnehav Hemma'].mean(), a_hist['Bollinnehav Borta'].mean(), is_pct=True, precision=0)
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)
            
            st.markdown("---")
            
            # --- SENASTE 10 MATCHER (SAMMA DESIGN SOM MATCHCENTER) ---
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<div class='total-header'>SENASTE 10: {h_team}</div>", unsafe_allow_html=True)
                h_l10 = df[((df['response.teams.home.name'] == h_team) | (df['response.teams.away.name'] == h_team)) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                for _, r in h_l10.iterrows():
                    st.markdown(render_match_row_html(r, standings_df), unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"<div class='total-header'>SENASTE 10: {a_team}</div>", unsafe_allow_html=True)
                a_l10 = df[((df['response.teams.home.name'] == a_team) | (df['response.teams.away.name'] == a_team)) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                for _, r in a_l10.iterrows():
                    st.markdown(render_match_row_html(r, standings_df), unsafe_allow_html=True)

            st.markdown("<br>### ⚔️ Senaste inbördes möten", unsafe_allow_html=True)
            h2h = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                     ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            h2h = h2h[h2h['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            for _, r in h2h.iterrows():
                st.markdown(render_match_row_html(r, standings_df), unsafe_allow_html=True)

        elif st.session_state.view_mode == "match_detail":
            st.markdown("<h2 style='text-align:center; color:#ddd; margin-bottom:20px;'>MATCH STATISTICS</h2>", unsafe_allow_html=True)
            stats_to_show = [("Ball Possession", 'Bollinnehav Hemma', 'Bollinnehav Borta', True), ("Shot on Target", 'Skott på mål Hemma', 'Skott på mål Borta', False), ("Expected Goals (xG)", 'xG Hemma', 'xG Borta', False), ("Pass Accuracy", 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', True), ("Corner Kicks", 'Hörnor Hemma', 'Hörnor Borta', False), ("Fouls", 'Fouls Hemma', 'Fouls Borta', False), ("Yellow Cards", 'Gula kort Hemma', 'Gula Kort Borta', False)]
            for label, h_col, a_col, is_pct in stats_to_show:
                h_val, a_val = m[h_col], m[a_col]
                suffix = "%" if is_pct else ""
                st.markdown(f'<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;"><div style="width: 80px; text-align: right; font-size: 1.4rem; font-weight: bold; color: black; padding-right: 15px;">{h_val}{suffix}</div><div style="width: 220px; background: #e63946; color: white; text-align: center; padding: 6px; font-weight: bold; font-size: 0.85rem; border-radius: 2px; text-transform: uppercase;">{label}</div><div style="width: 80px; text-align: left; font-size: 1.4rem; font-weight: bold; color: black; padding-left: 15px;">{a_val}{suffix}</div></div>', unsafe_allow_html=True)

    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell", "📊 Topplista"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True, key="mc_mode")
            if mode == "Nästa matcher":
                now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now + timedelta(days=7)
                subset = df[(df['response.fixture.status.short'] == 'NS') & (df['datetime'] >= now) & (df['datetime'] <= end_date)]
            else:
                subset = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False).head(30)
            
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                l_name = r['response.league.name']
                h_pos = get_team_pos(h_name, l_name, standings_df)
                a_pos = get_team_pos(a_name, l_name, standings_df)
                
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""
                        <div class="match-row">
                            <div style="width:130px; font-size:0.8em; color:gray;">{r['Speltid']}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">
                                <span class="pos-tag">{h_pos}</span> {h_name} 
                                <img src="{r['response.teams.home.logo']}" width="20">
                            </div>
                            <div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;">
                                <img src="{r['response.teams.away.logo']}" width="20"> 
                                {a_name} <span class="pos-tag">{a_pos}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("H2H" if mode == "Nästa matcher" else "Analys", key=f"btn_m_{idx}", use_container_width=True):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            # Behåll din befintliga kod för tab2 här...
            # (Jag har inte ändrat något i tab2, tab3, tab4, tab5 för att inte påverka din data)

else:
    st.error("Kunde inte ladda data.")
