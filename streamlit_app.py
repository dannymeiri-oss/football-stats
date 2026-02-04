import streamlit as st
import pandas as pd

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för den snygga mallen
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stat-row { display: flex; align-items: center; margin-bottom: 6px; }
    .stat-val-box { 
        flex: 1; text-align: center; padding: 6px; background: white; 
        border: 1px solid #eee; font-weight: bold; font-size: 15px; border-radius: 4px; 
    }
    .stat-label { 
        flex: 2; text-align: center; background: #4e54f3; color: white; 
        padding: 6px; margin: 0 10px; font-weight: bold; text-transform: uppercase; 
        font-size: 10px; border-radius: 4px; 
    }
    .score-display { font-size: 40px; font-weight: 900; text-align: center; }
    .section-header { 
        background: #eee; padding: 5px 15px; border-radius: 5px; 
        font-size: 14px; font-weight: bold; margin: 15px 0 10px 0; color: #333; 
    }
</style>
""", unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    if 'response.fixture.date' in df.columns:
        df['dt_obj'] = pd.to_datetime(df['response.fixture.date'], errors='coerce')
    return df

def draw_stat_item(label, h_val, a_val, is_percent=False):
    h_str = f"{h_val}%" if is_percent else f"{h_val}"
    a_str = f"{a_val}%" if is_percent else f"{a_val}"
    if "xG" in label:
        try:
            h_str = f"{float(h_val):.2f}"
            a_str = f"{float(a_val):.2f}"
        except: pass
    
    st.markdown(f'''
        <div class="stat-row">
            <div class="stat-val-box">{h_str}</div>
            <div class="stat-label">{label}</div>
            <div class="stat-val-box">{a_str}</div>
        </div>
    ''', unsafe_allow_html=True)

try:
    df = load_data()
    if 'page' not in st.session_state: st.session_state.page = 'list'

    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        mode = st.sidebar.radio("Visa matcher:", ["Kommande", "Senaste 30 Matcher"])
        
        if mode == "Senaste 30 Matcher":
            display_df = df[df['response.goals.home'].notna()]
            if 'dt_obj' in display_df.columns: display_df = display_df.sort_values(by='dt_obj', ascending=False)
            display_df = display_df.head(30)
        else:
            display_df = df[df['response.goals.home'].isna()]

        for i, row in display_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([1, 4, 2, 1.5])
                with c1:
                    if pd.notna(row.get('response.league.logo')): st.image(row['response.league.logo'], width=35)
                with c2:
                    st.markdown(f"**{row['response.teams.home.name']} - {row['response.teams.away.name']}**")
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

    elif st.session_state.page == 'details':
        m = st.session_state.selected_match
        if st.button("⬅ Tillbaka"):
            st.session_state.page = 'list'
            st.rerun()

        st.markdown('<div style="background:white; padding:20px; border-radius:15px; border:1px solid #eee;">', unsafe_allow_html=True)
        h_col, s_col, a_col = st.columns([2,3,2])
        with h_col:
            st.image(m.get('response.teams.home.logo',''), width=80)
            st.write(f"**{m['response.teams.home.name']}**")
        with s_col:
            h_g = m.get('response.goals.home')
            score = f"{int(h_g)} - {int(m['response.goals.away'])}" if pd.notna(h_g) else "VS"
            st.markdown(f"<div class='score-display'>{score}</div>", unsafe_allow_html=True)
        with a_col:
            st.image(m.get('response.teams.away.logo',''), width=80)
            st.write(f"**{m['response.teams.away.name']}**")

        st.markdown('<div class="section-header">ANFALL & CHANSER</div>', unsafe_allow_html=True)
        draw_stat_item("Expected Goals (xG)", m.get('xG Hemma', 0), m.get('xG Borta', 0))
        draw_stat_item("Skott på mål", m.get('Skott på mål Hemma', 0), m.get('Skott på mål Borta', 0))
        draw_stat_item("Totala Skott", m.get('Total Skott Hemma', 0), m.get('Total Skott Borta', 0))
        draw_stat_item("Skott Utanför", m.get('Skott Utanför Hemma', 0), m.get('Skott Utanför Borta', 0))
        draw_stat_item("Blockerade Skott", m.get('Blockerade Skott Hemma', 0), m.get('Blockerade Skott Borta', 0))
        draw_stat_item("Skott i Box", m.get('Skott i Box Hemma', 0), m.get('Skott i Box Borta', 0))
        draw_stat_item("Skott utanför Box", m.get('Skott utanför Box Hemma', 0), m.get('Skott utanför Box Borta', 0))
        
        st.markdown('<div class="section-header">SPELUPPBYGGNAD</div>', unsafe_allow_html=True)
        draw_stat_item("Bollinnehav", m.get('Bollinnehav Hemma', 0), m.get('Bollinnehav Borta', 0), is_percent=True)
        draw_stat_item("Passningar", m.get('Passningar Hemma', 0), m.get('Passningar Borta', 0))
        draw_stat_item("Passningssäkerhet", m.get('Passningssäkerhet Hemma', 0), m.get('Passningssäkerhet Borta', 0), is_percent=True)
        draw_stat_item("Hörnor", m.get('Hörnor Hemma', 0), m.get('Hörnor Borta', 0))
        draw_stat_item("Offside", m.get('Offside Hemma', 0), m.get('Offside Borta', 0))

        st.markdown('<div class="section-header">FÖRSVAR & DISCIPLIN</div>', unsafe_allow_html=True)
        draw_stat_item("Räddningar", m.get('Räddningar Hemma', 0), m.get('Räddningar Borta', 0))
        draw_stat_item("Fouls", m.get('Fouls Hemma', 0), m.get('Fouls Borta', 0))
        draw_stat_item("Gula Kort", m.get('Gula kort Hemma', 0), m.get('Gula Kort Borta', 0))
        draw_stat_item("Röda Kort", m.get('Röda Kort Hemma', 0), m.get('Röda Kort Borta', 0))
        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error("Kunde inte ladda matchdata.")
    st.write(e)
