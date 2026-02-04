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
        'response.teams.home.logo', 'response.teams.away.logo', 'response.fixture.referee'
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

if 'view_match' not in st.session_state:
    st.session_state.view_match = None

# --- HUVUDLAYOUT ---
if df is not None:
    years = sorted(df['Säsong'].unique(), reverse=True)
    year_options = ["Alla säsonger"] + [str(y) for y in years]

    if st.session_state.view_match is not None:
        # --- DETALJERAD MATCHRAPPORT (STATISTIK-VY) ---
        if st.button("← Tillbaka till matcher"): 
            st.session_state.view_match = None
            st.rerun()
        
        r = st.session_state.view_match
        
        # Header med resultat
        st.markdown(f"""
            <div style="text-align:center; padding:20px; background:#f8f9fa; border-radius:15px; border:1px solid #ddd;">
                <h1 style="margin:0;">{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>
                <p style="color:#666; margin-top:10px;">Domare: {r['ref_clean']} | Datum: {r['datetime'].strftime('%Y-%m-%d')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # Funktion för att rita en jämförelse-rad
        def stat_row(label, home_val, away_val, is_pct=False):
            c1, c2, c3 = st.columns([2, 1, 2])
            suffix = "%" if is_pct else ""
            c1.markdown(f"<div style='text-align:right; font-size:1.2em;'>{home_val}{suffix}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold;'>{label}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:left; font-size:1.2em;'>{away_val}{suffix}</div>", unsafe_allow_html=True)

        # 32 Datapunkter uppdelade i kategorier
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Anfall & Avslut")
            stat_row("xG", r['xG Hemma'], r['xG Borta'])
            stat_row("Totala Skott", int(r['Total Skott Hemma']), int(r['Total Skott Borta']))
            stat_row("Skott på mål", int(r['Skott på mål Hemma']), int(r['Skott på mål Borta']))
            stat_row("Skott Utanför", int(r['Skott Utanför Hemma']), int(r['Skott Utanför Borta']))
            stat_row("Blockerade Skott", int(r['Blockerade Skott Hemma']), int(r['Blockerade Skott Borta']))
            stat_row("Skott i Box", int(r['Skott i Box Hemma']), int(r['Skott i Box Borta']))
            stat_row("Skott utanför Box", int(r['Skott utanför Box Hemma']), int(r['Skott utanför Box Borta']))
            stat_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
            stat_row("Offside", int(r['Offside Hemma']), int(r['Offside Borta']))

        with col2:
            st.subheader("⚽ Speluppbyggnad")
            stat_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
            stat_row("Passningar", int(r['Passningar Hemma']), int(r['Passningar Borta']))
            stat_row("Passningssäkerhet", int(r['Passningssäkerhet Hemma']), int(r['Passningssäkerhet Borta']), True)
            
            st.write("")
            st.subheader("🛡️ Försvar & Disciplin")
            stat_row("Räddningar", int(r['Räddningar Hemma']), int(r['Räddningar Borta']))
            stat_row("Fouls", int(r['Fouls Hemma']), int(r['Fouls Borta']))
            stat_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))
            stat_row("Röda Kort", int(r['Röda Kort Hemma']), int(r['Röda Kort Borta']))
            stat_row("Straffar", int(r['Straffar Hemma']), int(r['Straffar Borta']))

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        # --- TAB 1: MATCHER ---
        with tab1:
            st.header("Matchcenter")
            m_col, s_col = st.columns(2)
            mode = m_col.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            search = s_col.text_input("Sök lag:", "", key="search_main")
            
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            if search:
                d_df = d_df[(d_df['response.teams.home.name'].str.contains(search, case=False)) | (d_df['response.teams.away.name'].str.contains(search, case=False))]
            
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1.2]) # Lite bredare för knappen
                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Senaste resultaten" else "VS"
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]} <img src="{r["response.teams.home.logo"]}" width="18"></div><div style="background:#222; color:white; padding:2px 8px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div><div style="flex:1; text-align:left; font-weight:bold;"><img src="{r["response.teams.away.logo"]}" width="18"> {r["response.teams.away.name"]}</div></div>', unsafe_allow_html=True)
                with c_b:
                    if mode=="Senaste resultaten" and st.button("Statistik", key=f"b{idx}"):
                        st.session_state.view_match = r
                        st.rerun()

        # TAB 2 & 3: LÄMNAS ORÖRDA ENLIGT INSTRUKTION
        with tab2:
            st.header("🛡️ Laganalys")
            # ... (Kod för laganalys finns kvar här i den faktiska filen)
        
        with tab3:
            st.header("⚖️ Domaranalys")
            # ... (Kod för domaranalys finns kvar här i den faktiska filen)

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None:
                st.dataframe(standings_df, hide_index=True, use_container_width=True)
else:
    st.error("Kunde inte ladda data.")
