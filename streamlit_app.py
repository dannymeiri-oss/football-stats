import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# Länkar till ditt Google Sheet
BASE_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid=0"
# KOM IHÅG: Byt ut 123456789 mot ditt korrekta GID för Standings-fliken
STANDINGS_URL = f"{BASE_URL}&gid=123456789" 

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return None

def clean_stats(data):
    if data is None: return None
    
    # 1. Hantera Datum
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    
    # 2. Säkerställ att alla kolumner finns för att undvika krascher (viktigt för domarstatistiken)
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Straffar Hemma', 'Straffar Borta',
        'Fouls Hemma', 'Fouls Borta', 'response.goals.home', 'response.goals.away',
        'response.fixture.referee', 'response.fixture.status.short',
        'Skott på mål Hemma', 'Skott på mål Borta', 'Hörnor Hemma', 'Hörnor Borta'
    ]
    
    for col in cols_to_ensure:
        if col not in data.columns:
            data[col] = 0
        elif col not in ['response.fixture.referee', 'response.fixture.status.short']:
            # Tvätta numerisk data
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            
    # 3. Tvätta domarnamn
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
            
    return data

# --- LADDA DATA ---
df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

# --- NAVIGATION (SESSION STATE) ---
if 'view_match' not in st.session_state:
    st.session_state.view_match = None

# --- FUNKTION: ANALYSSIDAN (DETALJVY) ---
def render_match_analysis(row):
    if st.button("← Tillbaka till listan"):
        st.session_state.view_match = None
        st.rerun()
    
    h_team = row['response.teams.home.name']
    a_team = row['response.teams.away.name']
    h_logo = row.get('response.teams.home.logo', '')
    a_logo = row.get('response.teams.away.logo', '')
    
    st.title(f"{h_team} {int(row['response.goals.home'])} - {int(row['response.goals.away'])} {a_team}")
    st.write(f"📅 {row['datetime'].strftime('%d %b %Y | %H:%M')} | ⚖️ Domare: {row['ref_clean']}")
    
    st.divider()
    
    # xG och Bollinnehav Highlights
    c1, c2, c3 = st.columns([1, 0.5, 1])
    with c1:
        if h_logo: st.image(h_logo, width=100)
        st.metric("Expected Goals (xG)", row['xG Hemma'])
        st.metric("Bollinnehav", f"{int(row['Bollinnehav Hemma'])}%")
    with c2:
        st.markdown("<h1 style='text-align:center; padding-top:50px;'>VS</h1>", unsafe_allow_html=True)
    with c3:
        if a_logo: st.image(a_logo, width=100)
        st.metric("Expected Goals (xG)", row['xG Borta'])
        st.metric("Bollinnehav", f"{int(row['Bollinnehav Borta'])}%")

    st.divider()
    
    # Detaljerad Matchstatistik
    st.subheader("Matchstatistik")
    detail_stats = {
        "Skott på mål": ('Skott på mål Hemma', 'Skott på mål Borta'),
        "Hörnor": ('Hörnor Hemma', 'Hörnor Borta'),
        "Fouls": ('Fouls Hemma', 'Fouls Borta'),
        "Gula Kort": ('Gula kort Hemma', 'Gula Kort Borta'),
        "Straffar": ('Straffar Hemma', 'Straffar Borta')
    }
    
    for label, (h_col, a_col) in detail_stats.items():
        h_val = int(row[h_col])
        a_val = int(row[a_col])
        st.write(f"**{label}**")
        st.write(f"{h_val} — {a_val}")
        # Progress bar för visuell jämförelse
        total = h_val + a_val
        st.progress(h_val / total if total > 0 else 0.5)

