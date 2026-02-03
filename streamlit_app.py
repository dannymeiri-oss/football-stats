import streamlit as st
import pandas as pd
from datetime import datetime
import traceback

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för det visuella gränssnittet
st.markdown("""
    <style>
    .score-big { font-size: 35px; font-weight: 900; color: #ff4b4b; text-align: center; margin: 0; }
    .vs-text { text-align: center; color: #888; font-size: 14px; }
    .league-header { color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    .date-text { color: #aaa; font-size: 13px; font-weight: bold; }
    .card { 
        background: #1e1e1e; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #333; 
        margin-bottom: 10px;
    }
    .team-name-list { font-size: 16px; font-weight: bold; color: white; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        
        # Datumhantering
        if 'response.fixture.date' in df.columns:
            dt = pd.to_datetime(df['response.fixture.date'], errors='coerce')
            try:
                dt = dt.dt.tz_localize(None)
            except:
                try: dt = dt.dt.tz_convert(None)
                except: pass
            df['dt_object'] = dt
            df['Datum'] = dt.dt.strftime('%d %b %Y %H:%M')
        else:
            df['dt_object'] = pd.NaT
            df['Datum'] = ""

        # Logik för spelad/kommande
        now = datetime.now()
        goal_col = 'response.goals.home'
        if goal_col in df.columns:
            goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
            df['spelad'] = (goals_numeric.notna()) | (df['dt_object'] < now)
        else:
            df['spelad'] = df['dt_object'] < now
            
        return df
    except Exception as e:
        return pd.DataFrame({"__load_error__": [str(e)]})

def go_back():
    st.session_state.page = 'list'
    st.session_state.selected_match = None

try:
    df_raw = load_data()

    if '__load_error__' in df_raw.columns:
        st.error(f"Kunde inte ladda data: {df_raw['__load_error__'].iat[0]}")
        st.stop()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        sida = st.sidebar.radio("Visa matcher:", ["Kommande", "Historik"])
        search = st.sidebar.text_input("Sök lag...")
        league_filter = st.sidebar.text_input("Filtrera liga")

        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()

        if league_filter:
            df_view = df_view[df_view['response.league.name'].str.contains(league_filter, case=False, na=False)]
        if search:
            mask = df_view.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            df_view = df_view[mask]

        if df_view.empty:
            st.info("Inga matcher matchar din sökning.")
        else:
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            for i, match in df_view.iterrows():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([0.8, 3, 2, 3, 1.5])
                
                with col1:
                    if pd.notna(match.get('response.league.logo')):
                        st.image(match['response.league.logo'], width=40)
                
                with col2:
                    st.markdown(f"<div class='team-name-list'>{match.get('response.teams.home.name','')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='league-header'>{match.get('response.league.name','')}</div>", unsafe_allow_html=True)
                
                with col3:
                    h_goals = match.get('response.goals.home')
                    if pd.notna(h_goals) and str(h_goals).strip() != "":
                        st.markdown(f"<div class='score-big'>{int(float(h_goals))} - {int(float(match['response.goals.away']))}</div>", unsafe_allow_html=True)
                    else:
                        tid = match['Datum'].split(' ')[3] if ' ' in str(match['Datum']) else "--:--"
                        st.markdown(f"<div class='vs-text'>VS<br>{tid}</div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"<div class='team-name-list'>{match.get('response.teams.away.name','')}</div>", unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"<div class='date-text'>{match.get('Datum','').split(' ')[0]} {match.get('Datum','').split(' ')[1]}</div>", unsafe_allow_html=True)
                    if st.button("Analys", key=f"btn_{i}"):
                        st.session_state.selected_match = match.to_dict()
                        st.session_state.page = 'detail'
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # --- SIDA 2: ANALYSVY ---
    elif st.session_state.page == 'detail':
        m = st.session_state.selected_match
        st.button("⬅ Tillbaka", on_click=go_back)
        
        # Header Scoreboard
        st.divider()
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            st.image(m.get('response.teams.home.logo',''), width=80)
            st.subheader(m.get('response.teams.home.name',''))
        with c2:
            h_g = m.get('response.goals.home')
            if pd.notna(h_g) and str(h_g).strip() != "":
                st.markdown(f"<div class='score-big'>{int(float(h_g))} - {int(float(m['response.goals.away']))}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='score-big'>VS</div>", unsafe_allow_html=True)
            st.caption(m.get('Datum',''))
        with c3:
            st.image(m.get('response.teams.away.logo',''), width=80)
            st.subheader(m.get('response.teams.away.name',''))
        
        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["📊 Statistik", "🔄 Inbördes", "📋 Info"])
        
        with tab1:
            st.subheader("Matchanalys")
            st.info("Statistikmoduler kommer snart...")

        with tab2:
            st.subheader("Tidigare möten")
            t1, t2 = m['response.teams.home.name'], m['response.teams.away.name']
            h2h = df_raw[(df_raw['spelad'] == True) & (
                ((df_raw['response.teams.home.name'] == t1) & (df_raw['response.teams.away.name'] == t2)) |
                ((df_raw['response.teams.home.name'] == t2) & (df_raw['response.teams.away.name'] == t1))
            )].sort_values(by='dt_object', ascending=False)
            
            if not h2h.empty:
                for _, hm in h2h.iterrows():
                    col_d, col_m, col_r = st.columns([1.5, 3, 1])
                    col_d.write(hm['dt_object'].strftime('%d %b %Y'))
                    col_m.write(f"{hm['response.teams.home.name']} - {hm['response.teams.away.name']}")
                    col_r.markdown(f"**{int(float(hm['response.goals.home']))} - {int(float(hm['response.goals.away']))}**")
                    st.divider()
            else:
                st.write("Ingen historik hittades.")

        with tab3:
            st.write(f"**Liga:** {m.get('response.league.name','')}")
            st.write(f"**Arena:** {m.get('response.fixture.venue.name','N/A')}")
            st.write(f"**Domare:** {m.get('response.fixture.referee','N/A')}")

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
    st.text(traceback.format_exc())
