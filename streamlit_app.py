import streamlit as st
import pandas as pd
from datetime import datetime

# Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# CSS för gränssnittet
st.markdown("""
    <style>
    .team-name { font-weight: bold; font-size: 20px; }
    .score-big { font-size: 45px; font-weight: 900; color: #ff4b4b; margin: 0; text-align: center; }
    .vs-text { text-align: center; color: #888; font-size: 16px; margin-top: 15px; }
    .league-header { color: #888; font-size: 14px; font-weight: bold; }
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
    
    goal_col = 'response.goals.home'
    if goal_col in df.columns:
        goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
        df['spelad'] = (goals_numeric.notna()) | (df['dt_object'] < datetime.now())
    else:
        df['spelad'] = False
    return df

try:
    df_raw = load_data()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_match' not in st.session_state:
        st.session_state.selected_match = None

    # --- SIDA 1: LISTAN ---
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
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 3, 2])
                    with col1:
                        st.image(match['response.league.logo'], width=45)
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
                        # Unikt ID för knappen för att undvika dubbletter
                        unique_key = f"btn_{i}_{match['response.teams.home.name'][:3]}"
                        if st.button("Analys", key=unique_key):
                            st.session_state.selected_match = match
                            st.session_state.page = 'details'
                            st.rerun()
                    st.divider()

    # --- SIDA 2: ANALYSSIDAN ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        if st.button("⬅️ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
            
        st.markdown(f"<div class='league-header'>{m['response.league.name']} | {m['response.league.country']}</div>", unsafe_allow_html=True)
        st.divider()

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

        st.
