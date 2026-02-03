import streamlit as st
import pandas as pd
from datetime import datetime

# Grundinställningar för appen
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# CSS för att skapa ett snyggt, app-liknande utseende
st.markdown("""
    <style>
    .team-name { font-weight: bold; font-size: 20px; }
    .score-big { font-size: 45px; font-weight: 900; color: #ff4b4b; margin: 0; }
    .vs-text { text-align: center; color: #888; font-size: 16px; margin-top: 15px; }
    .league-header { color: #888; font-size: 14px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Konvertera datum till Python-objekt för sortering och visning
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date']).dt.tz_localize(None)
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    # Logik för att skilja på spelade och kommande matcher
    now = datetime.now()
    goal_col = 'response.goals.home'
    if goal_col in df.columns:
        goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
        # En match räknas som spelad om det finns mål ELLER om tiden passerat
        df['spelad'] = (goals_numeric.notna()) | (df['dt_object'] < now)
    else:
        df['spelad'] = df['dt_object'] < now
        
    return df

try:
    df_raw = load_data()

    # Appens minne för sidnavigering
    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_match' not in st.session_state:
        st.session_state.selected_match = None

    # --- SIDA 1: HUVUDLISTAN ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        st.sidebar.title("Navigering")
        sida = st.sidebar.radio("Visa matcher:", ["Kommande", "Historik"])
        search = st.sidebar.text_input("Sök lag...")

        # Filtrera baserat på flik
        target_played = True if sida == "Historik" else False
        df_view = df_raw[df_raw['spelad'] == target_played].copy()

        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        if not df_view.empty:
            # Sortera (Kommande: närmast i tid först | Historik: senast spelade först)
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            
            for i, match in df_view.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 3, 2])
                    
                    with col1:
                        st.image(match['response.league.logo'], width=45)
                    
                    with col2:
                        st.markdown(f"<div style='text-align: right;' class='team-name'>{match['response.teams.home.name']}</div>", unsafe_allow_html=True)
                    
                    with col3:
                        home_goals = match.get('response.goals.home')
                        if pd.notna(home_goals) and str(home_goals).strip() != "":
                            st.markdown(f"<div style='text-align: center;' class='score-big'>{int(home_goals)} - {int(match['response.goals.away'])}</div>", unsafe_allow_html=True
