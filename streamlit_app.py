import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

# Snyggare CSS
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
    
    # Skapa datum-objekt
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date'])
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    # Skapa 'spelad' baserat på om mål-kolumnen har siffror
    goal_col = 'response.goals.home'
    if goal_col in df.columns:
        # Vi gör om till numeriskt och kollar vad som inte är tomt
        df['spelad'] = pd.to_numeric(df[goal_col], errors='coerce').notna()
    else:
        df['spelad'] = False
    return df

try:
    df_raw = load_data()

    # Initiera sid-minne
    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    # --- SIDA 1: LISTAN ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        # Sidebar-val
        st.sidebar.title("Inställningar")
        sida = st.sidebar.radio("Visa matcher:", ["Kommande", "Historik"])
        search = st.sidebar.text_input("Sök lag...")

        # Filtrera baserat på val
        # Om vi väljer Historik vill vi ha spelad == True
        is_played = True if sida == "Historik" else False
        df_view = df_raw[df_raw['spelad'] == is_played].copy()

        # Sökning
        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # Sortering
        if not df_view.empty:
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            
            # Rendera korten
            for i, match in df_view.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 3, 2])
                    
                    with col1:
                        st.image(match['response.league.logo'], width=40)
                    
                    with col2:
                        st.markdown(f"<div style='text-align: right;' class='team-name'>{match['response.teams.home.name']}</div>", unsafe_allow_html=True)
                    
                    with col3:
                        if match['spelad']:
                            st.markdown(f"<div style='text-align: center;' class='score'>{int(match['response.goals.home'])} - {int(match['response.goals.away'])}</div>", unsafe_allow_html=True)
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
            st.warning(f"Inga matcher hittades i kategorin '{sida}'.")
            if st.button("Tvinga uppdatering"):
                st.cache_data.clear()
                st.rerun()

    # --- SIDA 2: DETALJER ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        
        if st.button("⬅️ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
            
        st.header(f"{m['response.teams.home.name']} vs {m['response.teams.away.name']}")
        st.write(f"**Liga:** {m['response.league.name']} | **Datum:** {m['Datum']}")
        
        # Här kan vi lägga in all statistik sen
        st.divider()
        st.subheader("Rådata för analys")
        st.write(m.dropna())

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
