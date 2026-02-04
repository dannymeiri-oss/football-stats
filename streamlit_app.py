import streamlit as st
import pandas as pd

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats 2026", layout="wide")

# Länkar till ditt Google Sheet
# Byt ut DITT_STANDINGS_GID mot numret i URL:en (t.ex. gid=123456789)
BASE_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid=0"
STANDINGS_URL = f"{BASE_URL}&gid=DITT_STANDINGS_GID" 

@st.cache_data(ttl=300)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except Exception as e:
        return None

def clean_stats(data):
    if data is None: return None
    # Rensa bort rader som saknar match-ID
    data = data.dropna(subset=['response.fixture.id'])
    
    # Lista på kolumner som ska tvättas och göras om till siffror
    cols_to_clean = [
        'response.goals.home', 'response.goals.away', 'xG Hemma', 'xG Borta',
        'Gula kort Hemma', 'Gula Kort Borta', 'Röda Kort Hemma', 'Röda Kort Borta',
        'Bollinnehav Hemma', 'Bollinnehav Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
        'Hörnor Hemma', 'Hörnor Borta', 'Fouls Hemma', 'Fouls Borta',
        'Total Skott Hemma', 'Total Skott Borta', 'Passningar Hemma', 'Passningar Borta', 
        'Straffar Hemma', 'Straffar Borta'
    ]
    
    for col in cols_to_clean:
        if col in data.columns:
            # Ersätt komma med punkt och ta bort allt som inte är siffror
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        else:
            data[col] = 0
    return data

