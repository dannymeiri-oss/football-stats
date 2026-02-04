import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för din snygga mall (Matchar bilden du skickade)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stat-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .stat-val-box {
        flex: 1;
        text-align: center;
        padding: 8px;
        background: #ffffff;
        border: 1px solid #eee;
        font-weight: bold;
        font-size: 16px;
        border-radius: 5px;
    }
    .stat-label {
        flex: 2;
        text-align: center;
        background: #4e54f3;
        color: white;
        padding: 8px;
        margin: 0 10px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 11px;
        border-radius: 5px;
    }
    .score-display {
        font-size: 42px;
        font-weight: 900;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    # Försök konvertera datum för korrekt sortering
    if 'response.fixture.date' in df.columns:
        df['dt_obj'] = pd.to_datetime(df['response.fixture.date'], errors='coerce')
    return df

def draw_stat_item(label, h_val, a_val, is_percent=False):
    h_str = f"{h_val}%" if is_percent else f"{h_val}"
    a_str = f"{a_val}%" if is_percent else f"{a_val}"
    st.markdown(f'<div class="stat-row"><div class="stat-val-box">{h_str}</div><div class="stat-label">{label}</div><div class="stat-val-box">{a_str}</div></div>', unsafe_allow_html=True)

try:
    df = load_data()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        # Uppdaterat filternamn här
        mode = st.sidebar.radio("Visa matcher:", ["Kommande", "Senaste 30 Matcher"])
        search = st.sidebar.text_input("Sök lag...")
        
        # Logik för att visa Senaste 30 Matcher
        if mode == "Senaste 30 Matcher":
            # Filtrera fram de som har mål (spelade) och sortera på datum (senaste först)
            display_df = df[df['response.goals.home'].notna()]
            if 'dt_obj' in display_df.columns:
                display_df = display_df.sort_values(by='dt_obj', ascending=False)
            display_df = display_df.head(30)
        else:
            # Kommande matcher
            display_df = df[df['response.goals.home'].isna()]
            if 'dt_obj' in display_df.columns:
                display_df = display_df.sort_values(by='dt_obj', ascending=True)

        if search:
            display_df = display_df[display_df['response.teams.home.name'].str.contains(search, case=False, na=False) | 
                                    display_df['response.teams.away.name'].str.contains(search, case=False, na=False)]

        for i, row in display_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([1, 4, 2, 1.5])
                with c1:
                    if pd.notna(row.get('response.league.logo')):
                        st.image(row['response.league.logo'], width=35)
                with c2:
                    st.markdown(f"**{row['response.teams.home.name']} - {row['response.teams.away.name']}**")
                    st.caption(f"{row.get('response.league.name', '')}")
                with c3:
                    if mode == "Senaste 30 Matcher":
                        st.markdown(f"**{int(row['response.goals.home'])} - {int(row['response.goals.away'])}**")
                    else:
                        st.write(str(row.get('response.fixture.date', ''))[11:16])
                with c4:
                    if st.button("Analys", key=f"btn_{i}"):
                        st.session_state.selected_match = row
                        st.session_state.page = 'details'
                        st.rerun()
                st.divider()

    # --- SIDA 2: ANALYSVY ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        if st.button("⬅ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()

        st.markdown('<div style="background:white; padding:20px; border-radius:15px;">', unsafe_allow_html=True)
        col_h, col_s, col_a = st.columns([2,2,2])
        with col_h:
            st.image(m.get('response.teams.home.logo',''), width=70)
            st.write(f"**{m['response.teams.home.name']}**")
        with col_s:
            h_g = m.get('response.goals.home')
            score_txt = f"{int(h_g)} - {int(m['response.goals.away'])}" if pd.notna(h_g) else "VS"
            st.markdown(f"<div class='score-display'>{score_txt}</div>", unsafe_allow_html=True)
        with col_a:
            st.image(m.get('response.teams.away.logo',''), width=70)
            st.write(f"**{m['response.teams.away.name']}**")
        
        st.divider()
        st.write("### MATCH STATISTIC")
        
        # Här hämtas de 32 parametrarna vi nyss fixade i Google Scriptet
        # Se till att namnen matchar rubrikerna i din Raw Data-flik
        draw_stat_item("Ball Possession", m.get('Ball Possession_H', 0), m.get('Ball Possession_B', 0), is_percent=True)
        draw_stat_item("Shot on Target", m.get('Shots on Goal_H', 0), m.get('Shots on Goal_B', 0))
        draw_stat_item("Total Shots", m.get('Total Shots_H', 0), m.get('Total Shots_B', 0))
        draw_stat_item("Corners", m.get('Corners_H', 0), m.get('Corners_B', 0))
        draw_stat_item("Fouls", m.get('Fouls_H', 0), m.get('
