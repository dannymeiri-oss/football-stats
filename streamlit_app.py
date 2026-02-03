import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pro Football Stats", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # --- TOTALSTÄDNING: Vi tar bort listan på onödiga kolumner ---
    cols_to_drop = [
        'get', 'parameters', 'paging', 'errors', 'results',
        'response.fixture.id', 'response.fixture.timezone', 'response.fixture.timestamp',
        'response.fixture.periods.first', 'response.fixture.periods.second',
        'response.fixture.status.short', 'response.fixture.venue.id',
        'response.fixture.status.elapsed', 'response.fixture.status.extra',
        'response.league.id', 'response.league.logo', 'response.league.flag',
        'response.league.round', 'response.league.standings',
        'response.teams.home.id', 'response.teams.home.logo', 'response.teams.home.winner',
        'response.teams.away.id', 'response.teams.away.logo', 'response.teams.away.winner',
        'response.score.extratime.home', 'response.score.extratime.away',
        'response.score.penalty.home', 'response.score.penalty.away'
    ]
    
    # Vi tar bara bort de kolumner som faktiskt finns i listan för att undvika fel
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    # --- SNYGGARE NAMN: Döper om de kvarvarande viktiga namnen ---
    rename_dict = {
        'response.league.country': 'Land',
        'response.league.name': 'Serie',
        'response.league.season': 'Säsong',
        'response.fixture.referee': 'Domare',
        'response.teams.home.name': 'Hemmalag',
        'response.teams.away.name': 'Bortalag',
        'response.fixture.date': 'Datum',
        'response.fixture.venue.name': 'Arena',
        'response.fixture.venue.city': 'Stad',
        'response.goals.home': 'Mål Hemma',
        'response.goals.away': 'Mål Borta'
    }
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
    
    # Snygga till format
    if 'Säsong' in df.columns:
        df['Säsong'] = df['Säsong'].astype(str).str.replace('.0', '', regex=False)
    if 'Datum' in df.columns:
        # Gör om till snyggt datumformat: YYYY-MM-DD HH:MM
        df['Datum'] = pd.to_datetime(df['Datum']).dt.strftime('%Y-%m-%d %H:%M')
        
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    st.title("⚽ Matchanalys - Städad vy")
    
    # --- SIDEBAR FILTRERING ---
    st.sidebar.header("Filter")

    # Land
    land_list = ['Alla'] + sorted(df['Land'].dropna().unique().tolist()) if 'Land' in df.columns else ['Alla']
    val_land = st.sidebar.selectbox("Välj Land", land_list)
    if val_land != 'Alla':
        df = df[df['Land'] == val_land]

    # Serie
    serie_list = ['Alla'] + sorted(df['Serie'].dropna().unique().tolist()) if 'Serie' in df.columns else ['Alla']
    val_serie = st.sidebar.selectbox("Välj Serie", serie_list)
    if val_serie != 'Alla':
        df = df[df['Serie'] == val_serie]

    # Domare
    domare_list = ['Alla'] + sorted(df['Domare'].dropna().unique().tolist()) if 'Domare' in df.columns else ['Alla']
    val_domare = st.sidebar.selectbox("Välj Domare", domare_list)
    if val_domare != 'Alla':
        df = df[df['Domare'] == val_domare]

    # Lag-sök
    st.sidebar.markdown("---")
    val_lag = st.sidebar.text_input("Sök lag")
    if val_lag:
        df = df[(df['Hemmalag'].astype(str).str.contains(val_lag, case=False)) | 
                (df['Bortalag'].astype(str).str.contains(val_lag, case=False))]

    # --- DATATABELL ---
    st.metric("Visar antal matcher", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
