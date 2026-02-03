import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

# CSS för ett mer modernt utseende
st.markdown("""
    <style>
    .team-name {
        font-weight: bold;
        font-size: 18px;
    }
    .score {
        font-size: 24px;
        font-weight: 900;
        color: #ff4b4b;
    }
    .vs-text {
        text-align: center;
        color: #888;
        font-size: 14px;
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

    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_match_data' not in st.session_state:
        st.session_state.selected_match_data = None

    # --- NAVIGATION ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        sida = st.sidebar.radio("Visa:", ["Historik", "Kommande"])
        search = st.sidebar.text_input("Sök lag...")

        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()
        df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))

        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

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
                        tid = match['Datum'].split(' ')[3] if ' ' in match['Datum'] else ""
                        st.markdown(f"<div class='vs-text'>VS<br>{tid}</div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"<div style='text-align: left;' class='team-name'>{match['response.teams.away.name']}</div>", unsafe_allow_html=True)
                
                with col5:
                    # FIX: Unikt ID för knappen genom att kombinera tid och lagnamn
                    btn_id = f"btn_{match['response.teams.home.name']}_{match['response.teams.away.name']}_{i}"
                    if st.button("Analys", key=btn_id):
                        st.session_state.selected_match_data = match
                        st.session_state.page = 'details'
                        st.rerun()
                
                st.divider()

    elif st.session_state.page == 'details':
        m = st.session_state.selected_match_data
        
        if st.button("⬅️ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
        
        st.markdown(f"### {m['response.league.name']} ({m['response.league.country']})")
        
        h_col, s_col, a_col = st.columns([2, 1, 2])
        with h_col:
            st.image(m['response.teams.home.logo'], width=100)
            st.subheader(m['response.teams.home.name'])
        with s_col:
            if m['spelad']:
                st.title(f"{int(m['response.goals.home'])} - {int(m['response.goals.away'])}")
            else:
                st.title("VS")
            st.caption(m['Datum'])
        with a_col:
            st.image(m['response.teams.away.logo'], width=100)
            st.subheader(m['response.teams.away.name'])
        
        st.divider()

        tab1, tab2 = st.tabs(["📊 Statistik", "📋 All Data"])
        with tab1:
            st.info("Här bygger vi mätare för skott, bollinnehav etc. när vi valt ut kolumnerna.")
        with tab2:
            st.write(m.dropna())

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
