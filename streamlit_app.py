import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för den snygga mallen
st.markdown("""
    <style>
    /* Bakgrund och kort */
    .main { background-color: #f8f9fa; }
    .stat-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    /* Mall-rader för statistik */
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
        background: #4e54f3; /* Den blå färgen från din bild */
        color: white;
        padding: 8px;
        margin: 0 10px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 12px;
        border-radius: 5px;
        letter-spacing: 1px;
    }
    .score-display {
        font-size: 48px;
        font-weight: 900;
        text-align: center;
        color: #1a1a1a;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    return df

# Funktion för att rita en rad i mallen
def draw_stat_item(label, h_val, a_val, is_percent=False):
    h_str = f"{h_val}%" if is_percent else f"{h_val}"
    a_str = f"{a_val}%" if is_percent else f"{a_val}"
    
    st.markdown(f"""
        <div class="stat-row">
            <div class="stat-val-box">{h_str}</div>
            <div class="stat-label">{label}</div>
            <div class="stat-val-box">{a_str}</div>
        </div>
    """, unsafe_allow_html=True)

try:
    df = load_data()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        
        mode = st.sidebar.radio("Visa:", ["Kommande", "Historik"])
        search = st.sidebar.text_input("Sök lag...")
        
        # Filtrering baserat på målkolumn (finns mål = historik)
        if mode == "Historik":
            display_df = df[df['response.goals.home'].notna()].sort_index(ascending=False)
        else:
            display_df = df[df['response.goals.home'].isna()]

        if search:
            display_df = display_df[display_df['response.teams.home.name'].str.contains(search, case=False, na=False) | 
                                    display_df['response.teams.away.name'].str.contains(search, case=False, na=False)]

        for i, row in display_df.head(30).iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([1, 4, 2, 1.5])
                with c1:
                    if pd.notna(row.get('response.league.logo')):
                        st.image(row['response.league.logo'], width=35)
                with c2:
                    st.markdown(f"**{row['response.teams.home.name']} - {row['response.teams.away.name']}**")
                    st.caption(f"{row.get('response.league.name', '')}")
                with c3:
                    if mode == "Historik":
                        st.markdown(f"**{int(row['response.goals.home'])} - {int(row['response.goals.away'])}**")
                    else:
                        st.write(str(row.get('response.fixture.date', ''))[11:16])
                with c4:
                    if st.button("Analys", key=f"btn_{i}"):
                        st.session_state.selected_match = row
                        st.session_state.page = 'details'
                        st.rerun()
                st.divider()

    # --- SIDA 2: ANALYSVY (DIN TEMPLATE) ---
    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        
        if st.button("⬅ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()

        # HEADER
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        h_logo, h_name = m.get('response.teams.home.logo',''), m.get('response.teams.home.name','')
        a_logo, a_name = m.get('response.teams.away.logo',''), m.get('response.teams.away.name','')
        
        header_col1, header_col2, header_col3 = st.columns([2, 2, 2])
        with header_col1:
            st.image(h_logo, width=80)
            st.subheader(h_name)
        with header_col2:
            h_g = m.get('response.goals.home')
            if pd.notna(h_g):
                st.markdown(f"<div class='score-display'>{int(h_g)} - {int(m['response.goals.away'])}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='score-display'>VS</div>", unsafe_allow_html=True)
            st.caption(f"<p style='text-align:center'>{m.get('response.league.name','')}</p>", unsafe_allow_html=True)
        with header_col3:
            st.image(a_logo, width=80)
            st.subheader(a_name)
        
        st.divider()

        # STATISTIK-MALLEN (Här mappar vi dina kolumner AV till CA)
        # Vi använder .get() och sätter 0 som default om data saknas
        st.markdown("### Matchstatistik")
        
        # Rad 1: Bollinnehav
        draw_stat_item("Bollinnehav", m.get('Ball Possession_H', 0), m.get('Ball Possession_B', 0), is_percent=True)
        
        # Rad 2: Skott på mål
        draw_stat_item("Skott på mål", m.get('Shots on Goal_H', 0), m.get('Shots on Goal_B', 0))
        
        # Rad 3: Totalt antal skott
        draw_stat_item("Totala skott", m.get('Total Shots_H', 0), m.get('Total Shots_B', 0))
        
        # Rad 4: Hörnor
        draw_stat_item("Hörnor", m.get('Corners_H', 0), m.get('Corners_B', 0))
        
        # Rad 5: Gula kort
        draw_stat_item("Gula kort", m.get('Yellow Cards_H', 0), m.get('Yellow Cards_B', 0))

        # Rad 6: Expected Goals (xG) - Den viktigaste!
        draw_stat_item("Expected Goals (xG)", m.get('expected_goals_H', 0), m.get('expected_goals_B', 0))

        st.markdown('</div>', unsafe_allow_html=True)

        # Tabbar för extra info
        t1, t2 = st.tabs(["H2H", "Info"])
        with t1:
            st.write("Tidigare möten visas här...")
        with t2:
            st.write(f"Arena: {m.get('response.fixture.venue.name','N/A')}")
            st.write(f"Domare: {m.get('response.fixture.referee','N/A')}")

except Exception as e:
    st.error("Kunde inte ladda matchcenter just nu.")
    st.write(e)
