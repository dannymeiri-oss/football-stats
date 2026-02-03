import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

# CSS för att snygga till korten (Gör dem klickvänliga och moderna)
st.markdown("""
    <style>
    .match-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #333;
    }
    .team-name {
        font-weight: bold;
        font-size: 18px;
    }
    .score {
        font-size: 24px;
        font-weight: 900;
        color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date'])
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
    return df

try:
    df_raw = load_data()

    # --- SESSION STATE FÖR NAVIGATION ---
    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_match_data' not in st.session_state:
        st.session_state.selected_match_data = None

    # --- FUNKTION FÖR ATT GÅ TILL DETALJER ---
    def go_to_match(match_data):
        st.session_state.page = 'details'
        st.session_state.selected_match_data = match_data
        st.rerun()

    # --- FUNKTION FÖR ATT GÅ TILLBAKA ---
    def go_back():
        st.session_state.page = 'list'
        st.session_state.selected_match_data = None
        st.rerun()

    # --- SIDA 1: MATCHLISTAN (CARDS) ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        sida = st.sidebar.radio("Visa:", ["Historik", "Kommande"])
        search = st.sidebar.text_input("Sök lag...")

        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()
        df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))

        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        for _, match in df_view.iterrows():
            with st.container():
                # Vi skapar en snygg "rad" för varje match
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 3, 2])
                
                with col1:
                    st.image(match['response.league.logo'], width=40)
                
                with col2:
                    st.markdown(f"<div style='text-align: right;' class='team-name'>{match['response.teams.home.name']}</div>", unsafe_allow_html=True)
                
                with col3:
                    if match['spelad']:
                        st.markdown(f"<div style='text-align: center;' class='score'>{int(match['response.goals.home'])} - {int(match['response.goals.away'])}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: center; color: #888;'>VS<br><small>{match['Datum'].split(' ')[3]}</small></div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"<div style='text-align: left;' class='team-name'>{match['response.teams.away.name']}</div>", unsafe_allow_html=True)
                
                with col5:
                    if st.button("Analys", key=f"btn_{match['dt_object']}"):
                        go_to_match(match)
                
                st.divider()

    # --- SIDA 2: MATCHSIDA (DETALJER) ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match_data
        
        st.button("⬅️ Tillbaka", on_click=go_back)
        
        # Header med loggor och resultat
        st.markdown(f"### {m['response.league.name']} - {m['response.league.country']}")
        
        h_col, s_col, a_col = st.columns([2, 1, 2])
        with h_col:
            st.image(m['response.teams.home.logo'], width=120)
            st.header(m['response.teams.home.name'])
        with s_col:
            if m['spelad']:
                st.title(f"{int(m['response.goals.home'])} - {int(m['response.goals.away'])}")
            else:
                st.title("VS")
            st.write(m['Datum'])
        with a_col:
            st.image(m['response.teams.away.logo'], width=120)
            st.header(m['response.teams.away.name'])
        
        st.divider()

        # Statistik-sektion
        tab1, tab2, tab3 = st.tabs(["📊 Statistik", "📋 Laguppställning", "💡 Insikter"])
        
        with tab1:
            st.subheader("Matchstatistik")
            # Här bygger vi mätare för statistik senare
            st.info("Här kommer vi visualisera skott, bollinnehav och xG med snygga mätare.")
            st.write(m.dropna()) # Visa all rådata så länge

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
