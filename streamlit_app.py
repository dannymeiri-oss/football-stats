import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # 1. Skapa "Bindestreck"-kolumnen
    df['-'] = '-'
    
    # 2. Definiera ordningen vi vill ha (Logo -> Namn -> Mål -> vs -> Mål -> Namn -> Logo)
    # Vi lägger till övrig statistik (skott, hörnor etc.) på slutet automatiskt
    desired_order = [
        'response.teams.home.logo', 
        'response.teams.home.name', 
        'response.goals.home', 
        '-', 
        'response.goals.away', 
        'response.teams.away.name', 
        'response.teams.away.logo',
        'response.league.logo',
        'response.league.name',
        'response.fixture.date'
    ]
    
    # Identifiera alla andra kolumner (statistik etc.) som inte är med i listan ovan eller i svarta listan
    blacklist = [
        'get', 'parameters.league', 'parameters.season', 'paging.current', 'paging.total', 
        'results', 'errors', 'id', 'timezone', 'timestamp', 'periods', 'status', 'venue', 'winner', 'flag'
    ]
    
    remaining_cols = [c for c in df.columns if c not in desired_order and not any(b in c.lower() for b in blacklist)]
    
    # Slå ihop ordningen
    final_order = desired_order + remaining_cols
    df = df.reindex(columns=[c for c in final_order if c in df.columns])

    # Logik för spelad vs kommande
    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
    
    return df

try:
    df_raw = load_data()

    st.sidebar.title("Navigation")
    sida = st.sidebar.radio("Gå till:", ["Historik", "Kommande matcher"])

    # Filtrering
    if sida == "Historik":
        st.title("⚽ Matchresultat")
        df_view = df_raw[df_raw['spelad'] == True].copy()
    else:
        st.title("📅 Kommande matcher")
        df_view = df_raw[df_raw['spelad'] == False].copy()
        # För kommande matcher gömmer vi mål-kolumnerna och bindestrecket
        cols_to_hide = ['response.goals.home', '-', 'response.goals.away']
        df_view = df_view.drop(columns=[c for c in cols_to_hide if c in df_view.columns])

    # Sidebar Filter (samma som förut)
    st.sidebar.header("Filter")
    search = st.sidebar.text_input("Sök lag")
    if search:
        df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # --- RENDERERING ---
    st.metric(f"Antal {sida.lower()}", len(df_view))
    
    # Vi mappar de tekniska namnen till snygga rubriker i vyn
    st.dataframe(
        df_view,
        column_config={
            "response.teams.home.logo": st.column_config.ImageColumn(""),
            "response.teams.home.name": "Hemmalag",
            "response.goals.home": "H",
            "-": "",
            "response.goals.away": "B",
            "response.teams.away.name": "Bortalag",
            "response.teams.away.logo": st.column_config.ImageColumn(""),
            "response.league.logo": st.column_config.ImageColumn("Liga"),
            "response.league.name": "Serie",
            "response.fixture.date": "Datum"
        },
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
