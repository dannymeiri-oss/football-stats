import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFEKT LAYOUT - RÖR EJ) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; text-align: center; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    
    /* MATCHCENTER CSS */
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    
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
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1363673756"

# --- 2. DATAHANTERING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

def format_referee(name):
    """ Formaterar domarnamn till 'F. Efternamn' och tar bort land. """
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None"]:
        return "Domare: Okänd"
    
    # Ta bort allt efter kommatecken (landsinfo)
    name = str(name).split(',')[0].strip()
    
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    else:
        data['datetime'] = pd.Timestamp.now()
    if 'Säsong' not in data.columns:
        data['Säsong'] = data['datetime'].dt.year.astype(str)

    # Vi behåller din original-lista men lägger till alla dina 32 datapunkter här
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
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
        else:
            data[col] = 0.0
    
    # APPLICERA NY DOMAR-FORMATERING HÄR
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    
    data['Speltid'] = data['datetime'].dt.strftime('%d %b %Y')
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, val1, val2, is_pct=False, precision=2):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    suffix = "%" if is_pct else ""
    v1 = "N/A" if pd.isna(val1) else (f"{val1:.{precision}f}" if precision > 0 else f"{int(val1)}")
    v2 = "N/A" if pd.isna(val2) else (f"{val2:.{precision}f}" if precision > 0 else f"{int(val2)}")
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{v1}{suffix}</div><div style='color:#ccc; margin:0 10px;'>|</div><div style='flex:1; text-align:left;'>{v2}{suffix}</div></div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        referee_name = m['ref_clean']
        
        st.markdown(f"""
            <div style="background-color: #0e1117; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid #333;">
                <div style="color: #ffcc00; font-weight: bold; letter-spacing: 2px; font-size: 1.2rem;">{"FULL TIME" if m['response.fixture.status.short'] == 'FT' else "UPCOMING"}</div>
                <div style="display: flex; justify-content: center; align-items: center; gap: 30px; margin-top: 15px;">
                    <div style="flex: 1; text-align: right;">
                        <img src="{m['response.teams.home.logo']}" width="60"><br>
                        <span style="font-size: 1.1rem; font-weight: bold; color: white;">{h_team}</span>
                    </div>
                    <div style="display: flex; gap: 5px; align-items: center;">
                        <div style="background: #e63946; color: white; font-size: 2.5rem; padding: 5px 20px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.home']) if m['response.fixture.status.short'] == 'FT' else 0}</div>
                        <div style="background: #e63946; color: white; font-size: 1.2rem; padding: 15px 10px; border-radius: 5px; font-weight: bold;">{"90:00" if m['response.fixture.status.short'] == 'FT' else "VS"}</div>
                        <div style="background: #e63946; color: white; font-size: 2.5rem; padding: 5px 20px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.away']) if m['response.fixture.status.short'] == 'FT' else 0}</div>
                    </div>
                    <div style="flex: 1; text-align: left;">
                        <img src="{m['response.teams.away.logo']}" width="60"><br>
                        <span style="font-size: 1.1rem; font-weight: bold; color: white;">{a_team}</span>
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
            
            # --- DOMARE INFO ---
            if referee_name not in ["Domare: Okänd", "0", "Okänd", "nan", None]:
                ref_last_10 = df[(df['ref_clean'] == referee_name) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
                if not ref_last_10.empty:
                    ref_avg = (ref_last_10['Gula kort Hemma'].sum() + ref_last_10['Gula Kort Borta'].sum()) / len(ref_last_10)
                    st.markdown(f"<div class='referee-box'>⚖️ Domare: {referee_name} | Snitt Gula Kort (Senaste 10): {ref_avg:.2f}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='referee-box'>⚖️ Domare: {referee_name} | Ingen historik hittad</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='referee-box'>⚖️ Domare: Okänd</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='text-align:center; margin-top:20px; color:#333;'>SEASON AVERAGES COMPARISON</h3>", unsafe_allow_html=True)
            stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
            stat_comparison_row("EXPECTED GOALS (XG)", h_hist['xG Hemma'].mean(), a_hist['xG Borta'].mean())
            stat_comparison_row("BOLLINNEHAV", h_hist['Bollinnehav Hemma'].mean(), a_hist['Bollinnehav Borta'].mean(), is_pct=True, precision=0)
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)
            stat_comparison_row("RÖDA KORT / MATCH", h_hist['Röda kort Hemma'].mean(), a_hist['Röda kort Borta'].mean(), precision=2)
            
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
            subset = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(30).iterrows():
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""<div class="match-row"><div style="width:130px; font-size:0.8em; color:gray;">{r['Speltid']}</div><div style="flex:1; text-align:right; font-weight:bold;">{r['response.teams.home.name']} <img src="{r['response.teams.home.logo']}" width="20"></div><div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div><div style="flex:1; text-align:left; font-weight:bold;"><img src="{r['response.teams.away.logo']}" width="20"> {r['response.teams.away.name']}</div></div>""", unsafe_allow_html=True)
                with col_btn:
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
                        l10_display = last_10.rename(columns={'response.teams.home.name': 'Hemmalag', 'response.teams.away.name': 'Bortalag', 'response.goals.home': 'Mål H', 'response.goals.away': 'Mål B'})
                        st.dataframe(l10_display[['Speltid', 'Hemmalag', 'Mål H', 'Mål B', 'Bortalag']], use_container_width=True, hide_index=True)

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
                    st.markdown(f"<div class='section-header'>Statistik för {sel_ref}</div>", unsafe_allow_html=True)
                    m_count = len(r_df); gula_tot = r_df['Gula kort Hemma'].sum() + r_df['Gula Kort Borta'].sum()
                    d1, d2 = st.columns(2)
                    d1.metric("Antal Matcher", m_count); d2.metric("Gula Kort (Snitt)", round(gula_tot / m_count, 2) if m_count > 0 else 0)
                    r_df_sorted = r_df.sort_values('datetime', ascending=False)
                    st.dataframe(r_df_sorted[['Speltid', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta']], use_container_width=True, hide_index=True)

        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)

        with tab5:
            st.header("📊 Topplista")
            top_cat = st.radio("Välj kategori:", ["Lag", "Domare", "Heta Kortmatcher (Kommande)"], horizontal=True)
            
            c1, c2 = st.columns(2)
            with c1: num_matches = st.slider("Antal senaste matcher (Kriterium):", 1, 20, 5)
            with c2: 
                all_leagues = ["Alla"] + sorted(df['response.league.name'].unique().tolist()) if 'response.league.name' in df.columns else ["Alla"]
                sel_league = st.selectbox("Välj liga:", all_leagues, key="top_league_filter")

            filtered_df = df[df['response.fixture.status.short'] == 'FT']
            if sel_league != "Alla":
                filtered_df = filtered_df[filtered_df['response.league.name'] == sel_league]

            if top_cat == "Lag":
                st.info(f"Visar lag med minst **{num_matches}** spelade matcher.")
                team_stats = []
                teams = sorted(pd.concat([filtered_df['response.teams.home.name'], filtered_df['response.teams.away.name']]).unique())
                for t in teams:
                    t_matches = filtered_df[(filtered_df['response.teams.home.name'] == t) | (filtered_df['response.teams.away.name'] == t)].sort_values('datetime', ascending=False)
                    if len(t_matches) >= num_matches:
                        recent = t_matches.head(num_matches)
                        cards = [row['Gula kort Hemma'] if row['response.teams.home.name'] == t else row['Gula Kort Borta'] for _, row in recent.iterrows()]
                        team_stats.append({'Lag': t, 'Snitt Kort': round(sum(cards)/len(cards), 2), 'Matcher': len(cards)})
                if team_stats:
                    st.dataframe(pd.DataFrame(team_stats).sort_values('Snitt Kort', ascending=False), use_container_width=True, hide_index=True)

            elif top_cat == "Domare":
                st.info(f"Visar domare med minst **{num_matches}** dömda matcher.")
                ref_stats = []
                for r in filtered_df['ref_clean'].unique():
                    if r in ["Domare: Okänd", "0", "Okänd", "nan"]: continue
                    r_matches = filtered_df[filtered_df['ref_clean'] == r].sort_values('datetime', ascending=False)
                    if len(r_matches) >= num_matches:
                        recent = r_matches.head(num_matches)
                        avg = (recent['Gula kort Hemma'].sum() + recent['Gula Kort Borta'].sum()) / len(recent)
                        ref_stats.append({'Domare': r, 'Snitt Kort': round(avg, 2), 'Matcher': len(recent)})
                if ref_stats:
                    st.dataframe(pd.DataFrame(ref_stats).sort_values('Snitt Kort', ascending=False), use_container_width=True, hide_index=True)

            else:
                st.info(f"Analyserar kommande matcher baserat på lagens snitt (sista {num_matches} matcherna).")
                upcoming = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime', ascending=True).head(30)
                if sel_league != "Alla":
                    upcoming = upcoming[upcoming['response.league.name'] == sel_league]
                
                analysis_results = []
                for _, row in upcoming.iterrows():
                    h_team, a_team = row['response.teams.home.name'], row['response.teams.away.name']
                    ref = row['ref_clean']
                    
                    h_matches = filtered_df[(filtered_df['response.teams.home.name'] == h_team) | (filtered_df['response.teams.away.name'] == h_team)].sort_values('datetime', ascending=False).head(num_matches)
                    h_avg = sum([r['Gula kort Hemma'] if r['response.teams.home.name'] == h_team else r['Gula Kort Borta'] for _, r in h_matches.iterrows()]) / len(h_matches) if not h_matches.empty else 0
                    
                    a_matches = filtered_df[(filtered_df['response.teams.home.name'] == a_team) | (filtered_df['response.teams.away.name'] == a_team)].sort_values('datetime', ascending=False).head(num_matches)
                    a_avg = sum([r['Gula kort Hemma'] if r['response.teams.home.name'] == a_team else r['Gula Kort Borta'] for _, r in a_matches.iterrows()]) / len(a_matches) if not a_matches.empty else 0
                    
                    ref_avg_val = "N/A"
                    if ref not in ["Domare: Okänd", "0", "Okänd", "nan"]:
                        r_matches = filtered_df[filtered_df['ref_clean'] == ref].sort_values('datetime', ascending=False).head(num_matches)
                        if not r_matches.empty:
                            ref_avg_val = round((r_matches['Gula kort Hemma'].sum() + r_matches['Gula Kort Borta'].sum()) / len(r_matches), 2)
                    
                    total_index = round(h_avg + a_avg, 2)
                    analysis_results.append({
                        'Match': f"{h_team} vs {a_team}",
                        'Hemma snitt': round(h_avg, 2),
                        'Borta snitt': round(a_avg, 2),
                        'Kombinerat (Lagen)': total_index,
                        'Domare (Snitt)': ref_avg_val,
                        'Liga': row['response.league.name']
                    })
                
                if analysis_results:
                    analysis_df = pd.DataFrame(analysis_results).sort_values('Kombinerat (Lagen)', ascending=False)
                    st.dataframe(analysis_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
