import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för det visuella gränssnittet
st.markdown("""
    <style>
    .team-name { font-weight: bold; font-size: 18px; color: #FFFFFF; }
    .score-big { font-size: 40px; font-weight: 900; color: #ff4b4b; text-align: center; margin: 0; }
    .vs-text { text-align: center; color: #888; font-size: 14px; margin-top: 10px; }
    .league-header { color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date']).dt.tz_localize(None)
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    # Logik för att avgöra om match är spelad
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

    # Navigation State
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
                        st.markdown(f"<div style='text-align: right;' class='team-name'>{match['response.teams.home.name']}</div>", unsafe_allow_html=True)
                    
                    with col3:
                        h_goals = match.get('response.goals.home')
                        if pd.notna(h_goals) and str(h_goals).strip() != "":
                            st.markdown(f"<div class='score-big'>{int(h_goals)} - {int(match['response.goals.away'])}</div>", unsafe_allow_html=True)
                        else:
                            tid = match['Datum'].split(' ')[3] if ' ' in str(match['Datum']) else "--:--"
                            st.markdown(f"<div class='vs-text'>VS<br>{tid}</div>", unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"<div style='text-align: left;' class='team-name'>{match['response.teams.away.name']}</div>", unsafe_allow_html=True)
                    
                    with col5:
                        # Unik nyckel för att undvika Duplicate Key Error (Bild 2)
                        btn_key = f"analys_{i}_{match['response.teams.home.name'][:3]}"
                        if st.button("Analys", key=btn_key):
                            st.session_state.selected_match = match
                            st.session_state.page = 'details'
                            st.rerun()
                    st.divider()
        else:
            st.info(f"Inga matcher hittades i kategorin '{sida}'.")

    # --- SIDA 2: ANALYSVY (REN) ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        
        if st.button("⬅️ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
            
        st.markdown(f"<div class='league-header'>{m['response.league.name']} | {m['response.league.country']}</div>", unsafe_allow_html=True)
        st.divider()

        # Scoreboard Header
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            st.markdown(f"<div style='text-align: center;'><img src='{m['response.teams.home.logo']}' width='100'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;' class='team-name'>{m['response.teams.home.name']}</div>", unsafe_allow_html=True)
        with c2:
            if m['spelad'] and pd.notna(m.get('response.goals.home')):
                st.markdown(f"<div class='score-big'>{int(m['response.goals.home'])} - {int(m['response.goals.away'])}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='vs-text'><strong>VS</strong></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center; color: gray; font-size: 12px;'>{m['Datum']}</div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div style='text-align: center;'><img src='{m['response.teams.away.logo']}' width='100'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;' class='team-name'>{m['response.teams.away.name']}</div>", unsafe_allow_html=True)

        st.divider()
        
        # Tomma flikar redo för din statistik
        t1, t2, t3 = st.tabs(["📊 Statistik", "🔄 Inbördes", "📋 Info"])
        with t1:
            st.subheader("Matchanalys")
            st.info("Sidan är rensad och klar. Vilken statistik ska vi börja med?")
        with t3:
            st.write(f"**Arena:** {m.get('response.fixture.venue.name', 'Information saknas')}")
            st.write(f"**Domare:** {m.get('response.fixture.referee', 'Ej angiven')}")

except Exception as e:
    st.error(f"Ett tekniskt fel uppstod: {e}")
