import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION (PERFECT LAYOUT - H2H & COMPACT FIX) ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

st.markdown("""
    <style>
    /* Ta bort onödigt mellanrum i Streamlit */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    .stDataFrame { margin-left: auto; margin-right: auto; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; text-align: center; }
    
    /* Titlar */
    .main-title { text-align: center; color: #1E1E1E; margin-bottom: 0px; font-weight: bold; }
    .sub-title { text-align: center; color: #666; margin-bottom: 15px; }
    
    /* Matchcenter Styling - Kompakt & Centrerad */
    .match-row { 
        background: white; 
        padding: 6px 12px; 
        border-radius: 8px; 
        border: 1px solid #eee; 
        margin-bottom: 4px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
    }
    .date-box { width: 150px; font-size: 0.8rem; color: #666; text-align: left; font-weight: 500; }
    .team-box { flex: 1; display: flex; align-items: center; justify-content: center; gap: 10px; font-weight: bold; font-size: 1rem; }
    .score-box { 
        background: #222; 
        color: white; 
        padding: 2px 12px; 
        margin: 0 20px; 
        border-radius: 4px; 
        min-width: 50px; 
        text-align: center; 
        font-weight: bold;
    }
    
    /* H2H Header Styling */
    .h2h-header { display: flex; justify-content: center; align-items: center; gap: 40px; margin: 10px 0 25px 0; width: 100%; }
    .h2h-logo { width: 100px; height: auto; }
    .h2h-title { font-size: 2.2rem; font-weight: bold; margin: 0; text-align: center; }
    
    /* Stats Styling */
    .stat-label { color: #888; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; text-align: center; margin-top: 10px; }
    .odds-box { 
        background: #fdfdfd; 
        padding: 10px; 
        border-radius: 10px; 
        border: 1px dashed #bbb; 
        text-align: center; 
        margin: 10px auto 20px auto; 
        max-width: 500px; 
    }
    .bell-style { font-size: 1.2rem; margin-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Deep Stats Pro 2026</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Perfect Layout - H2H Centered & Compact</p>", unsafe_allow_html=True)

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
    
    numeric_cols = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'response.goals.home', 'response.goals.away'
    ]
    
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
            
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"
if 'selected_match' not in st.session_state: st.session_state.selected_match = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    st.markdown(f"<div class='stat-label'>{label}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.4rem; font-weight:bold;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; font-size:1.4rem; color:#eee;'>|</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.4rem; font-weight:bold;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 3. LAYOUT ---
if df is not None:
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): st.session_state.view_mode = "main"; st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        # CENTERED HEADER WITH LARGE LOGOS
        st.markdown(f"""
            <div class='h2h-header'>
                <img src='{m['response.teams.home.logo']}' class='h2h-logo'>
                <h1 class='h2h-title'>{h_team} <span style='color:#ccc;'>vs</span> {a_team}</h1>
                <img src='{m['response.teams.away.logo']}' class='h2h-logo'>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.view_mode == "h2h_detail":
            st.markdown(f"""<div class="odds-box">
                <strong>Analys Odds (1X2):</strong> 2.15 | 3.45 | 3.05
            </div>""", unsafe_allow_html=True)

            h_hist = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
            a_hist = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mål snitt", round(h_hist['response.goals.home'].mean() + a_hist['response.goals.away'].mean(), 2) if not h_hist.empty else 0)
            m2.metric("xG snitt", round(h_hist['xG Hemma'].mean() + a_hist['xG Borta'].mean(), 2) if not h_hist.empty else 0)
            m3.metric("Hörnor snitt", round(h_hist['Hörnor Hemma'].mean() + a_hist['Hörnor Borta'].mean(), 1) if not h_hist.empty else 0)
            m4.metric("Gula snitt", round(h_hist['Gula kort Hemma'].mean() + a_hist['Gula Kort Borta'].mean(), 1) if not h_hist.empty else 0)

            st.write("---")
            stat_comparison_row("MÅL / MATCH", round(h_hist['response.goals.home'].mean(), 2) if not h_hist.empty else 0, round(a_hist['response.goals.away'].mean(), 2) if not a_hist.empty else 0)
            stat_comparison_row("XG / MATCH", round(h_hist['xG Hemma'].mean(), 2) if not h_hist.empty else 0, round(a_hist['xG Borta'].mean(), 2) if not a_hist.empty else 0)
            stat_comparison_row("BOLLINNEHAV", int(h_hist['Bollinnehav Hemma'].mean()) if not h_hist.empty else 0, int(a_hist['Bollinnehav Borta'].mean()) if not a_hist.empty else 0, True)

            st.write("")
            st.markdown("<h4 style='text-align:center;'>⚔️ Senaste inbördes möten</h4>", unsafe_allow_html=True)
            h2h = df[((df['response.teams.home.name'] == h_team) & (df['response.teams.away.name'] == a_team)) | 
                     ((df['response.teams.home.name'] == a_team) & (df['response.teams.away.name'] == h_team))]
            h2h = h2h[h2h['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)
            if not h2h.empty:
                st.dataframe(h2h[['datetime', 'response.teams.home.name', 'response.goals.home', 'response.goals.away', 'response.teams.away.name']], use_container_width=True, hide_index=True)

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True, label_visibility="collapsed")
            subset = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            
            for idx, r in subset.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(25).iterrows():
                show_bell = False
                if mode == "Nästa matcher":
                    hist = df[df['response.fixture.status.short'] == 'FT']
                    h_avg = hist[(hist['response.teams.home.name'] == r['response.teams.home.name']) | (hist['response.teams.away.name'] == r['response.teams.home.name'])].apply(lambda x: x['Gula kort Hemma'] if x['response.teams.home.name'] == r['response.teams.home.name'] else x['Gula Kort Borta'], axis=1).mean()
                    a_avg = hist[(hist['response.teams.home.name'] == r['response.teams.away.name']) | (hist['response.teams.away.name'] == r['response.teams.away.name'])].apply(lambda x: x['Gula kort Hemma'] if x['response.teams.home.name'] == r['response.teams.away.name'] else x['Gula Kort Borta'], axis=1).mean()
                    if (np.nan_to_num(h_avg) + np.nan_to_num(a_avg)) > 3.4: show_bell = True

                # DATUMFORMAT: 20 Feb 2026 19:00
                date_str = r['datetime'].strftime('%d %b %Y %H:%M')
                # RESULTAT: Tomt om det är nästa matcher
                score_display = "" if mode == "Nästa matcher" else f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}"
                
                col_m, col_b = st.columns([5, 1])
                with col_m:
                    st.markdown(f"""
                        <div class="match-row">
                            <div class="date-box">{date_str}</div>
                            <div class="team-box" style="text-align:right;">{r['response.teams.home.name']} <img src="{r['response.teams.home.logo']}" width="22"></div>
                            <div class="score-box">{score_display}</div>
                            <div class="team-box" style="text-align:left;"><img src="{r['response.teams.away.logo']}" width="22"> {r['response.teams.away.name']}</div>
                            {"<div class='bell-style'>🔔</div>" if show_bell else ""}
                        </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    if st.button("H2H" if mode == "Nästa matcher" else "Stat", key=f"btn{idx}", use_container_width=True):
                        st.session_state.selected_match = r
                        st.session_state.view_mode = "h2h_detail" if mode == "Nästa matcher" else "match_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                h_df = df[(df['response.teams.home.name'] == sel_team) & (df['response.fixture.status.short'] == 'FT')]
                a_df = df[(df['response.teams.away.name'] == sel_team) & (df['response.fixture.status.short'] == 'FT')]
                c = st.columns(4)
                c[0].metric("Matcher", len(h_df)+len(a_df))
                c[1].metric("Mål snitt", round((h_df['response.goals.home'].mean()+a_df['response.goals.away'].mean())/2, 2))
                st.divider()
                col_h, col_a = st.columns(2)
                with col_h:
                    st.subheader("🏠 HEMMA")
                    st.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%")
                    st.metric("xG", round(h_df['xG Hemma'].mean(), 2))
                    st.metric("Hörnor", round(h_df['Hörnor Hemma'].mean(), 1))
                with col_a:
                    st.subheader("✈️ BORTA")
                    st.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%")
                    st.metric("xG", round(a_df['xG Borta'].mean(), 2))
                    st.metric("Hörnor", round(a_df['Hörnor Borta'].mean(), 1))

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                st.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                st.dataframe(r_df[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta']], use_container_width=True, hide_index=True)

        with tab4:
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True, hide_index=True)
else:
    st.error("Kunde inte ladda data.")