# --- HUVUDLAYOUT ---
if df is not None:
    # Visa analyssidan om en match är vald
    if st.session_state.view_match is not None:
        render_match_analysis(st.session_state.view_match)
    
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "📊 Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        # --- TAB 1: MATCHER (KOMMANDE & SPELADE) ---
        with tab1:
            st.header("Matchcenter")
            mode = st.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            
            if mode == "Nästa 50 matcher":
                # Filtrera på NS (Not Started) och sortera närmast i tid först
                display_df = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime', ascending=True).head(50)
            else:
                # Filtrera på FT (Full Time) och sortera senaste först
                display_df = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False).head(50)

            if display_df.empty:
                st.info("Inga matcher hittades för det valda filtret.")
            else:
                for index, row in display_df.iterrows():
                    col_info, col_btn = st.columns([5, 1])
                    
                    tid = row['datetime'].strftime('%d %b %H:%M') if pd.notnull(row['datetime']) else "TBD"
                    h_team = row['response.teams.home.name']
                    a_team = row['response.teams.away.name']
                    h_logo = row.get('response.teams.home.logo', '')
                    a_logo = row.get('response.teams.away.logo', '')
                    
                    score_txt = f"{int(row['response.goals.home'])} - {int(row['response.goals.away'])}" if mode == "Senaste resultaten" else "VS"

                    with col_info:
                        st.markdown(f"""
                        <div style="background:white; padding:12px; border-radius:10px; border:1px solid #eee; margin-bottom:8px; display:flex; align-items:center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="width:100px; color:#666; font-size:0.85em;">{tid}</div>
                            <div style="flex:1; text-align:right; font-weight:bold; padding-right:12px;">
                                {h_team} <img src="{h_logo}" width="22" style="vertical-align:middle; margin-left:8px;">
                            </div>
                            <div style="background:#222; color:white; padding:4px 12px; border-radius:5px; min-width:65px; text-align:center; font-family:monospace;">
                                {score_txt}
                            </div>
                            <div style="flex:1; text-align:left; font-weight:bold; padding-left:12px;">
                                <img src="{a_logo}" width="22" style="vertical-align:middle; margin-right:8px;"> {a_team}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_btn:
                        if mode == "Senaste resultaten":
                            if st.button("Analys", key=f"anl_{index}"):
                                st.session_state.view_match = row
                                st.rerun()
                        else:
                            st.button("H2H", key=f"h2h_{index}", disabled=True)

        # --- TAB 2: LAGSTATISTIK ---
        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj ett lag:", all_teams)
            
            if sel_team:
                t_df = df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)]
                st.subheader(f"Statistik för {sel_team}")
                st.write(f"Baserat på {len(t_df)} spelade matcher i databasen.")
                
                # Här kan du lägga till medelvärdesberäkningar för laget
                avg_goals = (t_df['response.goals.home'].mean() + t_df['response.goals.away'].mean()) / 2
                st.metric("Snitt mål per match", round(avg_goals, 2))

        # --- TAB 3: DOMARANALYS ---
        with tab3:
            st.header("⚖️ Domaranalys")
            # Filtrera bort domare som är 0 eller tomma
            valid_refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            
            sel_ref = st.selectbox("Välj domare:", valid_refs)
            
            if sel_ref:
                ref_df = df[df['ref_clean'] == sel_ref]
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Matcher", len(ref_df))
                
                yellows = (ref_df['Gula kort Hemma'] + ref_df['Gula Kort Borta']).mean()
                fouls = (ref_df['Fouls Hemma'] + ref_df['Fouls Borta']).mean()
                pens = (ref_df['Straffar Hemma'] + ref_df['Straffar Borta']).sum()
                
                m2.metric("Gula kort / match", round(yellows, 2))
                m3.metric("Fouls / match", round(fouls, 2))
                m4.metric("Straffar totalt", int(pens))
                
                st.divider()
                st.subheader(f"Senaste matcher dömda av {sel_ref}")
                st.dataframe(ref_df[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.status.short']], hide_index=True)

        # --- TAB 4: TABELL ---
        with tab4:
            st.header("🏆 Aktuell Serietabell")
            if standings_df is not None:
                st.dataframe(standings_df, use_container_width=True, hide_index=True)
            else:
                st.info("Tabell-data kunde inte läsas in. Kontrollera GID för Standings-fliken.")

else:
    st.error("Kunde inte ladda data från Google Sheets. Kontrollera att din länk är korrekt och att arket är publikt.")
