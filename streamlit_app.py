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
    
    /* NY CSS FÖR AI PREDICTIONS */
    .bet-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 5px; font-size: 0.9rem; }
    .good-bet { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .bad-bet { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .ai-text-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #2196F3; margin: 15px 0; font-style: italic; color: #333; font-size: 0.95rem; line-height: 1.6; }
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

def get_rolling_card_avg(team_name, full_df, n=20):
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

def get_rolling_corner_avg(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0
    corners = []
    for _, r in team_matches.iterrows():
        if r['response.teams.home.name'] == team_name:
            corners.append(r['Hörnor Hemma'])
        else:
            corners.append(r['Hörnor Borta'])
    return sum(corners) / len(corners)

def get_rolling_goals_stats(team_name, full_df, n=20):
    team_matches = full_df[((full_df['response.teams.home.name'] == team_name) | 
                            (full_df['response.teams.away.name'] == team_name)) & 
                           (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if team_matches.empty: return 0.0, 0.0
    scored = []
    conceded = []
    for _, r in team_matches.iterrows():
        if r['response.teams.home.name'] == team_name:
            scored.append(r['response.goals.home'])
            conceded.append(r['response.goals.away'])
        else:
            scored.append(r['response.goals.away'])
            conceded.append(r['response.goals.home'])
    return sum(scored)/len(scored), sum(conceded)/len(conceded)

def format_referee(name):
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None"]:
        return None
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
        'response.goals.home', 'response.goals.away'
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
            h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(20)
            a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(20)
            h_card_avg = get_rolling_card_avg(h_team, df, n=20)
            a_card_avg = get_rolling_card_avg(a_team, df, n=20)
            
            # Övre raden
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mål snitt (L20)", round(h_hist['response.goals.home'].mean() + a_hist['response.goals.away'].mean(), 2) if not h_hist.empty else "N/A")
            m2.metric("xG snitt (L20)", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2) if not h_hist.empty else "N/A")
            m3.metric("Hörnor snitt (L20)", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1) if not h_hist.empty else "N/A")
            m4.metric("Gula snitt (L20)", round(h_card_avg + a_card_avg, 1) if not h_hist.empty else "N/A")
            
            # Rad för Odds och Domarsnitt
            ref_avg_val = 0.0
            display_ref = "N/A"
            if referee_name:
                ref_last_10 = df[(df['ref_clean'] == referee_name) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                if not ref_last_10.empty:
                    ref_avg_val = (ref_last_10['Gula kort Hemma'].sum() + ref_last_10['Gula Kort Borta'].sum()) / len(ref_last_10)
                    display_ref = f"{ref_avg_val:.2f}"
            
            # Dummy odds logik för beräkning
            d_odd_h = 1.85
            d_odd_a = 2.10
            comb_odds = round(d_odd_h * d_odd_a, 2)
            dummy_odd_btts = 1.70

            o1, o2, o3 = st.columns(3)
            o1.metric("Komb-odds (Ö1.5 Kort)", f"{comb_odds}")
            o2.metric("BLGM Odds", f"{dummy_odd_btts}")
            o3.metric(f"Domare ({referee_name if referee_name else 'N/A'})", display_ref)

            # --- AI PREDICTIONS ---
            st.markdown("<div class='section-header'>🤖 DEEP STATS AI PREDICTION (L20)</div>", unsafe_allow_html=True)
            
            h2h_past = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                          ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            h2h_past = h2h_past[h2h_past['response.fixture.status.short'] == 'FT']
            
            # AI Beräkningar
            derby_boost = 0.8 if not h2h_past.empty and (h2h_past['Gula kort Hemma'] + h2h_past['Gula Kort Borta']).mean() > (h_card_avg + a_card_avg) else 0.0
            ref_calc = ref_avg_val if ref_avg_val > 0 else 4.0
            total_cards_pred = (h_card_avg + a_card_avg) * 0.6 + ref_calc * 0.4 + derby_boost
            h_card_pred = (h_card_avg * 0.6) + (ref_calc * 0.2) + (derby_boost / 2)
            a_card_pred = (a_card_avg * 0.6) + (ref_calc * 0.2) + (derby_boost / 2)

            h_corn_avg = get_rolling_corner_avg(h_team, df, n=20)
            a_corn_avg = get_rolling_corner_avg(a_team, df, n=20)
            
            h_scored, h_conceded = get_rolling_goals_stats(h_team, df, n=20)
            a_scored, a_conceded = get_rolling_goals_stats(a_team, df, n=20)
            btts_score = (h_scored + a_conceded + a_scored + h_conceded) / 2
            btts_pred_text = "JA (Troligt)" if btts_score > 2.0 else "NEJ"
            btts_color = "green" if btts_score > 2.0 else "red"

            # Visualisering AI
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{h_team} (xCards)", f"{h_card_pred:.2f}")
            c2.metric("TOTALT (xCards)", f"{total_cards_pred:.2f}")
            c3.metric(f"{a_team} (xCards)", f"{a_card_pred:.2f}")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if h_card_pred >= 2.0: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {h_team} ÖVER 1.5 KORT</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {h_team} UNDER 2.0 KORT</div>", unsafe_allow_html=True)
            with col_b2:
                if a_card_pred >= 2.0: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {a_team} ÖVER 1.5 KORT</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {a_team} UNDER 2.0 KORT</div>", unsafe_allow_html=True)

            stat_comparison_row("AI HÖRNOR PREDIKTION", h_corn_avg, a_corn_avg)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if h_corn_avg >= 5.5: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {h_team} ÖVER 5.5 HÖRNOR</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {h_team} UNDER 5.5 HÖRNOR</div>", unsafe_allow_html=True)
            with col_c2:
                if a_corn_avg >= 5.5: st.markdown(f"<div class='bet-box good-bet'>✅ BRA SPEL: {a_team} ÖVER 5.5 HÖRNOR</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='bet-box bad-bet'>❌ SKIPPA: {a_team} UNDER 5.5 HÖRNOR</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='text-align:center; font-weight:bold; margin-top: 15px;'>BÅDA LAGEN GÖR MÅL (BLGM)? <span style='color:{btts_color}; font-size:1.2rem;'>{btts_pred_text}</span></div>", unsafe_allow_html=True)

            # Slutsats stycken
            p1 = f"**🟨 Kort & Intensitet:** {h_team} ({h_card_avg:.1f}) och {a_team} ({a_card_avg:.1f}) kortsnitt vägs mot domarens snitt på {display_ref}. "
            if derby_boost > 0: p1 += "Då inbördes historik är hetare än snittet har en Derby-boost lagts till. "
            p2 = f"**🚩 Hörnor:** Baserat på 20 matcher förväntas totalt {h_corn_avg+a_corn_avg:.1f} hörnor. "
            p3 = f"**⚽ Mål:** BLGM-index på {btts_score:.2f} indikerar en {'målrik' if btts_score > 2.5 else 'tät'} matchbild."
            
            st.markdown(f"<div class='ai-text-box'><b>🎙️ AI-Analys & Logik:</b><br><br>{p1}<br><br>{p2}<br><br>{p3}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='text-align:center; margin-top:20px; color:#333;'>SEASON AVERAGES COMPARISON</h3>", unsafe_allow_html=True)
            stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
            stat_comparison_row("EXPECTED GOALS (XG)", h_hist['xG Hemma'].mean(), h_hist['xG Borta'].mean())
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), h_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), h_hist['Gula Kort Borta'].mean(), precision=1)
            
            st.markdown("<br>### ⚔️ Senaste inbördes möten", unsafe_allow_html=True)
            if not h2h_past.empty:
                st.dataframe(h2h_past[['Speltid', 'response.teams.home.name', 'response.goals.home', 'response.goals.away', 'response.teams.away.name']].rename(columns={'response.teams.home.name': 'Hemma', 'response.teams.away.name': 'Borta'}), use_container_width=True, hide_index=True)

        elif st.session_state.view_mode == "match_detail":
            st.markdown("<h2 style='text-align:center; color:#ddd; margin-bottom:20px;'>MATCH STATISTICS</h2>", unsafe_allow_html=True)
            stats_to_show = [("Ball Possession", 'Bollinnehav Hemma', 'Bollinnehav Borta', True), ("Shot on Target", 'Skott på mål Hemma', 'Skott på mål Borta', False), ("Expected Goals (xG)", 'xG Hemma', 'xG Borta', False), ("Pass Accuracy", 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', True), ("Corner Kicks", 'Hörnor Hemma', 'Hörnor Borta', False), ("Fouls", 'Fouls Hemma', 'Fouls Borta', False), ("Yellow Cards", 'Gula kort Hemma', 'Gula Kort Borta', False)]
            for label, h_col, a_col, is_pct in stats_to_show:
                h_val, a_val = m[h_col], m[a_col]
                suffix = "%" if is_pct else ""
                st.markdown(f'<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;"><div style="width: 80px; text-align: right; font-size: 1.4rem; font-weight: bold; color: black; padding-right: 15px;">{h_val}{suffix}</div><div style="width: 220px; background: #e63946; color: white; text-align: center; padding: 6px; font-weight: bold; font-size: 0.85rem; border-radius: 2px; text-transform: uppercase;">{label}</div><div style="width: 80px; text-align: left; font-size: 1.4rem; font-weight: bold; color: black; padding-left: 15px;">{a_val}{suffix}</div></div>', unsafe_allow_html=True)
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter (72h)", "🛡️ Laganalys", "⚖️ Domare", "🏆 Tabell"])
        with tab1:
            mode = st.radio("Visa:", ["Kommande (3 dygn)", "Resultat"], horizontal=True)
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if mode == "Kommande (3 dygn)":
                limit_date = now + timedelta(days=3)
                subset = df[(df['response.fixture.status.short'] == 'NS') & (df['datetime'] >= now) & (df['datetime'] <= limit_date)]
                st.info(f"Visar matcher mellan {now.strftime('%d %b')} och {limit_date.strftime('%d %b')}")
            else:
                subset = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False).head(30)
            
            for idx, r in subset.sort_values('datetime', ascending=True).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if r['response.fixture.status.short'] == 'NS' else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""
                        <div class="match-row">
                            <div style="width:100px; font-size:0.8em; color:gray;">{r['datetime'].strftime('%H:%M')} | {r['Speltid']}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{r['response.teams.home.logo']}" width="20"></div>
                            <div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px;">{score}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{r['response.teams.away.logo']}" width="20"> {a_name}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                    if st.button("Analys", key=f"btn_m_{idx}", use_container_width=True):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail" if r['response.fixture.status.short'] == 'NS' else "match_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                st.metric("Snitt Gula Kort (L20)", round(get_rolling_card_avg(sel_team, df), 2))
                with st.expander("📂 Djupanalys (Alla Datapunkter)", expanded=False):
                    team_df = df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)]
                    st.dataframe(team_df.sort_values('datetime', ascending=False), use_container_width=True)

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref].sort_values('datetime', ascending=False)
                st.metric("Snitt Gula Kort", round((r_df['Gula kort Hemma'].sum() + r_df['Gula Kort Borta'].sum())/len(r_df), 2))
                st.dataframe(r_df, use_container_width=True)

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None:
                st.dataframe(standings_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
