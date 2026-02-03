import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Football Stats Pro", layout="wide")

# CSS
st.markdown("""
    <style>
    .team-name { font-weight: bold; font-size: 18px; }
    .score { font-size: 24px; font-weight: 900; color: #ff4b4b; }
    .vs-text { text-align: center; color: #888; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Konvertera datum
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date']).dt.tz_localize(None)
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    # SMART LOGIK FÖR SPELAD VS KOMMANDE
    # En match är spelad OM det finns siffror i målkolumnen OCH matchen har startat
    now = datetime.now()
    goal_col = 'response.goals.home'
    
    if goal_col in df.columns:
        # Gör om mål till siffror (NaN om det är tomt/text)
        goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
        # Markera som spelad om mål finns ELLER om datumet är långt bak i tiden
        df['spelad'] = (goals_numeric.notna()) | (df['dt_object'] < now)
    else:
        df['spelad'] = df['dt_object'] < now
        
    return df

try:
    df_raw = load_data()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        st.sidebar.title("Inställningar")
        sida = st.sidebar.radio("Visa matcher:", ["Kommande", "Historik"])
        
        # DEBUG: Visa hur många matcher som finns i varje kategori (Hjälper oss hitta felet)
        num_kommande = len(df_raw[df_raw['spelad'] == False])
        num_historik = len(df_raw[df_raw['spelad'] == True])
        st.sidebar.write(f"📊 Info: {num_kommande} kommande, {num_historik} spelade.")

        search = st.sidebar.text_input("Sök lag...")

        # Välj filter
        target_played = True if sida == "Historik" else False
        df_view = df_raw[df_raw['spelad'] == target_played].copy()

        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        if not df_view.empty:
            # Sortering: Kommande = Tidigast först, Historik = Senaste först
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            
            for i, match in df_view.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 3, 2])
                    with col1:
                        st.image(match['response.league.logo'], width=40)
                    with col2:
                        st.markdown(f"<div style='text-align: right;' class='team-name'>{match['response.teams.home.name']}</div>", unsafe_allow_html=True)
                    with col3:
                        # Visa resultat om det finns, annars bara tid
                        home_goals = match.get('response.goals.home')
                        if pd.notna(home_goals) and str(home_goals).strip() != "":
                            st.markdown(f"<div style='text-align: center;' class='score'>{int(home_goals)} - {int(match['response.goals.away'])}</div>", unsafe_allow_html=True)
                        else:
                            tid = match['Datum'].split(' ')[3] if ' ' in str(match['Datum']) else "--:--"
                            st.markdown(f"<div class='vs-text'>VS<br>{tid}</div>", unsafe_allow_html=True)
                    with col4:
                        st.markdown(f"<div style='text-align: left;' class='team-name'>{match['response.teams.away.name']}</div>", unsafe_allow_html=True)
                    with col5:
                        if st.button("Analys", key=f"btn_{i}"):
                            st.session_state.selected_match = match
                            st.session_state.page = 'details'
                            st.rerun()
                    st.divider()
        else:
            st.warning(f"Inga matcher hittades under '{sida}'.")
            if st.button("Uppdatera data"):
                st.cache_data.clear()
                st.rerun()

    elif st.session_state.page == 'details':
        # (Matchrapport-kod här...)
        m = st.session_state.selected_match
        if st.button("⬅️ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
        st.header(f"{m['response.teams.home.name']} - {m['response.teams.away.name']}")
        st.write(m.dropna())

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
