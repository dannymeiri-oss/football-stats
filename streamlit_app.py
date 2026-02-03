import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # DIN UPPDATERADE SVARTA LISTA (Nu med fixture.id och timezone inkluderat)
    cols_to_remove = [
        'get', 'parameters.league', 'parameters.season', 'paging.current', 'paging.total', 
        'results', 'errors', 'response.fixture.id', 'response.fixture.timezone', 
        'response.fixture.timestamp', 'response.fixture.periods.first', 
        'response.fixture.periods.second', 'response.fixture.status.short', 
        'response.fixture.venue.id', 'response.fixture.status.elapsed', 
        'response.fixture.status.extra', 'response.league.id', 'response.league.logo', 
        'response.league.flag', 'response.league.round', 'response.league.standings',
        'response.teams.home.id', 'response.teams.home.logo', 'response.teams.home.winner',
        'response.teams.away.id', 'response.teams.away.logo', 'response.teams.away.winner',
        'response.score.extratime.home', 'response.score.extratime.away',
        'response.score.penalty.home', 'response.score.penalty.away'
    ]
    
    # 1. Ta bort de specifika kolumnerna
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns])

    # 2. Ta bort allt med "errors." eller "logo"
    df = df.drop(columns=[c for c in df.columns if 'errors.' in c or 'logo' in c])

    # 3. Skapa logik för spelad vs kommande
    # Vi kollar om målkolumnen har ett värde för att avgöra om matchen är spelad
    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
    
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
        'Bortalag': 'response.teams.away.name'
    }

    # Dela upp data baserat på vald sida
    if sida == "Historik":
        st.title("⚽ Matchhistorik")
        df_view = df_raw[df_raw['spelad'] == True].copy()
    else:
        st.title("📅 Kommande matcher")
        df_view = df_raw[df_raw['spelad'] == False].copy()

    # --- FILTER ---
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

    # --- VISA TABELL ---
    st.metric(f"Antal {sida.lower()}", len(df_view))
    st.dataframe(df_view, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
