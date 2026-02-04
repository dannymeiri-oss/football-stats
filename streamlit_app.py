import streamlit as st
import pandas as pd

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats 2026", layout="wide")

# Länkar till ditt Google Sheet
BASE_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid=0"
STANDINGS_URL = f"{BASE_URL}&gid=DITT_STANDINGS_GID" # Kom ihåg att ändra GID!

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

def clean_stats(data):
    if data is None: return None
    data = data.dropna(subset=['response.fixture.id'])
    cols = [
        'response.goals.home', 'response.goals.away', 'xG Hemma', 'xG Borta',
        'Gula kort Hemma', 'Gula Kort Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Skott på mål Hemma', 'Skott på mål Borta', 'Hörnor Hemma', 'Hörnor Borta', 
        'Fouls Hemma', 'Fouls Borta', 'Total Skott Hemma', 'Total Skott Borta',
        'Passningar Hemma', 'Passningar Borta', 'Straffar Hemma', 'Straffar Borta',
        'Skott i Box Hemma', 'Skott i Box Borta', 'Räddningar Hemma', 'Räddningar Borta'
    ]
    for col in cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    return data

df = clean_stats(load_data(RAW_DATA_URL))
standings_df = load_data(STANDINGS_URL)

# --- NAVIGATION LOGIK ---
if 'view_match' not in st.session_state:
    st.session_state.view_match = None

# --- FUNKTION FÖR ANALYSSIDAN ---
def render_match_analysis(match_row):
    if st.button("← Tillbaka till matchlistan"):
        st.session_state.view_match = None
        st.rerun()

    h_team = match_row['response.teams.home.name']
    a_team = match_row['response.teams.away.name']
    
    st.title(f"{h_team} {int(match_row['response.goals.home'])} - {int(match_row['response.goals.away'])} {a_team}")
    st.write(f"📅 Datum: {str(match_row['response.fixture.date']).split('T')[0]} | ⚖️ Domare: {match_row.get('response.fixture.referee', 'Okänd')}")
    
    st.divider()

    # Huvudstatistik
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.header(h_team)
        st.metric("Expected Goals (xG)", match_row['xG Hemma'])
        st.metric("Bollinnehav", f"{int(match_row['Bollinnehav Hemma'])}%")
    with col2:
        st.markdown("<br><br><h1 style='text-align:center;'>VS</h1>", unsafe_allow_html=True)
    with col3:
        st.header(a_team)
        st.metric("Expected Goals (xG)", match_row['xG Borta'])
        st.metric("Bollinnehav", f"{int(match_row['Bollinnehav Borta'])}%")

    st.divider()

    # Detaljerad tabelljämförelse
    stats_to_show = {
        "Skott på mål": ("Skott på mål Hemma", "Skott på mål Borta"),
        "Totala Skott": ("Total Skott Hemma", "Total Skott Borta"),
        "Hörnor": ("Hörnor Hemma", "Hörnor Borta"),
        "Fouls": ("Fouls Hemma", "Fouls Borta"),
        "Gula kort": ("Gula kort Hemma", "Gula Kort Borta"),
        "Räddningar": ("Räddningar Hemma", "Räddningar Borta"),
        "Passningar": ("Passningar Hemma", "Passningar Borta")
    }

    st.subheader("Matchstatistik")
    for label, (h_col, a_col) in stats_to_show.items():
        h_val = match_row[h_col]
        a_val = match_row[a_col]
        
        # Enkel visuell bar
        st.write(f"**{label}**")
        st.progress(h_val / (h_val + a_val) if (h_val + a_val) > 0 else 0.5)
        st.write(f"{int(h_val)} — {int(a_val)}")
        st.write("---")

# --- HUVUDPROGRAM ---
if df is not None:
    # Om en match är vald, visa bara analyssidan
    if st.session_state.view_match is not None:
        render_match_analysis(st.session_state.view_match)
    else:
        # Annars visa de vanliga flikarna
        tab1, tab2, tab3, tab4 = st.tabs(["⚽ Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        with tab1:
            st.header("Matchhistorik")
            search = st.text_input("Sök lag:", "")
            m_df = df.copy().sort_values('response.fixture.date', ascending=False)
            if search:
                m_df = m_df[(m_df['response.teams.home.name'].str.contains(search, case=False)) | 
                            (m_df['response.teams.away.name'].str.contains(search, case=False))]
            
            for index, row in m_df.head(30).iterrows():
                col_m, col_btn = st.columns([4, 1])
                
                h_name = row['response.teams.home.name']
                a_name = row['response.teams.away.name']
                h_goal = int(row['response.goals.home'])
                a_goal = int(row['response.goals.away'])
                date = str(row['response.fixture.date']).split('T')[0]

                with col_m:
                    st.markdown(f"""
                    <div style="background:#f9f9f9; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px;">
                        <b>{date}</b> | {h_name} {h_goal} - {a_goal} {a_name}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    if st.button("Visa analys", key=f"btn_{index}"):
                        st.session_state.view_match = row
                        st.rerun()

        # (De andra flikarna tab2, tab3, tab4 behålls som i förra koden)
        with tab2:
            st.write("Lagstatistik visas här...")
        with tab3:
            st.write("Domaranalys visas här...")
        with tab4:
            st.write("Tabell visas här...")
