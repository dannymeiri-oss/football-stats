import streamlit as st
import pandas as pd
from datetime import datetime
import traceback

# 1. Grundinställningar - Görs direkt
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS - Laddas in en gång
st.markdown("""
    <style>
    .score-big { font-size: 30px; font-weight: 900; color: #ff4b4b; text-align: center; margin: 0; }
    .vs-text { text-align: center; color: #888; font-size: 14px; }
    .league-name { color: #666; font-size: 12px; font-weight: bold; }
    .date-badge { background: #f0f2f6; padding: 2px 8px; border-radius: 4px; color: #333; font-size: 12px; }
    .match-card { padding: 15px; border-bottom: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

# OPTIMERING: Cacha hela den färdiga DataFrame:n
@st.cache_data(ttl=300) # Sparar i 5 minuter
def get_clean_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        
        if 'response.fixture.date' in df.columns:
            # Gör tunga datum-beräkningar här inne (bara en gång per 5 min)
            df['dt_object'] = pd.to_datetime(df['response.fixture.date'], errors='coerce').dt.tz_localize(None)
            df['visnings_datum'] = df['dt_object'].dt.strftime('%d %b %Y')
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
    df_raw = get_clean_data()

    if 'error' in df_raw.columns:
        st.error(f"Datafel: {df_raw['error'].iat[0]}")
        st.stop()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        with st.sidebar:
            st.header("Filter")
            sida = st.radio("Kategori:", ["Kommande", "Historik"])
            search = st.text_input("Sök lag...")

        # Snabb filtrering
        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()
        
        if search:
            mask = df_view['response.teams.home.name'].str.contains(search, case=False, na=False) | \
                   df_view['response.teams.away.name'].str.contains(search, case=False, na=False)
            df_view = df_view[mask]

        if not df_view.empty:
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            
            # Visa bara de första 50 matcherna för att öka hastigheten vid scroll
            for i, row in df_view.head(50).iterrows():
                with st.container():
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
                        if st.button("Analys", key=f"btn_{i}"):
                            st.session_state.selected_match = row.to_dict()
                            st.session_state.page = 'details'
                            st.rerun()
                    st.divider()
        else:
            st.info("Inga matcher hittades.")

    # --- SIDA 2: ANALYSVY ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        if st.button("← Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()
            
        st.divider()
        # Header, H2H osv (samma som förut men mer effektiv inläsning)
        # ... [Resten av analyskoden är densamma]
        st.write(f"### {m['response.teams.home.name']} vs {m['response.teams.away.name']}")
        
        tab1, tab2 = st.tabs(["📊 Statistik", "🔄 Inbördes"])
        with tab2:
            # Snabb H2H-sökning i redan cachad data
            t1, t2 = m['response.teams.home.name'], m['response.teams.away.name']
            h2h = df_raw[(df_raw['spelad'] == True) & (
                ((df_raw['response.teams.home.name'] == t1) & (df_raw['response.teams.away.name'] == t2)) |
                ((df_raw['response.teams.home.name'] == t2) & (df_raw['response.teams.away.name'] == t1))
            )].sort_values(by='dt_object', ascending=False)
            st.dataframe(h2h[['visnings_datum', 'response.teams.home.name', 'response.teams.away.name', 'response.goals.home', 'response.goals.away']])

except Exception:
    st.error("Ett fel uppstod.")
    st.text(traceback.format_exc())
