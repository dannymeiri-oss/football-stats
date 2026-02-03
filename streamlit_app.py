import streamlit as st
import pandas as pd
from datetime import datetime
import traceback

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS - Rensad från mörka fält som spökade
st.markdown("""
    <style>
    .score-big { font-size: 30px; font-weight: 900; color: #ff4b4b; text-align: center; margin: 0; }
    .vs-text { text-align: center; color: #888; font-size: 14px; }
    .league-name { color: #666; font-size: 12px; font-weight: bold; }
    .date-badge { background: #f0f2f6; padding: 2px 8px; border-radius: 4px; color: #333; font-size: 12px; }
    .match-card { 
        padding: 15px; 
        border-bottom: 1px solid #eee; 
    }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        
        if 'response.fixture.date' in df.columns:
            # Skapa ett rent datum-objekt
            df['dt_object'] = pd.to_datetime(df['response.fixture.date'], errors='coerce').dt.tz_localize(None)
            # Snyggt datum för visning
            df['visnings_datum'] = df['dt_object'].dt.strftime('%d %b %Y')
            # Tid för visning
            df['visnings_tid'] = df['dt_object'].dt.strftime('%H:%M')
        
        now = datetime.now()
        goal_col = 'response.goals.home'
        if goal_col in df.columns:
            goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
            df['spelad'] = (goals_numeric.notna()) | (df['dt_object'] < now)
        else:
            df['spelad'] = False
            
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

try:
    df_raw = load_data()

    if 'error' in df_raw.columns:
        st.error(f"Datafel: {df_raw['error'].iat[0]}")
        st.stop()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        with st.sidebar:
            st.header("Inställningar")
            sida = st.radio("Kategori:", ["Kommande", "Historik"])
            search = st.text_input("Sök lag...")

        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()
        
        if search:
            mask = df_view['response.teams.home.name'].str.contains(search, case=False, na=False) | \
                   df_view['response.teams.away.name'].str.contains(search, case=False, na=False)
            df_view = df_view[mask]

        if not df_view.empty:
            # Sortering: Kommande (tidigast först), Historik (senaste först)
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            
            for i, row in df_view.iterrows():
                st.markdown('<div class="match-card">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 3, 1])
                
                with col1:
                    if pd.notna(row.get('response.league.logo')):
                        st.image(row['response.league.logo'], width=30)
                
                with col2:
                    st.write(f"**{row.get('response.teams.home.name','')}**")
                    st.markdown(f"<span class='league-name'>{row.get('response.league.name','')}</span>", unsafe_allow_html=True)
                
                with col3:
                    h_g = row.get('response.goals.home')
                    if pd.notna(h_g) and str(h_g).strip() != "":
                        st.markdown(f"<div class='score-big'>{int(float(h_g))} - {int(float(row['response.goals.away']))}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='vs-text'>VS<br>{row.get('visnings_tid','--:--')}</div>", unsafe_allow_html=True)
                
                with col4:
                    st.write(f"**{row.get('response.teams.away.name','')}**")
                    st.markdown(f"<span class='date-badge'>{row.get('visnings_datum','')}</span>", unsafe_allow_html=True)
                
                with col5:
                    # Garanterat unik nyckel för knappen med index + lagnamn
                    if st.button("Analys", key=f"btn_{i}_{row.get('response.teams.home.id', i)}"):
                        st.session_state.selected_match = row.to_dict()
                        st.session_state.page = 'details'
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Inga matcher hittades.")

    # --- SIDA 2: ANALYSVY ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        if st.button("← Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
            
        st.divider()
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            st.image(m.get('response.teams.home.logo',''), width=80)
            st.subheader(m.get('response.teams.home.name',''))
        with c2:
            h_g = m.get('response.goals.home')
            if pd.notna(h_g):
                st.markdown(f"<div class='score-big'>{int(float(h_g))} - {int(float(m['response.goals.away']))}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='vs-text'><strong>VS</strong></div>", unsafe_allow_html=True)
        with c3:
            st.image(m.get('response.teams.away.logo',''), width=80)
            st.subheader(m.get('response.teams.away.name',''))
            
        st.divider()
        tab1, tab2, tab3 = st.tabs(["📊 Statistik", "🔄 Inbördes", "📋 Info"])
        
        with tab1:
            st.info("Statistik kommer visas här.")

        with tab2:
            st.subheader("Inbördes möten")
            t1 = m['response.teams.home.name']
            t2 = m['response.teams.away.name']
            
            h2h = df_raw[(df_raw['spelad'] == True) & (
                ((df_raw['response.teams.home.name'] == t1) & (df_raw['response.teams.away.name'] == t2)) |
                ((df_raw['response.teams.home.name'] == t2) & (df_raw['response.teams.away.name'] == t1))
            )].sort_values(by='dt_object', ascending=False)
            
            if not h2h.empty:
                for _, hm in h2h.iterrows():
                    col_date, col_m, col_r = st.columns([1, 3, 1])
                    # Här använder vi nu den fixade datum-strängen
                    col_date.write(hm['visnings_datum'])
                    col_m.write(f"{hm['response.teams.home.name']} - {hm['response.teams.away.name']}")
                    col_r.markdown(f"**{int(float(hm['response.goals.home']))} - {int(float(hm['response.goals.away']))}**")
                    st.divider()
            else:
                st.write("Ingen tidigare historik hittades.")

        with tab3:
            st.write(f"**Arena:** {m.get('response.fixture.venue.name','N/A')}")
            st.write(f"**Domare:** {m.get('response.fixture.referee','N/A')}")

except Exception:
    st.error("Ett oväntat fel uppstod.")
    st.text(traceback.format_exc())
