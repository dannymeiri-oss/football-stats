import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # DIN "SVARTA LISTA" - Dessa kolumner tas bort helt
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
    
    # Ta bort kolumnerna om de finns i filen
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns])
    
    # SNYGGARE NAMN ENBART FÖR FILTRERING (för att göra sidebaren läsbar)
    # Vi mappar de långa namnen till korta namn för logikens skull
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
    st.write("Här visas all din statistik, minus den tekniska metadatan.")

    # --- SIDEBAR FILTER ---
    st.sidebar.header("Filtrera")
    
    # Land-filter
    if fm['Land'] in df.columns:
        land_opt = ['Alla'] + sorted(df[fm['Land']].dropna().unique().tolist())
        val_land = st.sidebar.selectbox("Välj Land", land_opt)
        if val_land != 'Alla':
            df = df[df[fm['Land']] == val_land]

    # Serie-filter
    if fm['Serie'] in df.columns:
        serie_opt = ['Alla'] + sorted(df[fm['Serie']].dropna().unique().tolist())
        val_serie = st.sidebar.selectbox("Välj Serie", serie_opt)
        if val_serie != 'Alla':
            df = df[df[fm['Serie'] == val_serie]]

    # Domar-filter
    if fm['Domare'] in df.columns:
        dom_opt = ['Alla'] + sorted(df[fm['Domare']].dropna().unique().tolist())
        val_dom = st.sidebar.selectbox("Välj Domare", dom_opt)
        if val_dom != 'Alla':
            df = df[df[fm['Domare']] == val_dom]

    # Lag-sök
    search = st.sidebar.text_input("Sök specifikt lag")
    if search:
        # Söker i både hemma- och bortakolumnen
        h_col = fm['Hemmalag']
        a_col = fm['Bortalag']
        df = df[(df[h_col].astype(str).str.contains(search, case=False)) | 
                (df[a_col].astype(str).str.contains(search, case=False))]

    # --- VISA TABELLEN ---
    st.metric("Antal matcher", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
