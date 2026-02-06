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
    .match-row { background: white; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 5px; display: flex; align-items: center; cursor: pointer; }
    .match-time { font-size: 0.8rem; color: #666; width: 50px; }
    .match-teams { flex: 1; display: flex; align-items: center; gap: 10px; font-weight: 500; }
    .match-score { font-weight: bold; width: 60px; text-align: center; background: #f0f0f0; border-radius: 4px; }
    
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
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=712668345"

# --- 2. DATAHANTERING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

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
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    else:
        data['datetime'] = pd.Timestamp.now()
    
    if 'Säsong' not in data.columns:
        data['Säsong'] = data['datetime'].dt.year.astype(str)

    needed_cols = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'Fouls Hemma', 'Fouls Borta', 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 
        'Skott på mål Hemma', 'Skott på mål Borta', 'Skott totalt Hemma', 'Skott totalt Borta', 
        'Röda kort Hemma', 'Röda kort Borta', 'Räddningar Hemma', 'Räddningar Borta', 
        'Offside Hemma', 'Offside Borta', 'response.goals.home', 'response.goals.away'
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
        
        # Match Header
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
            
            # Referee Info Row
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
            stat_comparison_row("BOLLINNEHAV", h_hist['Bollinnehav Hemma'].mean(), h_hist['Bollinnehav Borta'].mean(), is_pct=True, precision=0)
            stat_comparison_row("HÖRNOR / MATCH", h_hist['Hörnor Hemma'].mean(), a_hist['Hörnor Borta'].mean(), precision=1)
            stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)

    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys", "🏆 Tabell", "📊 Topplista"])
        
        with tab1:
            st.subheader("📅 Matchcenter")
            leagues = sorted(df['response.league.name'].unique())
            sel_league = st.selectbox("Filtrera på liga:", ["Alla ligor"] + leagues)
            m_df = df if sel_league == "Alla ligor" else df[df['response.league.name'] == sel_league]
            
            for _, row in m_df.sort_values('datetime', ascending=False).head(20).iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"""
                        <div class="match-row">
                            <div class="match-time">{row['datetime'].strftime('%H:%M')}</div>
                            <div class="match-teams">
                                <img src="{row['response.teams.home.logo']}" width="25"> {row['response.teams.home.name']} 
                                <span style="color:#ccc; margin:0 10px;">vs</span> 
                                <img src="{row['response.teams.away.logo']}" width="25"> {row['response.teams.away.name']}
                            </div>
                            <div class="match-score">{int(row['response.goals.home'])}-{int(row['response.goals.away'])}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("H2H", key=f"h2h_{row['response.fixture.id']}"):
                        st.session_state.selected_match = row
                        st.session_state.view_mode = "h2h_detail"
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(df['response.teams.home.name'].unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            t_df = df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)]
            if not t_df.empty:
                st.markdown(f"<div class='section-header'>Statistik för {sel_team}</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                c1.metric("Matcher", len(t_df))
                c2.metric("Snitt xG", round((t_df['xG Hemma'].mean() + t_df['xG Borta'].mean())/2, 2))
                c3.metric("Snitt Hörnor", round((t_df['Hörnor Hemma'].mean() + t_df['Hörnor Borta'].mean())/2, 1))

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r != "Domare: Okänd"])
            sel_ref = st.selectbox("Välj domare:", refs)
            r_df = df[df['ref_clean'] == sel_ref]
            if not r_df.empty:
                st.markdown(f"<div class='section-header'>Domarhistorik: {sel_ref}</div>", unsafe_allow_html=True)
                st.dataframe(r_df[['Speltid', 'response.teams.home.name', 'response.teams.away.name', 'Gula kort Hemma', 'Gula Kort Borta']], use_container_width=True, hide_index=True)

        with tab4:
            st.markdown("<h2 style='text-align:center;'>🏆 Aktuell Tabell</h2>", unsafe_allow_html=True)
            if standings_df is not None:
                liga_col = standings_df.columns[0]
                available_leagues = sorted(standings_df[liga_col].dropna().unique().tolist())
                sel_league_stand = st.selectbox("Välj liga:", available_leagues, key="stand_sel")
                display_table = standings_df[standings_df[liga_col] == sel_league_stand].copy()
                st.dataframe(display_table.iloc[:, 1:], use_container_width=True, hide_index=True)

        with tab5:
            st.header("📊 Topplista")
            st.info("Topplistan baseras på data i Raw Data.")

else:
    st.error("Kunde inte ladda data från Google Sheets.")
