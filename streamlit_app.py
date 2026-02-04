import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats 2026", layout="wide")

# Länkar till ditt Google Sheet
BASE_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid=0"
# Byt ut DITT_STANDINGS_GID mot det faktiska numret för din tabell-flik
STANDINGS_URL = f"{BASE_URL}&gid=DITT_STANDINGS_GID" 

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except Exception as e:
        return None

def clean_stats(data):
    if data is None: return None
    # Säkerställ att datumkolumnen är i rätt format
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    
    # Fixa saknade kolumner för att undvika KeyError
    important_cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
                      'Gula kort Hemma', 'Gula Kort Borta', 'Straffar Hemma', 'Straffar Borta']
    for col in important_cols:
        if col not in data.columns:
            data[col] = 0
            
    return data

# --- Ladda data ---
df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

# --- SESSION STATE FÖR NAVIGATION ---
if 'view_match' not in st.session_state:
    st.session_state.view_match = None

# --- FUNKTION: ANALYSSIDAN (När man klickat på en match) ---
def render_match_analysis(row):
    if st.button("← Tillbaka till matchlistan"):
        st.session_state.view_match = None
        st.rerun()

    h_team = row['response.teams.home.name']
    a_team = row['response.teams.away.name']
    h_logo = row.get('response.teams.home.logo', '')
    a_logo = row.get('response.teams.away.logo', '')
    
    st.title(f"{h_team} vs {a_team}")
    st.write(f"📅 {row['datetime'].strftime('%Y-%m-%d %H:%M')} | ⚖️ Domare: {row.get('response.fixture.referee', 'Okänd')}")
    
    c1, c2, c3 = st.columns([1, 0.5, 1])
    with c1:
        if h_logo: st.image(h_logo, width=80)
        st.metric("xG", row['xG Hemma'])
        st.metric("Bollinnehav", f"{int(row['Bollinnehav Hemma'])}%")
    with c2:
        st.markdown(f"<h1 style='text-align:center;'>{int(row['response.goals.home'])} - {int(row['response.goals.away'])}</h1>", unsafe_allow_html=True)
    with c3:
        if a_logo: st.image(a_logo, width=80)
        st.metric("xG", row['xG Borta'])
        st.metric("Bollinnehav", f"{int(row['Bollinnehav Borta'])}%")

# --- HUVUDLAYOUT ---
if df is not None:
    if st.session_state.view_match is not None:
        render_match_analysis(st.session_state.view_match)
    else:
        tab1, tab2, tab3 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "🏆 Tabell"])

        with tab1:
            st.header("Matchcenter")
            
            # FILTRERING: Nästa 50 (NS) vs Senaste Resultat (FT)
            mode = st.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)

            if mode == "Nästa 50 matcher":
                # Endast matcher som inte startat (NS), sorterade närmast i tid först
                display_df = df[df['response.fixture.status.short'].isin(['NS', 'TBD'])].sort_values('datetime', ascending=True).head(50)
            else:
                # Endast spelade matcher (FT), sorterade senaste först
                display_df = df[df['response.fixture.status.short'].isin(['FT', 'AET', 'PEN'])].sort_values('datetime', ascending=False).head(50)

            if display_df.empty:
                st.info("Inga matcher hittades för detta val.")
            else:
                for index, row in display_df.iterrows():
                    col_m, col_btn = st.columns([5, 1])
                    
                    tid = row['datetime'].strftime('%d %b %H:%M') if pd.notnull(row['datetime']) else "Tid saknas"
                    h_team = row['response.teams.home.name']
                    a_team = row['response.teams.away.name']
                    h_logo = row.get('response.teams.home.logo', '')
                    a_logo = row.get('response.teams.away.logo', '')
                    
                    # Om matchen är spelad, visa resultat, annars "VS"
                    score = f"{int(row['response.goals.home'])} - {int(row['response.goals.away'])}" if mode == "Senaste resultaten" else "VS"

                    with col_m:
                        st.markdown(f"""
                        <div style="background:white; padding:12px; border-radius:10px; border:1px solid #eee; margin-bottom:8px; display:flex; align-items:center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="width:100px; color:#666; font-size:0.85em;">{tid}</div>
                            <div style="flex:1; text-align:right; font-weight:bold; padding-right:10px;">
                                {h_team} <img src="{h_logo}" width="20" style="vertical-align:middle; margin-left:5px;">
                            </div>
                            <div style="background:#333; color:white; padding:4px 12px; border-radius:4px; min-width:65px; text-align:center; font-weight:bold;">{score}</div>
                            <div style="flex:1; text-align:left; font-weight:bold; padding-left:10px;">
                                <img src="{a_logo}" width="20" style="vertical-align:middle; margin-right:5px;"> {a_team}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_btn:
                        if mode == "Senaste resultaten":
                            if st.button("Analys", key=f"anl_{index}"):
                                st.session_state.view_match = row
                                st.rerun()
                        else:
                            st.button("H2H", key=f"h2h_{index}", disabled=True)

        with tab2:
            st.write("Välj ett lag i listan för att se deras genomsnittliga stats.")
            # Här kan du lägga in din tidigare lagstatistik-kod

        with tab3:
            st.header("🏆 Tabell")
            if standings_df is not None:
                st.dataframe(standings_df, hide_index=True)
