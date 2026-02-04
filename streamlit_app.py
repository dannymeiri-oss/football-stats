import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Röda Kort Hemma', 'Röda Kort Borta',
        'Skott på mål Hemma', 'Skott på mål Borta', 'Hörnor Hemma', 'Hörnor Borta',
        'Fouls Hemma', 'Fouls Borta', 'Total Skott Hemma', 'Total Skott Borta',
        'Skott Utanför Hemma', 'Skott Utanför Borta', 'Blockerade Skott Hemma', 'Blockerade Skott Borta',
        'Skott i Box Hemma', 'Skott i Box Borta', 'Skott utanför Box Hemma', 'Skott utanför Box Borta',
        'Passningar Hemma', 'Passningar Borta', 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta',
        'Offside Hemma', 'Offside Borta', 'Räddningar Hemma', 'Räddningar Borta',
        'Straffar Hemma', 'Straffar Borta',
        'response.goals.home', 'response.goals.away', 'response.fixture.status.short',
        'response.teams.home.logo', 'response.teams.away.logo', 'response.fixture.referee',
        'response.teams.home.name', 'response.teams.away.name'
    ]
    
    for col in cols_to_ensure:
        if col not in data.columns:
            data[col] = 0
        elif col not in ['response.fixture.referee', 'response.fixture.status.short', 'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name']:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

# --- SESSION STATE FÖR NAVIGATION ---
if 'view_match' not in st.session_state:
    st.session_state.view_match = None
if 'view_h2h' not in st.session_state:
    st.session_state.view_h2h = None

