import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pro Football Stats", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # --- STRÄNGARE TVÄTTMASKIN ---
    # Tar bort kolumner som innehåller något av dessa ord överhuvudtaget
    bad_keywords = ['get', 'parameter', 'paging', 'error', 'results', 'fixture.id', 'logo', 'flag', 'winner', 'penalty', 'extratime']
    
    clean_cols = [c for c in df.columns if not any(bad in c.lower() for bad in bad_keywords)]
    df = df[clean_cols]
    
    # --- NAMNBYTE ---
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
    
    # Fixa format för Säsong och Datum
    if 'Säsong' in df.columns:
        df['Säsong'] = df['Säsong'].astype(str).str.replace('.0', '', regex=False)
    if 'Datum' in df.columns:
        df['Datum'] = pd.to_datetime(df['Datum']).dt.strftime('%Y-%m-%d %H:%M')
        
    return df

try:
    df = load_data()

    st.title("⚽ Matchanalys - Städad vy")
    
    # --- SIDEBAR ---
    st.sidebar.header("Filter")
    
    # Filter-logik (kollar om kolumnen finns innan den skapar filtret)
    if 'Land' in df.columns:
        land = st.sidebar.selectbox("Välj Land", ['Alla'] + sorted(df['Land'].dropna().unique().tolist()))
        if land != 'Alla':
            df = df[df['Land'] == land]

    if 'Serie' in df.columns:
        serie = st.sidebar.selectbox("Välj Serie", ['Alla'] + sorted(df['Serie'].dropna().unique().tolist()))
        if serie != 'Alla':
            df = df[df['Serie'] == serie]

    if 'Domare' in df.columns:
        domare = st.sidebar.selectbox("Välj Domare", ['Alla'] + sorted(df['Domare'].dropna().unique().tolist()))
        if domare != 'Alla':
            df = df[df['Domare'] == domare]

    # Sök lag
    val_lag = st.sidebar.text_input("Sök lag")
    if val_lag:
        # Söker i alla kolumner för säkerhets skull
        df = df[df.astype(str).apply(lambda x: x.str.contains(val_lag, case=False)).any(axis=1)]

    # --- RESULTAT ---
    st.metric("Hittade matcher", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
