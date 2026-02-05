import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFECT LAYOUT) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; text-align: center; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    .sub-title { text-align: center; color: #666; margin-bottom: 25px; }
    
    /* MATCHCENTER */
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    
    /* H2H DESIGN */
    .centered-header { display: flex; justify-content: center; align-items: center; gap: 30px; margin-bottom: 20px; width: 100%; }
    .h2h-logo { width: 100px; }
    .stat-label-centered { color: #888; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; text-align: center; margin-top: 10px; }
    .stat-comparison { display: flex; justify-content: center; align-items: center; gap: 20px; font-size: 1.4rem; font-weight: bold; }
    
    /* SEKTIONER */
    .section-header { text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; margin-bottom: 15px; font-weight: bold; }
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

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    if 'Säsong' not in data.columns and 'datetime' in data.columns:
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
        data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
            
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    suffix = "%" if is_pct else ""
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{val1}{suffix}</div><div style='color:#eee;'>|</div><div style='flex:1; text-align:left;'>{val2}{suffix}</div></div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        st.markdown(f"""<div class='centered-header'><img src='{m['response.teams.home.logo']}' class='h2h-logo'><h1 style='margin:0;'>{h_team} vs {a_team}</h1><img src='{m['response.teams.away.logo']}' class='h2h-logo'></div>""", unsafe_allow_html=True)

        h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mål snitt", round(h_hist['response.goals.home'].mean() + a_hist['response.goals.away'].mean(), 2) if not h_hist.empty else 0)
        m2.metric("xG snitt", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2) if not h_hist.empty else 0)
        m3.metric("Hörnor snitt", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1) if not h_hist.empty else 0)
        m4.metric("Gula snitt", round(h_hist['Gula kort Hemma'].mean() + a_hist['Gula Kort Borta'].mean(), 1) if not h_hist.empty else 0)

        st.write("---")
        stat_comparison_row("MÅL/MATCH", round(h_hist['response.goals.home'].mean(), 2) if not h_hist.empty else 0, round(a_hist['response.goals.away'].mean(), 2) if not a_hist.empty else 0)
        stat_comparison_row("XG/MATCH", round(h_hist['xG Hemma'].mean(), 2) if not h_hist.empty else 0, round(a_hist['xG Borta'].mean(), 2) if not a_hist.empty else 0)
        stat_comparison_row("BOLLINNEHAV", int(h_hist['Bollinnehav Hemma'].mean()) if not h_hist.empty else 0, int(a_hist['Bollinnehav Borta'].mean()) if not a_hist.empty else 0, True)

        st.markdown("### ⚔️ Senaste inbördes möten")
        h2h = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                 ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
        h2h = h2h[h2h['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
        if not h2h.empty:
            st.dataframe(h2h[['datetime', 'response.teams.home.name', 'response.goals.home', 'response.goals.away', 'response.teams.away.name']], use_container_width=True, hide_index=True)

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            subset = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(30).iterrows():
                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""<div class="match-row">
                            <div style="width:130px; font-size:0.8em; color:gray;">{r['datetime'].strftime('%d %b %Y %H:%M')}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{r['response.teams.home.name']} <img src="{r['response.teams.home.logo']}" width="20"></div>
                            <div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{r['response.teams.away.logo']}" width="20"> {r['response.teams.away.name']}</div>
                        </div>""", unsafe_allow_html=True)
                with col_btn:
                    if st.button("H2H" if mode == "Nästa matcher" else "Analys", key=f"m{idx}", use_container_width=True):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            f1, f2 = st.columns(2)
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            all_seasons = sorted(df['Säsong'].unique(), reverse=True)
            with f1: sel_team = st.selectbox("Välj lag:", all_teams, key="team_analysis_sel")
            with f2: sel_season = st.selectbox("Välj säsong:", ["Alla"] + all_seasons, key="season_analysis_sel")
            
            if sel_team:
                team_df = df if sel_season == "Alla" else df[df['Säsong'] == sel_season]
                h_df = team_df[(team_df['response.teams.home.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                a_df = team_df[(team_df['response.teams.away.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                
                # Beräkna TOTALT (Kombinerat Hemma + Borta)
                tot_matches = len(h_df) + len(a_df)
                
                st.divider()
                col_h, col_t, col_a = st.columns(3)
                
                # --- HJÄLPFUNKTION FÖR ATT RENDERA KOLUMNER ---
                def render_team_stats(data_h, data_a, mode="total"):
                    if mode == "home":
                        df_view = data_h
                        g, xg, boll, horn, gul, rod, foul, pen, sm, stot, passp, radd, off = 'response.goals.home', 'xG Hemma', 'Bollinnehav Hemma', 'Hörnor Hemma', 'Gula kort Hemma', 'Röda kort Hemma', 'Fouls Hemma', 'Straffar Hemma', 'Skott på mål Hemma', 'Skott totalt Hemma', 'Passningssäkerhet Hemma', 'Räddningar Hemma', 'Offside Hemma'
                    elif mode == "away":
                        df_view = data_a
                        g, xg, boll, horn, gul, rod, foul, pen, sm, stot, passp, radd, off = 'response.goals.away', 'xG Borta', 'Bollinnehav Borta', 'Hörnor Borta', 'Gula Kort Borta', 'Röda kort Borta', 'Fouls Borta', 'Straffar Borta', 'Skott på mål Borta', 'Skott totalt Borta', 'Passningssäkerhet Borta', 'Räddningar Borta', 'Offside Borta'
                    else: # TOTAL
                        # Specialhantering för snittvärden på totalen
                        st.markdown("<div class='section-header'>TOTALT</div>", unsafe_allow_html=True)
                        if tot_matches > 0:
                            m_avg = (data_h['response.goals.home'].sum() + data_a['response.goals.away'].sum()) / tot_matches
                            xg_avg = (data_h['xG Hemma'].sum() + data_a['xG Borta'].sum()) / tot_matches
                            st.metric("Mål snitt", round(m_avg, 2))
                            st.metric("xG snitt", round(xg_avg, 2))
                            st.metric("Bollinnehav", f"{int((data_h['Bollinnehav Hemma'].sum() + data_a['Bollinnehav Borta'].sum()) / tot_matches)}%")
                            st.metric("Hörnor", round((data_h['Hörnor Hemma'].sum() + data_a['Hörnor Borta'].sum()) / tot_matches, 1))
                            st.metric("Gula Kort", round((data_h['Gula kort Hemma'].sum() + data_a['Gula Kort Borta'].sum()) / tot_matches, 1))
                            st.metric("Fouls", round((data_h['Fouls Hemma'].sum() + data_a['Fouls Borta'].sum()) / tot_matches, 1))
                            st.metric("Skott på mål", round((data_h['Skott på mål Hemma'].sum() + data_a['Skott på mål Borta'].sum()) / tot_matches, 1))
                            st.metric("Skott totalt", round((data_h['Skott totalt Hemma'].sum() + data_a['Skott totalt Borta'].sum()) / tot_matches, 1))
                            st.metric("Röda Kort", round((data_h['Röda kort Hemma'].sum() + data_a['Röda kort Borta'].sum()) / tot_matches, 2))
                            st.metric("Straffar (Tot)", int(data_h['Straffar Hemma'].sum() + data_a['Straffar Borta'].sum()))
                            st.metric("Passnings%", f"{int((data_h['Passningssäkerhet Hemma'].sum() + data_a['Passningssäkerhet Borta'].sum()) / tot_matches)}%")
                            st.metric("Räddningar", round((data_h['Räddningar Hemma'].sum() + data_a['Räddningar Borta'].sum()) / tot_matches, 1))
                            st.metric("Offside", round((data_h['Offside Hemma'].sum() + data_a['Offside Borta'].sum()) / tot_matches, 1))
                        return

                    if not df_view.empty:
                        st.markdown(f"<div class='section-header'>{'HEMMA' if mode=='home' else 'BORTA'}</div>", unsafe_allow_html=True)
                        st.metric("Mål", round(df_view[g].mean(), 2))
                        st.metric("xG", round(df_view[xg].mean(), 2))
                        st.metric("Bollinnehav", f"{int(df_view[boll].mean())}%")
                        st.metric("Hörnor", round(df_view[horn].mean(), 1))
                        st.metric("Gula Kort", round(df_view[gul].mean(), 1))
                        st.metric("Fouls", round(df_view[foul].mean(), 1))
                        st.metric("Skott på mål", round(df_view[sm].mean(), 1))
                        st.metric("Skott totalt", round(df_view[stot].mean(), 1))
                        st.metric("Röda Kort", round(df_view[rod].mean(), 2))
                        st.metric("Straffar (Tot)", int(df_view[pen].sum()))
                        st.metric("Passnings%", f"{int(df_view[passp].mean())}%")
                        st.metric("Räddningar", round(df_view[radd].mean(), 1))
                        st.metric("Offside", round(df_view[off].mean(), 1))

                with col_h: render_team_stats(h_df, a_df, "home")
                with col_t: render_team_stats(h_df, a_df, "total")
                with col_a: render_team_stats(h_df, a_df, "away")

        with tab3:
            st.header("⚖️ Domaranalys")
            f1, f2 = st.columns(2)
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            with f1: sel_ref = st.selectbox("Välj domare:", refs, key="ref_analysis_sel")
            with f2: sel_season_ref = st.selectbox("Välj säsong:", ["Alla"] + all_seasons, key="season_ref_analysis_sel")
            
            if sel_ref:
                ref_df = df if sel_season_ref == "Alla" else df[df['Säsong'] == sel_season_ref]
                r_df = ref_df[ref_df['ref_clean'] == sel_ref]
                if not r_df.empty:
                    c = st.columns(3)
                    c[0].metric("Matcher", len(r_df))
                    c[1].metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                    c[2].metric("Straffar", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))
                    st.dataframe(r_df[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta']], use_container_width=True, hide_index=True)

        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
