import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFEKT LAYOUT - FULLSTÄNDIG) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    .sub-title { text-align: center; color: #666; margin-bottom: 25px; }
    .bell-style { font-size: 1.3rem; display: flex; align-items: center; justify-content: center; height: 100%; }
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Perfekt Layout - Fullständig Version</p>", unsafe_allow_html=True)

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
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    numeric_cols = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'Fouls Hemma', 'Fouls Borta', 'Straffar Hemma', 'Straffar Borta',
        'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
        'response.goals.home', 'response.goals.away'
    ]
    
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        else:
            data[col] = 0.0
            
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.1em;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode == "match_detail":
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        r = st.session_state.selected_match
        st.markdown(f"<h2 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h2>", unsafe_allow_html=True)
        st.divider()
        stat_comparison_row("xG", round(r['xG Hemma'], 2), round(r['xG Borta'], 2))
        stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
        stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    elif st.session_state.view_mode == "h2h_detail":
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h2 style='text-align: center;'>{h_team} vs {a_team}</h2>", unsafe_allow_html=True)
        
        h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mål snitt", round(h_hist['response.goals.home'].mean() + a_hist['response.goals.away'].mean(), 2))
        c2.metric("xG snitt", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2))
        c3.metric("Hörnor snitt", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1))
        c4.metric("Gula snitt", round(h_hist['Gula kort Hemma'].mean() + a_hist['Gula Kort Borta'].mean(), 1))
        
        st.write("")
        stat_comparison_row("Mål/Match", round(h_hist['response.goals.home'].mean(), 2), round(a_hist['response.goals.away'].mean(), 2))
        stat_comparison_row("xG/Match", round(h_hist['xG Hemma'].mean(), 2), round(a_hist['xG Borta'].mean(), 2))
        stat_comparison_row("Hörnor snitt", round(h_hist['Hörnor Hemma'].mean(), 1), round(a_hist['Hörnor Borta'].mean(), 1))

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            subset = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(30).iterrows():
                show_bell = False
                if mode == "Nästa matcher":
                    # Klock-analys
                    h_total = df[(df['response.teams.home.name'] == r['response.teams.home.name']) | (df['response.teams.away.name'] == r['response.teams.home.name'])]
                    h_avg = h_total.apply(lambda x: x['Gula kort Hemma'] if x['response.teams.home.name'] == r['response.teams.home.name'] else x['Gula Kort Borta'], axis=1).mean()
                    a_total = df[(df['response.teams.home.name'] == r['response.teams.away.name']) | (df['response.teams.away.name'] == r['response.teams.away.name'])]
                    a_avg = a_total.apply(lambda x: x['Gula kort Hemma'] if x['response.teams.home.name'] == r['response.teams.away.name'] else x['Gula Kort Borta'], axis=1).mean()
                    if (np.nan_to_num(h_avg) + np.nan_to_num(a_avg)) > 3.4: show_bell = True

                col_info, col_btn = st.columns([4.5, 1.5])
                with col_info:
                    score = "VS" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                    st.markdown(f"""
                        <div class="match-row">
                            <div style="width:70px; font-size:0.8em; color:gray;">{r['datetime'].strftime('%d %b')}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{r['response.teams.home.name']} <img src="{r['response.teams.home.logo']}" width="20"></div>
                            <div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{r['response.teams.away.logo']}" width="20"> {r['response.teams.away.name']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    c_b1, c_b2 = st.columns([2, 1])
                    with c_b1:
                        if st.button("H2H" if mode == "Nästa matcher" else "Analys", key=f"m{idx}", use_container_width=True):
                            st.session_state.selected_match = r
                            st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"
                            st.rerun()
                    with c_b2:
                        if show_bell: st.markdown("<div class='bell-style'>🔔</div>", unsafe_allow_html=True)

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                h_df = df[(df['response.teams.home.name'] == sel_team) & (df['response.fixture.status.short'] == 'FT')]
                a_df = df[(df['response.teams.away.name'] == sel_team) & (df['response.fixture.status.short'] == 'FT')]
                cols = st.columns(4)
                cols[0].metric("Matcher", len(h_df) + len(a_df))
                cols[1].metric("Mål snitt", round((h_df['response.goals.home'].sum() + a_df['response.goals.away'].sum())/(len(h_df)+len(a_df)), 2))
                cols[2].metric("Gula snitt", round((h_df['Gula kort Hemma'].sum() + a_df['Gula Kort Borta'].sum())/(len(h_df)+len(a_df)), 2))
                cols[3].metric("Hörnor snitt", round((h_df['Hörnor Hemma'].sum() + a_df['Hörnor Borta'].sum())/(len(h_df)+len(a_df)), 1))
                
                st.write("---")
                ch, ca = st.columns(2)
                with ch:
                    st.subheader("Hemma")
                    st.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%")
                    st.metric("Passnings%", f"{int(h_df['Passningssäkerhet Hemma'].mean())}%")
                with ca:
                    st.subheader("Borta")
                    st.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%")
                    st.metric("Passnings%", f"{int(a_df['Passningssäkerhet Borta'].mean())}%")

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                c = st.columns(3)
                c[0].metric("Matcher", len(r_df))
                c[1].metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                c[2].metric("Straffar", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))
                st.dataframe(r_df[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta']], use_container_width=True, hide_index=True)

        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)

else:
    st.error("Kunde inte ladda data.")
