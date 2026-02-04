import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

# Dina Sheet-id:n
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" # Byt ut detta när din tabell är laddad

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

def clean_stats(data):
    if data is None: return None
    
    # Konvertera datum
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    
    # Kolumner som behövs för ALLA funktioner
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Straffar Hemma', 'Straffar Borta',
        'Fouls Hemma', 'Fouls Borta', 'response.goals.home', 'response.goals.away',
        'response.fixture.referee', 'response.fixture.status.short',
        'Skott på mål Hemma', 'Skott på mål Borta', 'Hörnor Hemma', 'Hörnor Borta',
        'response.teams.home.logo', 'response.teams.away.logo'
    ]
    
    for col in cols_to_ensure:
        if col not in data.columns:
            data[col] = "" if "logo" in col else 0
        elif col not in ['response.fixture.referee', 'response.fixture.status.short', 'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name']:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            
    # Skapa ren domarkolumn
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

# --- DATALADDNING ---
df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

# --- NAVIGATION ---
if 'view_match' not in st.session_state:
    st.session_state.view_match = None

# --- MATCHANALYS (DETALJVY) ---
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
    
    c1, c2, c3 = st.columns([1, 0.5, 1])
    with c1:
        if h_logo: st.image(h_logo, width=100)
        st.metric("Expected Goals (xG)", row['xG Hemma'])
        st.metric("Bollinnehav", f"{int(row['Bollinnehav Hemma'])}%")
    with c2:
        st.markdown("<h1 style='text-align:center; padding-top:40px;'>VS</h1>", unsafe_allow_html=True)
    with c3:
        if a_logo: st.image(a_logo, width=100)
        st.metric("Expected Goals (xG)", row['xG Borta'])
        st.metric("Bollinnehav", f"{int(row['Bollinnehav Borta'])}%")

    st.divider()
    st.subheader("Matchstatistik")
    detail_stats = {
        "Skott på mål": ('Skott på mål Hemma', 'Skott på mål Borta'),
        "Hörnor": ('Hörnor Hemma', 'Hörnor Borta'),
        "Fouls": ('Fouls Hemma', 'Fouls Borta'),
        "Gula Kort": ('Gula kort Hemma', 'Gula Kort Borta')
    }
    for label, (h, a) in detail_stats.items():
        st.write(f"**{label}**: {int(row[h])} — {int(row[a])}")
        total = row[h] + row[a]
        st.progress(row[h] / total if total > 0 else 0.5)

# --- HUVUDLAYOUT ---
if df is not None:
    if st.session_state.view_match is not None:
        render_match_analysis(st.session_state.view_match)
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "📊 Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        # --- TAB 1: MATCHER ---
        with tab1:
            st.header("Matchcenter")
            c_mode, c_search = st.columns([1, 1])
            with c_mode:
                mode = st.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            with c_search:
                search_query = st.text_input("Sök lag:", "")

            if mode == "Nästa 50 matcher":
                display_df = df[df['response.fixture.status.short'] == 'NS'].sort_values('datetime', ascending=True)
            else:
                display_df = df[df['response.fixture.status.short'] == 'FT'].sort_values('datetime', ascending=False)

            if search_query:
                display_df = display_df[(display_df['response.teams.home.name'].str.contains(search_query, case=False)) | 
                                        (display_df['response.teams.away.name'].str.contains(search_query, case=False))]

            for index, row in display_df.head(50).iterrows():
                c_info, c_btn = st.columns([5, 1])
                tid = row['datetime'].strftime('%d %b %H:%M') if pd.notnull(row['datetime']) else "TBD"
                res_txt = f"{int(row['response.goals.home'])} - {int(row['response.goals.away'])}" if mode == "Senaste resultaten" else "VS"
                h_logo = row.get('response.teams.home.logo', '')
                a_logo = row.get('response.teams.away.logo', '')
                
                with c_info:
                    st.markdown(f"""
                    <div style="background:white; padding:10px; border-radius:10px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                        <div style="width:90px; color:#777; font-size:0.8em;">{tid}</div>
                        <div style="flex:1; text-align:right; font-weight:bold; padding-right:10px;">
                            {row['response.teams.home.name']} <img src="{h_logo}" width="20" style="vertical-align:middle; margin-left:5px;">
                        </div>
                        <div style="background:#222; color:white; padding:3px 10px; border-radius:4px; min-width:60px; text-align:center; font-family:monospace;">{res_txt}</div>
                        <div style="flex:1; text-align:left; font-weight:bold; padding-left:10px;">
                            <img src="{a_logo}" width="20" style="vertical-align:middle; margin-right:5px;"> {row['response.teams.away.name']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_btn:
                    if mode == "Senaste resultaten":
                        if st.button("Analys", key=f"btn_{index}"):
                            st.session_state.view_match = row
                            st.rerun()
                    else:
                        st.button("H2H", key=f"btn_{index}", disabled=True)

        # --- TAB 2: LAGSTATISTIK ---
        with tab2:
            st.header("📊 Laganalys")
            teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", teams)
            if sel_team:
                t_df = df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)]
                st.metric("Matcher totalt i systemet", len(t_df))

        # --- TAB 3: DOMARANALYS ---
        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Matcher", len(r_df))
                c2.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                c3.metric("Fouls/Match", round((r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean(), 2))
                c4.metric("Straffar Totalt", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))

        # --- TAB 4: TABELL ---
        with tab4:
            st.header("🏆 Serietabell")
            if standings_df is not None and not standings_df.empty:
                st.dataframe(standings_df, hide_index=True, use_container_width=True)
            else:
                st.info("Tabellen uppdateras så fort API-kvoten nollställs.")

else:
    st.error("Kunde inte ladda 'Raw Data'. Kontrollera länk och publicering.")
