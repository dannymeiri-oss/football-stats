import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300) # Sänkt till 5 minuter för snabbare uppdatering
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # RENSNING (samma som tidigare)
    cols_to_remove = ['get', 'parameters.league', 'parameters.season', 'paging.current', 'paging.total', 'results', 'errors']
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns])
    df = df.drop(columns=[c for c in df.columns if 'errors.' in c or 'logo' in c or 'winner' in c])

    # Skapa en hjälp-kolumn för att se om matchen spelats
    # Vi kollar om 'response.goals.home' har ett värde
    df['spelad'] = df['response.goals.home'].notna()
    
    return df

try:
    df_raw = load_data()

    # --- NAVIGATION ---
    st.sidebar.title("Navigation")
    sida = st.sidebar.radio("Gå till:", ["Historik", "Kommande matcher"])

    # --- FILTER-MAPPNING ---
    fm = {
        'Land': 'response.league.country',
        'Serie': 'response.league.name',
        'Hemmalag': 'response.teams.home.name',
        'Bortalag': 'response.teams.away.name',
        'Datum': 'response.fixture.date'
    }

    if sida == "Historik":
        st.title("⚽ Matchhistorik")
        df_view = df_raw[df_raw['spelad'] == True].copy()
    else:
        st.title("📅 Kommande matcher")
        # Kommande är matcher där mål saknas
        df_view = df_raw[df_raw['spelad'] == False].copy()
        if df_view.empty:
            st.info("Just nu finns inga kommande matcher i din databas.")

    # --- GEMENSAMMA FILTER ---
    st.sidebar.header("Filtrera vyn")
    
    # Land filter
    if fm['Land'] in df_view.columns:
        land_list = ['Alla'] + sorted(df_view[fm['Land']].dropna().unique().tolist())
        val_land = st.sidebar.selectbox("Välj Land", land_list)
        if val_land != 'Alla':
            df_view = df_view[df_view[fm['Land']] == val_land]

    # Sök lag
    search = st.sidebar.text_input("Sök lag")
    if search:
        df_view = df_view[(df_view[fm['Hemmalag']].astype(str).str.contains(search, case=False)) | 
                          (df_view[fm['Bortalag']].astype(str).str.contains(search, case=False))]

    # --- VISA DATA ---
    st.metric(f"Antal {sida.lower()}", len(df_view))
    st.dataframe(df_view, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
