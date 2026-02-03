import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # --- DEFINIERA LOGO-KOLUMNER ---
    # Vi vill behålla dessa tre specifikt
    logos = ['response.league.logo', 'response.teams.home.logo', 'response.teams.away.logo']
    
    # DIN LISTA (Vi har tagit bort logotyperna från utrensningslistan)
    cols_to_remove = [
        'get', 'parameters.league', 'parameters.season', 'paging.current', 'paging.total', 
        'results', 'errors', 'response.fixture.id', 'response.fixture.timezone', 
        'response.fixture.timestamp', 'response.fixture.periods.first', 
        'response.fixture.periods.second', 'response.fixture.status.short', 
        'response.fixture.venue.id', 'response.fixture.status.elapsed', 
        'response.fixture.status.extra', 'response.league.id',
        'response.league.flag', 'response.league.round', 'response.league.standings',
        'response.teams.home.id', 'response.teams.home.winner',
        'response.teams.away.id', 'response.teams.away.winner',
        'response.score.extratime.home', 'response.score.extratime.away',
        'response.score.penalty.home', 'response.score.penalty.away'
    ]
    
    # Ta bort skräp men spara logos
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns])
    df = df.drop(columns=[c for c in df.columns if 'errors.' in c or 'fixture.id' in c or 'timezone' in c])

    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
    
    return df

try:
    df_raw = load_data()

    st.sidebar.title("Navigation")
    sida = st.sidebar.radio("Gå till:", ["Historik", "Kommande matcher"])

    # --- FILTER-MAPPNING ---
    fm = {
        'Land': 'response.league.country',
        'Serie': 'response.league.name',
        'Hemmalag': 'response.teams.home.name',
        'Bortalag': 'response.teams.away.name'
    }

    if sida == "Historik":
        st.title("⚽ Matchhistorik")
        df_view = df_raw[df_raw['spelad'] == True].copy()
    else:
        st.title("📅 Kommande matcher")
        df_view = df_raw[df_raw['spelad'] == False].copy()

    # --- FILTER ---
    st.sidebar.header("Filtrera vyn")
    if fm['Land'] in df_view.columns:
        land_list = ['Alla'] + sorted(df_view[fm['Land']].dropna().unique().tolist())
        val_land = st.sidebar.selectbox("Välj Land", land_list)
        if val_land != 'Alla':
            df_view = df_view[df_view[fm['Land']] == val_land]

    search = st.sidebar.text_input("Sök lag")
    if search:
        df_view = df_view[(df_view[fm['Hemmalag']].astype(str).str.contains(search, case=False)) | 
                          (df_view[fm['Bortalag']].astype(str).str.contains(search, case=False))]

    # --- RENDERERING AV LOGOTYPER ---
    # Vi använder st.column_config för att berätta för Streamlit att vissa kolumner är bilder
    st.metric(f"Antal {sida.lower()}", len(df_view))
    
    st.dataframe(
        df_view,
        column_config={
            "response.league.logo": st.column_config.ImageColumn("Liga"),
            "response.teams.home.logo": st.column_config.ImageColumn("H-Logo"),
            "response.teams.away.logo": st.column_config.ImageColumn("B-Logo"),
        },
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
