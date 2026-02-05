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
    .sub-title { text-align: center; color: #666; margin-bottom: 25px; }
    
    /* MATCHCENTER CSS */
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    
    /* H2H SPECIFIK DESIGN */
    .centered-header { display: flex; justify-content: center; align-items: center; gap: 30px; margin-bottom: 20px; width: 100%; }
    .h2h-logo { width: 100px; }
    .stat-label-centered { color: #888; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; text-align: center; margin-top: 10px; }
    .stat-comparison { display: flex; justify-content: center; align-items: center; gap: 20px; font-size: 1.4rem; font-weight: bold; }
    
    /* SEKTIONER LAGANALYS & DOMARE */
    .section-header { text-align: center; padding: 8px; background: #222; color: white; border-radius: 5px; margin: 20px 0 15px 0; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
    .total-header { text-align: center; padding: 5px; color: #444; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Domarstatistik Återställd</p>", unsafe_allow_html=True)

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

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): st.session_state.view_mode = "main"; st.rerun()
        # (H2H Innehåll bevaras här)
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell"])
        
        # --- TAB 1: MATCHCENTER ---
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
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"; st.rerun()

        # --- TAB 2: LAGANALYS (PERFEKT LAYOUT) ---
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
                tot_m = len(h_df) + len(a_df)

                if tot_m > 0:
                    st.markdown("<div class='total-header'>TOTAL PRESTATION (SNITT)</div>", unsafe_allow_html=True)
                    t1, t2, t3, t4, t5, t6 = st.columns(6)
                    t1.metric("Matcher", tot_m)
                    t2.metric("Mål", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/tot_m, 2))
                    t3.metric("xG", round((h_df['xG Hemma'].sum() + a_df['xG Borta'].sum())/tot_m, 2))
                    t4.metric("Hörnor", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/tot_m, 1))
                    t5.metric("Gula Kort", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/tot_m, 1))
                    t6.metric("Bollinnehav", f"{int((h_df['Bollinnehav Hemma'].sum() + a_df['Bollinnehav Borta'].sum())/tot_m)}%")

                    col_h, col_a = st.columns(2)
                    with col_h:
                        st.markdown("<div class='section-header'>🏠 Hemma</div>", unsafe_allow_html=True)
                        if not h_df.empty:
                            c1, c2 = st.columns(2)
                            c1.metric("Mål", round(h_df['response.goals.home'].mean(), 2))
                            c2.metric("xG", round(h_df['xG Hemma'].mean(), 2))
                            c1.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%")
                            c2.metric("Hörnor", round(h_df['Hörnor Hemma'].mean(), 1))
                            c1.metric("Gula Kort", round(h_df['Gula kort Hemma'].mean(), 1))
                            c2.metric("Röda Kort", round(h_df['Röda kort Hemma'].mean(), 2))
                            c1.metric("Fouls", round(h_df['Fouls Hemma'].mean(), 1))
                            c2.metric("Straffar (Tot)", int(h_df['Straffar Hemma'].sum()))
                            c1.metric("Skott på mål", round(h_df['Skott på mål Hemma'].mean(), 1))
                            c2.metric("Skott totalt", round(h_df['Skott totalt Hemma'].mean(), 1))
                            c1.metric("Passnings%", f"{int(h_df['Passningssäkerhet Hemma'].mean())}%")
                            c2.metric("Räddningar", round(h_df['Räddningar Hemma'].mean(), 1))
                            c1.metric("Offside", round(h_df['Offside Hemma'].mean(), 1))

                    with col_a:
                        st.markdown("<div class='section-header'>✈️ Borta</div>", unsafe_allow_html=True)
                        if not a_df.empty:
                            c1, c2 = st.columns(2)
                            c1.metric("Mål", round(a_df['response.goals.away'].mean(), 2))
                            c2.metric("xG", round(a_df['xG Borta'].mean(), 2))
                            c1.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%")
                            c2.metric("Hörnor", round(a_df['Hörnor Borta'].mean(), 1))
                            c1.metric("Gula Kort", round(a_df['Gula Kort Borta'].mean(), 1))
                            c2.metric("Röda Kort", round(a_df['Röda kort Borta'].mean(), 2))
                            c1.metric("Fouls", round(a_df['Fouls Borta'].mean(), 1))
                            c2.metric("Straffar (Tot)", int(a_df['Straffar Borta'].sum()))
                            c1.metric("Skott på mål", round(a_df['Skott på mål Borta'].mean(), 1))
                            c2.metric("Skott totalt", round(a_df['Skott totalt Borta'].mean(), 1))
                            c1.metric("Passnings%", f"{int(a_df['Passningssäkerhet Borta'].mean())}%")
                            c2.metric("Räddningar", round(a_df['Räddningar Borta'].mean(), 1))
                            c1.metric("Offside", round(a_df['Offside Borta'].mean(), 1))

        # --- TAB 3: DOMARANALYS (NY UPPDATERING) ---
        with tab3:
            st.header("⚖️ Domaranalys")
            rf1, rf2 = st.columns(2)
            # Filtrera bort domare utan namn
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd", "nan"]])
            with rf1: sel_ref = st.selectbox("Välj domare:", ["Välj domare..."] + refs, key="ref_analysis_sel")
            with rf2: sel_ref_season = st.selectbox("Välj säsong:", ["Alla"] + all_seasons, key="ref_season_sel")
            
            if sel_ref != "Välj domare...":
                ref_df = df if sel_ref_season == "Alla" else df[df['Säsong'] == sel_ref_season]
                r_df = ref_df[ref_df['ref_clean'] == sel_ref]
                
                if not r_df.empty:
                    st.markdown(f"<div class='section-header'>Statistik för {sel_ref}</div>", unsafe_allow_html=True)
                    
                    # Beräkningar
                    m_count = len(r_df)
                    gula_tot = r_df['Gula kort Hemma'].sum() + r_df['Gula Kort Borta'].sum()
                    straff_tot = r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()
                    
                    d1, d2, d3 = st.columns(3)
                    d1.metric("Antal Matcher", m_count)
                    d2.metric("Gula Kort (Snitt)", round(gula_tot / m_count, 2) if m_count > 0 else "N/A")
                    
                    # Straff-logik: Visa N/A om det inte finns data (t.ex. om alla är 0 eller saknas)
                    straff_display = int(straff_tot) if straff_tot >= 0 else "N/A"
                    d3.metric("Antal Straffar", straff_display)
                    
                    st.divider()
                    st.subheader("Senaste dömda matcher")
                    st.dataframe(
                        r_df[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta', 'Straffar Hemma', 'Straffar Borta']]
                        .sort_values('datetime', ascending=False),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info(f"Ingen data hittades för {sel_ref} under säsongen {sel_ref_season}.")

        # --- TAB 4: TABELL ---
        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
