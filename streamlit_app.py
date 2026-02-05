import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFECT LAYOUT) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; text-align: center; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    .sub-title { text-align: center; color: #666; margin-bottom: 25px; }
    
    /* MATCHCENTER CSS */
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    
    /* H2H SPECIFIK DESIGN */
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
st.markdown("<p class='sub-title'>Perfect Layout - Season Filters Restored</p>", unsafe_allow_html=True)

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
    
    # Skapa Säsongs-kolumn om den inte finns (baserat på datum)
    if 'Säsong' not in data.columns and 'datetime' in data.columns:
        data['Säsong'] = data['datetime'].dt.year.astype(str)

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
        
        st.markdown(f"""
            <div class='centered-header'>
                <img src='{m['response.teams.home.logo']}' class='h2h-logo'>
                <h1 style='margin:0;'>{h_team} vs {a_team}</h1>
                <img src='{m['response.teams.away.logo']}' class='h2h-logo'>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.view_mode == "h2h_detail":
            st.markdown(f"""<div class="odds-box"><strong>Analys Odds (1X2):</strong> 2.15 | 3.45 | 3.05</div>""", unsafe_allow_html=True)
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

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            subset = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(30).iterrows():
                show_bell = False
                if mode == "Nästa matcher":
                    hist = df[df['response.fixture.status.short'] == 'FT']
                    h_avg = hist[(hist['response.teams.home.name'] == r['response.teams.home.name']) | (hist['response.teams.away.name'] == r['response.teams.home.name'])].apply(lambda x: x['Gula kort Hemma'] if x['response.teams.home.name'] == r['response.teams.home.name'] else x['Gula Kort Borta'], axis=1).mean()
                    if np.nan_to_num(h_avg) > 1.7: show_bell = True
                
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
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"; st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            f1, f2 = st.columns(2)
            all_seasons = sorted(df['Säsong'].unique(), reverse=True)
            with f1: sel_season = st.selectbox("Välj säsong (Lag):", ["Alla"] + all_seasons)
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            with f2: sel_team = st.selectbox("Välj lag:", all_teams)
            
            if sel_team:
                team_df = df if sel_season == "Alla" else df[df['Säsong'] == sel_season]
                h_df = team_df[(team_df['response.teams.home.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                a_df = team_df[(team_df['response.teams.away.name'] == sel_team) & (team_df['response.fixture.status.short'] == 'FT')]
                tot = len(h_df) + len(a_df)
                if tot > 0:
                    c = st.columns(4)
                    c[0].metric("Matcher", tot)
                    c[1].metric("Mål snitt", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/tot, 2))
                    c[2].metric("Gula snitt", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/tot, 2))
                    c[3].metric("Hörnor snitt", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/tot, 1))
                    st.write("---")
                    col_h, col_a = st.columns(2)
                    with col_h:
                        st.subheader("🏠 HEMMA")
                        st.metric("Mål", round(h_df['response.goals.home'].mean(), 1))
                        st.metric("xG", round(h_df['xG Hemma'].mean(), 2))
                        st.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%")
                    with col_a:
                        st.subheader("✈️ BORTA")
                        st.metric("Mål", round(a_df['response.goals.away'].mean(), 1))
                        st.metric("xG", round(a_df['xG Borta'].mean(), 2))
                        st.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%")

        with tab3:
            st.header("⚖️ Domaranalys")
            f1, f2 = st.columns(2)
            with f1: sel_season_ref = st.selectbox("Välj säsong (Domare):", ["Alla"] + all_seasons)
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            with f2: sel_ref = st.selectbox("Välj domare:", refs)
            
            if sel_ref:
                ref_df = df if sel_season_ref == "Alla" else df[df['Säsong'] == sel_season_ref]
                r_df = ref_df[ref_df['ref_clean'] == sel_ref]
                if not r_df.empty:
                    c = st.columns(3)
                    c[0].metric("Matcher", len(r_df))
                    c[1].metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                    h_pen = r_df['Straffar Hemma'].sum() if 'Straffar Hemma' in r_df.columns else 0
                    a_pen = r_df['Straffar Borta'].sum() if 'Straffar Borta' in r_df.columns else 0
                    c[2].metric("Straffar", int(h_pen + a_pen))
                    st.dataframe(r_df[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta']], use_container_width=True, hide_index=True)

        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
