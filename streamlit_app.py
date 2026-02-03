import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # DIN SVARTA LISTA
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
    
    # 1. Ta bort de exakta namnen
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns])

    # 2. Ta bort allt som innehåller "errors." (som errors.1)
    df = df.drop(columns=[c for c in df.columns if 'errors.' in c])
    
    # 3. Mappning för filter
    filter_mapping = {
        'Land': 'response.league.country',
        'Serie': 'response.league.name',
        'Säsong': 'response.league.season',
        'Domare': 'response.fixture.referee',
        'Hemmalag': 'response.teams.home.name',
        'Bortalag': 'response.teams.away.name'
    }
    
    return df, filter_mapping

try:
    df, fm = load_data()

    st.title("⚽ Matchanalys")

    # --- SIDEBAR FILTER ---
    st.sidebar.header("Filtrera")
    
    if fm['Land'] in df.columns:
        land_opt = ['Alla'] + sorted(df[fm['Land']].dropna().unique().tolist())
        val_land = st.sidebar.selectbox("Välj Land", land_opt)
        if val_land != 'Alla':
            df = df[df[fm['Land']] == val_land]

    if fm['Serie'] in df.columns:
        serie_opt = ['Alla'] + sorted(df[fm['Serie']].dropna().unique().tolist())
        val_serie = st.sidebar.selectbox("Välj Serie", serie_opt)
        if val_serie != 'Alla':
            df = df[df[fm['Serie']] == val_serie]

    if fm['Domare'] in df.columns:
        dom_opt = ['Alla'] + sorted(df[fm['Domare']].dropna().unique().tolist())
        val_dom = st.sidebar.selectbox("Välj Domare", dom_opt)
        if val_dom != 'Alla':
            df = df[df[fm['Domare']] == val_dom]

    search = st.sidebar.text_input("Sök specifikt lag")
    if search:
        h_col = fm['Hemmalag']
        a_col = fm['Bortalag']
        df = df[(df[h_col].astype(str).str.contains(search, case=False)) | 
                (df[a_col].astype(str).str.contains(search, case=False))]

    # --- VISA ---
    st.metric("Antal matcher", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
