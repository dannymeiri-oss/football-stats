import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFEKT LAYOUT) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    .sub-title { text-align: center; color: #666; margin-bottom: 25px; }
    .bell-style { font-size: 1.5rem; display: flex; align-items: center; height: 100%; padding-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Perfekt Layout - Stabiliserad Version</p>", unsafe_allow_html=True)

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "1363673756" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

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
    
    # Säkerställ att kolumner finns för att undvika KeyError
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

df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

# Initiera session state korrekt för att undvika ValueError
if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.1em;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    # Kontrollera om vi ska visa detaljvy (Match eller H2H)
    show_main = True
    
    if st.session_state.view_match is not None:
        show_main = False
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h2 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h2>", unsafe_allow_html=True)
        st.divider()
        stat_comparison_row("xG", round(r['xG Hemma'], 2), round(r['xG Borta'], 2))
        stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
        stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    elif st.session_state.view_h2h is not None:
        show_main = False
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h2 style='text-align: center;'>{h_team} vs {a_team}</h2>", unsafe_allow_html=True)
        
        # Hämta historik för snittberäkning
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Mål snitt", round(h_stats['response.goals.home'].mean() + a_stats['response.goals.away'].mean(), 2) if not h_stats.empty else 0)
        tc2.metric("xG snitt", round(h_stats['xG Hemma'].mean() + a_stats['xG Borta'].mean(), 2) if not h_stats.empty else 0)
        tc3.metric("Hörnor snitt", round(h_stats['Hörnor Hemma'].mean() + a_stats['Hörnor Borta'].mean(), 1) if not h_stats.empty else 0)
        tc4.metric("Gula snitt", round(h_stats['Gula kort Hemma'].mean() + a_stats['Gula Kort Borta'].mean(), 1) if not h_stats.empty else 0)
        
        st.write("") 
        stat_comparison_row("Mål/Match", round(h_stats['response.goals.home'].mean(), 2) if not h_stats.empty else 0, round(a_stats['response.goals.away'].mean(), 2) if not a_stats.empty else 0)
        stat_comparison_row("xG/Match", round(h_stats['xG Hemma'].mean(), 2) if not h_stats.empty else 0, round(a_stats['xG Borta'].mean(), 2) if not a_stats.empty else 0)

    if show_main:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(40).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                h_logo, a_logo = r.get('response.teams.home.logo', ''), r.get('response.teams.away.logo', '')
                
                show_alert = False
                if mode == "Nästa matcher":
                    # Smart klock-logik: Letar i ALL historik för lagen
                    hist = df[df['response.fixture.status.short'] == 'FT']
                    h_avg = hist[hist['response.teams.home.name'] == h_name]['Gula kort Hemma'].mean()
                    a_avg = hist[hist['response.teams.away.name'] == a_name]['Gula Kort Borta'].mean()
                    
                    if (np.nan_to_num(h_avg) + np.nan_to_num(a_avg)) > 3.4: 
                        show_alert = True

                c_i, c_b = st.columns([4.2, 1.8]) 
                score_text = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Resultat" else "VS"
                with c_i:
                    st.markdown(f'''<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                            <div style="width:80px; font-size:0.8em; color:gray;">{r["datetime"].strftime("%d %b")}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{h_logo}" width="22"></div>
                            <div style="background:#222; color:white; padding:2px 12px; margin:0 15px; border-radius:4px; font-weight:bold; min-width:65px; text-align:center;">{score_text}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{a_logo}" width="22"> {a_name}</div>
                            <div style="margin-left:10px; font-size:0.7em; color:blue; width:100px;">{r.get("response.league.name", "")}</div></div>''', unsafe_allow_html=True)
                with c_b:
                    col_btn, col_bell = st.columns([2.5, 1])
                    with col_btn:
                        btn_label = "H2H" if mode=="Nästa matcher" else "Statistik"
                        if st.button(btn_label, key=f"btn{idx}", use_container_width=True):
                            if mode=="Nästa matcher": st.session_state.view_h2h = r
                            else: st.session_state.view_match = r
                            st.rerun()
                    with col_bell:
                        if show_alert: st.markdown("<div class='bell-style'>🔔</div>", unsafe_allow_html=True)

        with tab2:
            st.header("🛡️ Laganalys")
            # Bevarad kod för laganalys...
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                st.write(f"Analys för {sel_team}")

        with tab3:
            st.header("⚖️ Domaranalys")
            # Fixad domaranalys utan Straffar-krasch
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                st.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))

        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