# --- HUVUDLAYOUT ---
if df is not None:
    years = sorted(df['Säsong'].unique(), reverse=True)
    year_options = ["Alla säsonger"] + [str(y) for y in years]

    # --- VY 1: STATISTIK-RAPPORT (SPELADE MATCHER) ---
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka till matcher"): 
            st.session_state.view_match = None
            st.rerun()
        
        r = st.session_state.view_match
        st.markdown(f"""<div style="text-align:center; padding:20px; background:#f8f9fa; border-radius:15px; border:1px solid #ddd;">
            <h1 style="margin:0;">{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>
            <p style="color:#666; margin-top:10px;">Domare: {r['ref_clean']} | Datum: {r['datetime'].strftime('%Y-%m-%d')}</p>
        </div>""", unsafe_allow_html=True)
        
        def stat_row(label, home_val, away_val, is_pct=False):
            c1, c2, c3 = st.columns([2, 1, 2])
            suffix = "%" if is_pct else ""
            c1.markdown(f"<div style='text-align:right; font-size:1.2em;'>{home_val}{suffix}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold;'>{label}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:left; font-size:1.2em;'>{away_val}{suffix}</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎯 Anfall")
            stat_row("xG", r['xG Hemma'], r['xG Borta'])
            stat_row("Totala Skott", int(r['Total Skott Hemma']), int(r['Total Skott Borta']))
            stat_row("Skott på mål", int(r['Skott på mål Hemma']), int(r['Skott på mål Borta']))
            stat_row("Skott i Box", int(r['Skott i Box Hemma']), int(r['Skott i Box Borta']))
            stat_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        with col2:
            st.subheader("⚽ Matchfakta")
            stat_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
            stat_row("Passningssäkerhet", int(r['Passningssäkerhet Hemma']), int(r['Passningssäkerhet Borta']), True)
            stat_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))
            stat_row("Fouls", int(r['Fouls Hemma']), int(r['Fouls Borta']))
            stat_row("Räddningar", int(r['Räddningar Hemma']), int(r['Räddningar Borta']))

    # --- VY 2: H2H-VY (KOMMANDE MATCHER) ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka till matcher"): 
            st.session_state.view_h2h = None
            st.rerun()
        
        match_info = st.session_state.view_h2h
        team1 = match_info['response.teams.home.name']
        team2 = match_info['response.teams.away.name']
        
        st.header(f"H2H Historik: {team1} vs {team2}")
        
        # Hitta alla spelade matcher mellan dessa två lag (oavsett hemma/borta)
        h2h_df = df[
            ((df['response.teams.home.name'] == team1) & (df['response.teams.away.name'] == team2)) |
            ((df['response.teams.home.name'] == team2) & (df['response.teams.away.name'] == team1))
        ]
        h2h_df = h2h_df[h2h_df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
        
        if not h2h_df.empty:
            for _, r in h2h_df.iterrows():
                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px; display:flex; align-items:center; justify-content:space-between;">
                    <div style="width:100px; font-size:0.9em;">{r['datetime'].strftime('%Y-%m-%d')}</div>
                    <div style="flex:1; text-align:right; font-weight:bold;">{r['response.teams.home.name']}</div>
                    <div style="background:#222; color:white; padding:5px 15px; border-radius:5px; margin:0 20px; font-weight:bold;">{score}</div>
                    <div style="flex:1; text-align:left; font-weight:bold;">{r['response.teams.away.name']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Inga tidigare möten hittades i databasen.")

    # --- VY 3: FLIKARNA (HEMSKÄRMEN) ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        with tab1:
            st.header("Matchcenter")
            m_col, s_col = st.columns(2)
            mode = m_col.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            search = s_col.text_input("Sök lag:", "", key="search_main")
            
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            if search:
                d_df = d_df[(d_df['response.teams.home.name'].str.contains(search, case=False)) | (d_df['response.teams.away.name'].str.contains(search, case=False))]
            
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1.2])
                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Senaste resultaten" else "VS"
                
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]} <img src="{r["response.teams.home.logo"]}" width="18"></div><div style="background:#222; color:white; padding:2px 8px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div><div style="flex:1; text-align:left; font-weight:bold;"><img src="{r["response.teams.away.logo"]}" width="18"> {r["response.teams.away.name"]}</div></div>', unsafe_allow_html=True)
                
                with c_b:
                    if mode == "Senaste resultaten":
                        if st.button("Statistik", key=f"stat{idx}"):
                            st.session_state.view_match = r
                            st.rerun()
                    else:
                        if st.button("H2H", key=f"h2h{idx}"):
                            st.session_state.view_h2h = r
                            st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            f_col1, f_col2 = st.columns(2)
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = f_col1.selectbox("Välj lag:", all_teams)
            sel_year_team = f_col2.selectbox("Välj säsong (Lag):", year_options)
            if sel_team:
                t_df = df if sel_year_team == "Alla säsonger" else df[df['Säsong'] == int(sel_year_team)]
                h_df = t_df[(t_df['response.teams.home.name'] == sel_team) & (t_df['response.fixture.status.short'] == 'FT')]
                a_df = t_df[(t_df['response.teams.away.name'] == sel_team) & (t_df['response.fixture.status.short'] == 'FT')]
                st.subheader(f"📊 Totalt snitt ({sel_year_team})")
                t_m = len(h_df) + len(a_df)
                if t_m > 0:
                    tc1, tc2, tc3, tc4, tc5 = st.columns(5)
                    tc1.metric("Matcher", t_m)
                    tc2.metric("Mål snitt", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/t_m, 2))
                    tc3.metric("xG snitt", round((h_df['xG Hemma'].sum() + a_df['xG Borta'].sum())/t_m, 2))
                    tc4.metric("Hörnor snitt", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/t_m, 2))
                    tc5.metric("Gula snitt", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/t_m, 2))
                st.divider()
                col_h, col_a = st.columns(2)
                with col_h:
                    st.subheader("🏠 HEMMA")
                    if not h_df.empty:
                        for label, col in [("Matcher Hemma", 'datetime'), ("Mål", 'response.goals.home'), ("xG", 'xG Hemma'), ("Bollinnehav", 'Bollinnehav Hemma'), ("Skott på mål", 'Skott på mål Hemma'), ("Totala Skott", 'Total Skott Hemma'), ("Skott Utanför", 'Skott Utanför Hemma'), ("Blockar", 'Blockerade Skott Hemma'), ("Skott i Box", 'Skott i Box Hemma'), ("Skott utanför Box", 'Skott utanför Box Hemma'), ("Hörnor", 'Hörnor Hemma'), ("Offside", 'Offside Hemma'), ("Fouls", 'Fouls Hemma'), ("Räddningar", 'Räddningar Hemma'), ("Gula Kort", 'Gula kort Hemma'), ("Röda Kort", 'Röda Kort Hemma'), ("Passningar", 'Passningar Hemma'), ("Passnings%", 'Passningssäkerhet Hemma')]:
                            val = len(h_df) if label == "Matcher Hemma" else h_df[col].mean()
                            st.metric(label, round(val, 1) if "Passnings%" not in label and label != "Matcher Hemma" else (f"{int(val)}%" if "Passnings%" in label else int(val)))
                with col_a:
                    st.subheader("✈️ BORTA")
                    if not a_df.empty:
                        for label, col in [("Matcher Borta", 'datetime'), ("Mål", 'response.goals.away'), ("xG", 'xG Borta'), ("Bollinnehav", 'Bollinnehav Borta'), ("Skott på mål", 'Skott på mål Borta'), ("Totala Skott", 'Total Skott Borta'), ("Skott Utanför", 'Skott Utanför Borta'), ("Blockar", 'Blockerade Skott Borta'), ("Skott i Box", 'Skott i Box Borta'), ("Skott utanför Box", 'Skott utanför Box Borta'), ("Hörnor", 'Hörnor Borta'), ("Offside", 'Offside Borta'), ("Fouls", 'Fouls Borta'), ("Räddningar", 'Räddningar Borta'), ("Gula Kort", 'Gula Kort Borta'), ("Röda Kort", 'Röda Kort Borta'), ("Passningar", 'Passningar Borta'), ("Passnings%", 'Passningssäkerhet Borta')]:
                            val = len(a_df) if label == "Matcher Borta" else a_df[col].mean()
                            st.metric(label, round(val, 1) if "Passnings%" not in label and label != "Matcher Borta" else (f"{int(val)}%" if "Passnings%" in label else int(val)))

        with tab3:
            st.header("⚖️ Domaranalys")
            d_col1, d_col2 = st.columns(2)
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = d_col1.selectbox("Välj domare:", refs)
            sel_year_ref = d_col2.selectbox("Välj säsong (Domare):", year_options)
            if sel_ref:
                ref_year_df = df if sel_year_ref == "Alla säsonger" else df[df['Säsong'] == int(sel_year_ref)]
                r_df = ref_year_df[ref_year_df['ref_clean'] == sel_ref]
                if not r_df.empty:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Matcher", len(r_df))
                    c2.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                    c3.metric("Fouls/Match", round((r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean(), 2))
                    c4.metric("Straffar", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None: 
                st.dataframe(standings_df, hide_index=True, use_container_width=True)
else:
    st.error("Kunde inte ladda data.")
