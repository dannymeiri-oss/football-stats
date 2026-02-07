import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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
    
    /* DOMARE INFO I H2H */
    .referee-box { text-align: center; background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 20px; font-weight: bold; }

    /* AI INSIGHT BOX */
    .ai-box { background: #f0f7ff; border: 1px solid #007bff; border-radius: 10px; padding: 15px; margin-top: 20px; text-align: center; }
    .ai-header { color: #007bff; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 5px; }
    .ai-prediction { font-size: 1.3rem; font-weight: bold; color: #1E1E1E; }
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
        league_col, pos_col, team_col = standings.columns[0], standings.columns[1], standings.columns[2]
        row = standings[(standings[league_col].astype(str) == str(league_name)) & 
                        (standings[team_col].astype(str) == str(team_name))]
        if not row.empty: return f"#{int(float(row[pos_col].values[0]))}"
    except: pass
    return ""

def get_rolling_card_avg(team_name, full_df, n=10):
    m = full_df[((full_df['response.teams.home.name'] == team_name) | (full_df['response.teams.away.name'] == team_name)) & (full_df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(n)
    if m.empty: return 0.0
    cards = [r['Gula kort Hemma'] if r['response.teams.home.name'] == team_name else r['Gula Kort Borta'] for _, r in m.iterrows()]
    return sum(cards) / len(cards)

def format_referee(name):
    if not name or pd.isna(name) or str(name).strip() in ["0", "Okänd", "nan", "None"]: return "Domare: Okänd"
    parts = str(name).split(',')[0].strip().split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) >= 2 else name

def clean_stats(data):
    if data is None: return None
    data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce').dt.tz_localize(None)
    cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 'response.goals.home', 'response.goals.away']
    for c in cols:
        if c in data.columns: data[c] = pd.to_numeric(data[c].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").apply(format_referee)
    data['Speltid'] = data['datetime'].dt.strftime('%d %b %Y')
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

if 'view_mode' not in st.session_state: st.session_state.view_mode = "main"

def stat_comparison_row(label, x1, x2, is_pct=False, precision=2):
    st.markdown(f"<div class='stat-label-centered'>{label}</div>", unsafe_allow_html=True)
    v1 = f"{x1:.{precision}f}" + ("%" if is_pct else "")
    v2 = f"{x2:.{precision}f}" + ("%" if is_pct else "")
    st.markdown(f"<div class='stat-comparison'><div style='flex:1; text-align:right;'>{v1}</div><div style='color:#ccc; margin:0 10px;'>|</div><div style='flex:1; text-align:left;'>{v2}</div></div>", unsafe_allow_html=True)

# --- 3. AI MOTOR ---
def get_ai_insight(h_avg, a_avg, ref_avg):
    combined_score = h_avg + a_avg
    if ref_avg > 0:
        # Viktning: 60% lagens historik, 40% domarens historik
        final_prediction = (combined_score * 0.6) + (ref_avg * 0.4)
    else:
        final_prediction = combined_score

    if final_prediction >= 4.5:
        return "🔥 Hög Sannolikhet: Över 4.5 kort", "Hög intensitet förväntas"
    elif final_prediction >= 3.5:
        return "✅ Sannolikt: Över 3.5 kort", "Stabil kortstatistik i båda lagen"
    elif final_prediction <= 2.5:
        return "⚠️ Varning: Under 3.5 kort", "Få kort förväntas"
    else:
        return "⚖️ Neutral: Över 2.5 kort", "Osäker marknad"

# --- 4. LAYOUT ---
if df is not None:
    if st.session_state.view_mode == "h2h_detail":
        if st.button("← Tillbaka"): st.session_state.view_mode = "main"; st.rerun()
        m = st.session_state.selected_match
        ref_n = m['ref_clean']
        st.markdown(f"<div style='background:#0e1117; padding:20px; border-radius:10px; text-align:center;'><h2 style='color:white;'>{m['response.teams.home.name']} VS {m['response.teams.away.name']}</h2></div>", unsafe_allow_html=True)
        
        ref_avg_val = 0.0
        if ref_n != "Domare: Okänd":
            r_hist = df[(df['ref_clean'] == ref_n) & (df['response.fixture.status.short'] == 'FT')].sort_values('datetime', ascending=False).head(10)
            if not r_hist.empty:
                ref_avg_val = (r_hist['Gula kort Hemma'].sum() + r_hist['Gula Kort Borta'].sum()) / len(r_hist)
                st.markdown(f"<div class='referee-box'>⚖️ Domare: {ref_n} | Snitt Gula Kort (Senaste 10): {ref_avg_val:.2f}</div>", unsafe_allow_html=True)

        h_avg_val = get_rolling_card_avg(m['response.teams.home.name'], df)
        a_avg_val = get_rolling_card_avg(m['response.teams.away.name'], df)
        
        # AI INSIGHT BOX
        title, desc = get_ai_insight(h_avg_val, a_avg_val, ref_avg_val)
        st.markdown(f"""
            <div class="ai-box">
                <div class="ai-header">🤖 AI Match Insight (Kortanalys)</div>
                <div class="ai-prediction">{title}</div>
                <div style="font-size:0.85rem; color:#555;">{desc}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<h3 style='text-align:center; margin-top:20px;'>SEASON AVERAGES COMPARISON</h3>", unsafe_allow_html=True)
        h_hist = df[(df['response.teams.home.name'] == m['response.teams.home.name']) & (df['response.fixture.status.short'] == 'FT')]
        a_hist = df[(df['response.teams.away.name'] == m['response.teams.away.name']) & (df['response.fixture.status.short'] == 'FT')]
        stat_comparison_row("MÅL / MATCH", h_hist['response.goals.home'].mean(), a_hist['response.goals.away'].mean())
        stat_comparison_row("GULA KORT / MATCH", h_hist['Gula kort Hemma'].mean(), a_hist['Gula Kort Borta'].mean(), precision=1)

    else:
        tab1, tab2, tab3 = st.tabs(["📅 Matchcenter", "🛡️ Laganalys", "⚖️ Domaranalys"])
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            subset = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')].sort_values('datetime', ascending=(mode=="Nästa matcher")).head(20)
            for idx, r in subset.iterrows():
                h_avg = get_rolling_card_avg(r['response.teams.home.name'], df)
                a_avg = get_rolling_card_avg(r['response.teams.away.name'], df)
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(f"""
                        <div class="match-row" style="flex-direction: column; align-items: stretch;">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <div style="width:100px; font-size:0.8em; color:gray;">{r['Speltid']}</div>
                                <div style="flex:1; text-align:right; font-weight:bold;">{r['response.teams.home.name']} <img src="{r['response.teams.home.logo']}" width="20"></div>
                                <div style="background:#222; color:white; padding:2px 10px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{"VS" if mode=="Nästa matcher" else f"{int(r['response.goals.home'])}-{int(r['response.goals.away'])}"}</div>
                                <div style="flex:1; text-align:left; font-weight:bold;"><img src="{r['response.teams.away.logo']}" width="20"> {r['response.teams.away.name']}</div>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 5px; border-top: 1px solid #eee; padding-top: 4px;">
                                <div style="width:100px;"></div>
                                <div style="flex:1; text-align:right; color:{'#28a745' if h_avg >= 2.0 else 'black'}; font-weight:bold; font-size:0.75rem;">🟨 {h_avg:.2f}</div>
                                <div style="width:70px;"></div>
                                <div style="flex:1; text-align:left; color:{'#28a745' if a_avg >= 2.0 else 'black'}; font-weight:bold; font-size:0.75rem;">🟨 {a_avg:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("Analys", key=f"btn_{idx}", use_container_width=True):
                        st.session_state.selected_match, st.session_state.view_mode = r, "h2h_detail"
                        st.rerun()

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r != "Domare: Okänd"])
            sel_ref = st.selectbox("Välj domare:", ["Välj..."] + refs)
            if sel_ref != "Välj...":
                r_df = df[df['ref_clean'] == sel_ref].sort_values('datetime', ascending=False)
                st.metric("Snitt Gula Kort", round((r_df['Gula kort Hemma'].sum() + r_df['Gula Kort Borta'].sum()) / len(r_df), 2))
                for idx, row in r_df.iterrows():
                    st.write(f"{row['Speltid']}: {row['response.teams.home.name']} - {row['response.teams.away.name']} (🟨 {int(row['Gula kort Hemma'] + row['Gula Kort Borta'])})")
else: st.error("Kunde inte ladda data.")