# Ladda in data
df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if df is not None:
    tab1, tab2, tab3, tab4 = st.tabs(["⚽ Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

    # --- FLIK 1: MATCHER ---
    with tab1:
        st.header("Matchanalys & Historik")
        c1, c2 = st.columns([2, 1])
        with c1:
            search_query = st.text_input("Sök lag i matchlistan:", "")
        with c2:
            sort_order = st.selectbox("Sortera efter datum:", ["Senaste först", "Äldsta först"])

        m_df = df.copy()
        if search_query:
            m_df = m_df[(m_df['response.teams.home.name'].str.contains(search_query, case=False)) | 
                        (m_df['response.teams.away.name'].str.contains(search_query, case=False))]
        
        m_df = m_df.sort_values('response.fixture.date', ascending=(sort_order == "Äldsta först"))

        if not m_df.empty:
            # Snabb-statistik för urvalet
            s1, s2, s3, s4 = st.columns(4)
            total_m = len(m_df)
            home_wins = len(m_df[m_df['response.goals.home'] > m_df['response.goals.away']])
            away_wins = len(m_df[m_df['response.goals.away'] > m_df['response.goals.home']])
            over25 = len(m_df[(m_df['response.goals.home'] + m_df['response.goals.away']) > 2.5])
            
            s1.metric("Antal matcher", total_m)
            s2.metric("Hemmavinst %", f"{(home_wins/total_m*100):.1f}%")
            s3.metric("Bortavinst %", f"{(away_wins/total_m*100):.1f}%")
            s4.metric("Över 2.5 mål %", f"{(over25/total_m*100):.1f}%")
            st.divider()

            for _, row in m_df.head(30).iterrows():
                date = str(row['response.fixture.date']).split('T')[0]
                st.markdown(f"""
                <div style="background:#f9f9f9; padding:15px; border-radius:8px; border-left:5px solid #2e7d32; margin-bottom:10px; border:1px solid #eee;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="flex:1; text-align:right; font-weight:bold;">{row['response.teams.home.name']}</div>
                        <div style="flex:0.4; text-align:center; background:#333; color:white; padding:5px; border-radius:4px; margin:0 15px; font-size:1.1em;">
                            {int(row['response.goals.home'])} - {int(row['response.goals.away'])}
                        </div>
                        <div style="flex:1; text-align:left; font-weight:bold;">{row['response.teams.away.name']}</div>
                    </div>
                    <div style="display:flex; justify-content:center; gap:15px; margin-top:8px; font-size:0.8em; color:#666;">
                        <span>📅 {date}</span> | <span>📊 xG: {row.get('xG Hemma',0)} - {row.get('xG Borta',0)}</span> | <span>🚩 {int(row.get('Hörnor Hemma',0))}-{int(row.get('Hörnor Borta',0))}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- FLIK 2: LAGSTATISTIK ---
    with tab2:
        HOME_COL, AWAY_COL = 'response.teams.home.name', 'response.teams.away.name'
        all_teams = sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique())
        selected_team = st.selectbox("Välj lag för djupanalys:", all_teams)
        
        if selected_team:
            s_df = df[(df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)].sort_values('response.fixture.date', ascending=False)
            
            st.write(f"### Senaste 5 matcherna: {selected_team}")
            f_cols = st.columns(5)
            for i, (_, row) in enumerate(s_df.head(5).iterrows()):
                is_h = row[HOME_COL] == selected_team
                opp = row[AWAY_COL] if is_h else row[HOME_COL]
                gf = int(row['response.goals.home'] if is_h else row['response.goals.away'])
                ga = int(row['response.goals.away'] if is_h else row['response.goals.home'])
                color = '#2e7d32' if gf > ga else ('#d32f2f' if gf < ga else '#9e9e9e')
                res_txt = 'V' if gf > ga else ('F' if gf < ga else 'O')
                
                with f_cols[i]:
                    st.markdown(f"""
                    <div style="text-align:center; background:#f8f9fa; padding:10px; border-radius:8px; border:1px solid #ddd;">
                        <div style="background:{color}; color:white; border-radius:50%; width:35px; height:35px; display:flex; align-items:center; justify-content:center; margin:auto; font-weight:bold;">{res_txt}</div>
                        <div style="font-size:0.9em; font-weight:bold; margin-top:5px;">{gf} - {ga}</div>
                        <div style="font-size:0.7em; color:#666;">vs {opp[:12]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            # Här kan du lägga till dina render_lag_block funktioner från tidigare för genomsnittlig statistik

    # --- FLIK 3: DOMARE ---
    with tab3:
        REF_COL = 'response.fixture.referee'
        if REF_COL in df.columns:
            df[REF_COL] = df[REF_COL].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
            selected_ref = st.selectbox("Välj domare:", sorted(df[REF_COL].unique()))
            if selected_ref:
                r_df = df[df[REF_COL] == selected_ref]
                st.subheader(f"⚖️ Domarstatistik: {selected_ref}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Matcher", len(r_df))
                m2.metric("Gula/Match", (r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean().round(2))
                m3.metric("Fouls/Match", (r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean().round(2))
                m4.metric("Straffar Tot", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))

    # --- FLIK 4: TABELL ---
    with tab4:
        st.header("🏆 Aktuell Serietabell")
        if standings_df is not None:
            html_table = """
            <table style="width:100%; border-collapse: collapse; font-family: sans-serif;">
                <tr style="background-color: #f2f2f2; text-align: left; border-bottom: 2px solid #333;">
                    <th style="padding: 12px;">Rank</th>
                    <th>Lag</th>
                    <th>S</th>
                    <th>V</th>
                    <th>O</th>
                    <th>F</th>
                    <th>+/-</th>
                    <th>P</th>
                    <th>Form</th>
                </tr>
            """
            for _, row in standings_df.iterrows():
                # Form-styling (W -> Grön, L -> Röd)
                form_raw = str(row['Form']) if pd.notnull(row['Form']) else ""
                html_table += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 12px; font-weight: bold;">{row['Rank']}</td>
                    <td>
                        <img src="{row['Logo']}" width="22" style="vertical-align: middle; margin-right: 10px;">
                        {row['Team']}
                    </td>
                    <td>{row['Played']}</td>
                    <td>{row['Win']}</td>
                    <td>{row['Draw']}</td>
                    <td>{row['Lose']}</td>
                    <td>{row['GD']}</td>
                    <td><b>{row['Points']}</b></td>
                    <td style="font-size: 0.85em; letter-spacing: 1px;">{form_raw}</td>
                </tr>
                """
            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("Ingen tabell hittades. Kontrollera att fliken 'Standings' finns och att GID är korrekt.")
