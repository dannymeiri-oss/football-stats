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

    /* AI CARD PREDICTION BOXES */
    .bet-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 5px; font-size: 0.9rem; }
    .good-bet { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .bad-bet { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
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

def get_rolling_card_avg(team_name, full_df, n=10):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    cards = []
    for _, r in team_matches.iterrows():
        if r['response.teams.home.name'] == team_name:
            cards.append(r['Gula kort Hemma'])
        else:
            cards.append(r['Gula Kort Borta'])
    return sum(cards) / len(cards)

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
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mål snitt", round(h_hist['response.goals.home'].mean() + a_hist['response.goals.away'].mean(), 2) if not h_hist.empty else "N/A")
            m2.metric("xG snitt", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2) if not h_hist.empty else "N/A")
            m3.metric("Hörnor snitt", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1) if not h_hist.empty else "N/A")
            m4.metric("Gula snitt", round(h_hist['Gula kort Hemma'].mean() + a_hist['Gula Kort Borta'].mean(), 1) if not h_hist.empty else "N/A")
            
            ref_avg = 0.0
            if referee_name not in ["Domare: Okänd", "0", "Okänd", "nan", None]:
                ref_last_10 = df[(df['ref_clean'] == referee_name) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                if not ref_last_10.empty:
                    ref_avg = (ref_last_10['Gula kort Hemma'].sum() + ref_last_10['Gula Kort Borta'].sum()) / len(ref_last_10)
                    st.markdown(f"<div class='referee-box'>⚖️ Domare: {referee_name} | Snitt Gula Kort (Senaste 10): {ref_avg:.2f}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='referee-box'>⚖️ Domare: {referee_name} | Ingen historik hittad</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='referee-box'>⚖️ Domare: Okänd</div>", unsafe_allow_html=True)

            # --- AI CARD PREDICTIONS SEKTION ---
            st.markdown("<div class='section-header'>AI CARD PREDICTIONS</div>", unsafe_allow_html=True)
            h_card_avg = get_rolling_card_avg(h_team, df)
            a_card_avg = get_rolling_card_avg(a_team, df)
            
            # Prediktionslogik
            ref_weight = (ref_avg / 2) if ref_avg > 0 else 2.0
            h_pred = (h_card_avg + ref_weight) / 2
            a_pred = (a_card_avg + ref_weight) / 2
            
            stat_comparison_row("AI FÖRVÄNTADE KORT", h_pred, a_pred)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if h_pred >= 2.0:
                    st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {h_team} ÖVER 2.0 KORT</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='bet-box bad-bet'>❌ INGET BRA SPEL PÅ {h_team}</div>", unsafe_allow_html=True)
            with col_b2:
                if a_pred >= 2.0:
                    st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {a_team} ÖVER 2.0 KORT</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='bet-box bad-bet'>❌ INGET BRA SPEL PÅ {a_team}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='text-align:center; margin-top:20px; color:#333;'>SEASON AVERAGES COMPARISON</h3>", unsafe_allow_html=True)
            stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
            stat_comparison_row("EXPECTED GOALS (XG)", h_hist['xG Hemma'].mean(), a_hist['xG Borta'].mean())
            stat_comparison_row("BOLLINNEHAV", h_hist['Bollinnehav Hemma'].mean(), h_hist['Bollinnehav Borta'].mean(), is_pct=True, precision=0)
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), h_hist['Gula Kort Borta'].mean(), precision=1)
            stat_comparison_row("RÖDA KORT / MATCH", h_hist['Röda kort Hemma'].mean(), h_hist['Röda kort Borta'].mean(), precision=2)
            
            st.markdown("<br>### ⚔️ Senaste inbördes möten", unsafe_allow_html=True)
            h2h = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                     ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            h2h = h2h[h2h['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            if not h2h.empty:
                h2h_display = h2h.rename(columns={'response.teams.home.name': 'Hemmalag', 'response.teams.away.name': 'Bortalag', 'response.goals.home': 'Mål H', 'response.goals.away': 'Mål B'})
                st.dataframe(h2h_display[['Speltid', 'Hemmalag', 'Mål H', 'Mål B', 'Bortalag']], use_container_width=True, hide_index=True)

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
                h_avg = get_rolling_card_avg(h_name, df)
                a_avg = get_rolling_card_avg(a_name, df)
                
                h_color = "#28a745" if h_avg >= 2.00 else "black"
                a_color = "#28a745" if a_avg >= 2.00 else "black"
                
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""
                        <div class="match-row" style="flex-direction: column; align-items: stretch; padding: 10px 15px;">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
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
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 5px; padding-top: 4px; border-top: 1px solid #fcfcfc;">
                                <div style="width:130px;"></div>
                                <div style="flex:1; text-align:right; padding-right: 25px;">
                                    <span style="font-size: 0.75rem; color: {h_color}; font-weight:bold;"><span style="color: #e6b800;">🟨</span> {h_avg:.2f}</span>
                                </div>
                                <div style="width:70px;"></div>
                                <div style="flex:1; text-align:left; padding-left: 25px;">
                                    <span style="font-size: 0.75rem; color: {a_color}; font-weight:bold;"><span style="color: #e6b800;">🟨</span> {a_avg:.2f}</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    if st.button("H2H" if mode == "Nästa matcher" else "Analys", key=f"btn_m_{idx}", use_container_width=True):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            all_seasons = sorted(df['Säsong'].unique(), reverse=True)
            f1, f2 = st.columns(2)
            with f1: sel_team = st.selectbox("Välj lag:", all_teams, key="laganalys_team")
            with f2: sel_season = st.selectbox("Välj säsong:", ["Alla"] + all_seasons, key="laganalys_season")
            if sel_team:
                team_df = df if sel_season == "Alla" else df[df['Säsong'] == sel_season]
                h_df = team_df[(team_df['response.teams.home.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                a_df = team_df[(team_df['response.teams.away.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                tot_m = len(h_df) + len(a_df)
                if tot_m > 0:
                    st.markdown("<div class='total-header'>TOTAL PRESTATION (SNITT)</div>", unsafe_allow_html=True)
                    t1, t2, t3, t4, t5, t6 = st.columns(6)
                    t1.metric("Matcher", tot_m); t2.metric("Mål", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/tot_m, 2)); t3.metric("xG", round((h_df['xG Hemma'].sum() + a_df['xG Borta'].sum())/tot_m, 2)); t4.metric("Hörnor", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/tot_m, 1)); t5.metric("Gula Kort", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/tot_m, 1)); t6.metric("Bollinnehav", f"{int((h_df['Bollinnehav Hemma'].sum() + a_df['Bollinnehav Borta'].sum())/tot_m)}%")
                    col_h, col_a = st.columns(2)
                    with col_h:
                        st.markdown("<div class='section-header'>🏠 Hemma</div>", unsafe_allow_html=True)
                        if not h_df.empty:
                            c1, c2 = st.columns(2)
                            c1.metric("Mål", round(h_df['response.goals.home'].mean(), 2)); c2.metric("xG", round(h_df['xG Hemma'].mean(), 2))
                            c1.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%"); c2.metric("Hörnor", round(h_df['Hörnor Hemma'].mean(), 1))
                            c1.metric("Gula Kort", round(h_df['Gula kort Hemma'].mean(), 1)); c2.metric("Röda Kort", round(h_df['Röda kort Hemma'].mean(), 2))
                    with col_a:
                        st.markdown("<div class='section-header'>✈️ Borta</div>", unsafe_allow_html=True)
                        if not a_df.empty:
                            c1, c2 = st.columns(2)
                            c1.metric("Mål", round(a_df['response.goals.away'].mean(), 2)); c2.metric("xG", round(a_df['xG Borta'].mean(), 2))
                            c1.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%"); c2.metric("Hörnor", round(a_df['Hörnor Borta'].mean(), 1))
                            c1.metric("Gula Kort", round(a_df['Gula Kort Borta'].mean(), 1)); c2.metric("Röda Kort", round(a_df['Röda kort Borta'].mean(), 2))
                    st.divider(); st.subheader(f"📅 Senaste 10 matcher för {sel_team}")
                    last_10 = team_df[((team_df['response.teams.home.name'] == sel_team) | (team_df['response.teams.away.name'] == sel_team)) & (team_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                    if not last_10.empty:
                        for idx, r in last_10.iterrows():
                            h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                            l_name = r['response.league.name']
                            h_pos = get_team_pos(h_name, l_name, standings_df)
                            a_pos = get_team_pos(a_name, l_name, standings_df)
                            h_avg = get_rolling_card_avg(h_name, df)
                            a_avg = get_rolling_card_avg(a_name, df)
                            h_color = "#28a745" if h_avg >= 2.00 else "black"
                            a_color = "#28a745" if a_avg >= 2.00 else "black"
                            col_info, col_btn = st.columns([4.5, 1.5])
                            with col_info:
                                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                                st.markdown(f"""
                                    <div class="match-row" style="flex-direction: column; align-items: stretch; padding: 10px 15px;">
                                        <div style="display: flex; align-items: center; justify-content: space-between;">
                                            <div style="width:100px; font-size:0.75rem; color:gray;">{r['Speltid']}</div>
                                            <div style="flex:1; text-align:right; font-weight:bold; font-size: 0.95rem;">
                                                <span class="pos-tag">{h_pos}</span> {h_name} 
                                                <img src="{r['response.teams.home.logo']}" width="18">
                                            </div>
                                            <div style="background:#222; color:white; padding:2px 8px; margin:0 12px; border-radius:4px; min-width:45px; text-align:center; font-weight: bold;">{score}</div>
                                            <div style="flex:1; text-align:left; font-weight:bold; font-size: 0.95rem;">
                                                <img src="{r['response.teams.away.logo']}" width="18"> 
                                                {a_name} <span class="pos-tag">{a_pos}</span>
                                            </div>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            with col_btn:
                                if st.button("Analys", key=f"btn_la_{idx}", use_container_width=True):
                                    st.session_state.selected_match = r
                                    st.session_state.view_mode = "match_detail"
                                    st.rerun()

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["Domare: Okänd", "0", "Okänd", "nan"]])
            rf1, rf2 = st.columns(2)
            with rf1: sel_ref = st.selectbox("Välj domare:", ["Välj domare..."] + refs, key="domaranalys_ref")
            with rf2: sel_ref_season = st.selectbox("Välj säsong för domare:", ["Alla"] + all_seasons, key="domaranalys_season")
            if sel_ref != "Välj domare...":
                ref_df = df if sel_ref_season == "Alla" else df[df['Säsong'] == sel_ref_season]
                r_df = ref_df[ref_df['ref_clean'] == sel_ref]
                if not r_df.empty:
                    m_count = len(r_df); gula_tot = r_df['Gula kort Hemma'].sum() + r_df['Gula Kort Borta'].sum()
                    d1, d2 = st.columns(2)
                    d1.metric("Antal Matcher", m_count); d2.metric("Gula Kort (Snitt)", round(gula_tot / m_count, 2) if m_count > 0 else 0)
                    for idx_r, row_r in r_df.sort_values('datetime', ascending=False).iterrows():
                        st.markdown(f"<div class='match-row'>{row_r['Speltid']} | {row_r['response.teams.home.name']} {int(row_r['Gula kort Hemma'])}-{int(row_r['Gula Kort Borta'])} {row_r['response.teams.away.name']}</div>", unsafe_allow_html=True)

        with tab4:
            st.header("🏆 Ligatabell")
            if standings_df is not None:
                liga_col = standings_df.columns[0]
                available_leagues = sorted(standings_df[liga_col].dropna().unique().tolist())
                sel_league_stand = st.selectbox("Välj liga:", available_leagues, key="stand_sel")
                display_table = standings_df[standings_df[liga_col] == sel_league_stand].copy()
                st.dataframe(display_table.iloc[:, 1:], use_container_width=True, hide_index=True)

        with tab5:
            st.header("📊 Topplista")
            top_cat = st.radio("Välj kategori:", ["Lag", "Domare", "Heta Kortmatcher (Kommande)"], horizontal=True)
            if top_cat == "Lag":
                team_stats = []
                teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
                for t in teams:
                    t_avg = get_rolling_card_avg(t, df, n=10)
                    team_stats.append({'Lag': t, 'Snitt Kort': round(t_avg, 2)})
                st.dataframe(pd.DataFrame(team_stats).sort_values('Snitt Kort', ascending=False), use_container_width=True, hide_index=True)
            elif top_cat == "Domare":
                ref_stats = []
                for r in df['ref_clean'].unique():
                    if "Okänd" in r: continue
                    r_m = df[df['ref_clean'] == r]
                    if len(r_m) >= 5:
                        avg = (r_m['Gula kort Hemma'].sum() + r_m['Gula Kort Borta'].sum()) / len(r_m)
                        ref_stats.append({'Domare': r, 'Snitt Kort': round(avg, 2)})
                st.dataframe(pd.DataFrame(ref_stats).sort_values('Snitt Kort', ascending=False), use_container_width=True, hide_index=True)
            elif top_cat == "Heta Kortmatcher (Kommande)":
                upcoming = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime', ascending=True)
                results = []
                for _, row in upcoming.head(20).iterrows():
                    h_a = get_rolling_card_avg(row['response.teams.home.name'], df)
                    a_a = get_rolling_card_avg(row['response.teams.away.name'], df)
                    results.append({'Match': f"{row['response.teams.home.name']} - {row['response.teams.away.name']}", 'Kortstyrka': round(h_a+a_a, 2)})
                st.table(pd.DataFrame(results).sort_values('Kortstyrka', ascending=False))
