import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för det visuella
st.markdown("""
    <style>
    .score-big { font-size: 35px; font-weight: 900; color: #ff4b4b; text-align: center; }
    .vs-text { text-align: center; color: #888; font-size: 14px; }
    .league-header { color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    .date-text { color: #aaa; font-size: 14px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Skapa datum-objekt
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date']).dt.tz_localize(None)
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    # Logik för att avgöra om matchen är spelad
    now = datetime.now()
    goal_col = 'response.goals.home'
    if goal_col in df.columns:
        goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
        df['spelad'] = (goals_numeric.notna()) | (df['dt_object'] < now)
    else:
        df['spelad'] = False
    return df

try:
    df_raw = load_data()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_match' not in st.session_state:
        st.session_state.selected_match = None

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        sida = st.sidebar.radio("Visa matcher:", ["Kommande", "Historik"])
        search = st.sidebar.text_input("Sök lag...")

        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()
        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        if not df_view.empty:
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            
            for i, match in df_view.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([0.8, 3, 2, 3, 1.5])
                    with col1:
                        st.image(match['response.league.logo'], width=40)
                    with col2:
                        st.write(f"**{match['response.teams.home.name']}**")
                    with col3:
                        h_goals = match.get('response.goals.home')
                        if pd.notna(h_goals) and str(h_goals).strip() != "":
                            st.markdown(f"<div class='score-big'>{int(h_goals)} - {int(match['response.goals.away'])}</div>", unsafe_allow_html=True)
                        else:
                            tid = match['Datum'].split(' ')[3] if ' ' in str(match['Datum']) else "--:--"
                            st.markdown(f"<div class='vs-text'>VS<br
