import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pro Football Stats", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # --- TVÄTTMASKIN: Ta bort teknisk metadata ---
    # Vi behåller bara kolumner som INTE börjar med dessa ord
    cols_to_exclude = ['get', 'parameters', 'paging', 'errors']
    df = df[[c for c in df.columns if not any(c.startswith(bad) for bad in cols_to_exclude)]]
    
    # Snygga till säsongs-formatet
    if 'response.league.season' in df.columns:
        df['response.league.season'] = df['response.league.season'].astype(str).str.replace('.0', '', regex=False)
        
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    st.title("⚽ Renodlad Matchanalys")
    st.write("Teknisk metadata har filtrerats bort för en renare vy.")

    # --- SIDEBAR FILTRERING ---
    st.sidebar.header("Filtreringsverktyg")

    # Kolumn-mappning för snyggare filter
    col_map = {
        'land': 'response.league.country',
        'serie': 'response.league.name',
        'sasong': 'response.league.season',
        'domare': 'response.fixture.referee',
        'hemma': 'response.teams.home.name',
        'borta': 'response.teams.away.name'
    }

    # 1. Land
    val_land = st.sidebar.selectbox("Välj Land", ['Alla'] + sorted(df[col_map['land']].dropna().unique().tolist()))
    if val_land != 'Alla':
        df = df[df[col_map['land']] == val_land]

    # 2. Serie
    val_serie = st.sidebar.selectbox("Välj Serie", ['Alla'] + sorted(df[col_map['serie']].dropna().unique().tolist()))
    if val_serie != 'Alla':
        df = df[df[col_map['serie']] == val_serie]

    # 3. Säsong
    val_sasong = st.sidebar.selectbox("Välj Säsong", ['Alla'] + sorted(df[col_map['sasong']].dropna().unique().tolist(), reverse=True))
    if val_sasong != 'Alla':
        df = df[df[col_map['sasong']] == val_sasong]

    # 4. Domare
    val_domare = st.sidebar.selectbox("Välj Domare", ['Alla'] + sorted(df[col_map['domare']].dropna().unique().tolist()))
    if val_domare != 'Alla':
        df = df[df[col_map['domare']] == val_domare]

    # 5. Lag & Position
    st.sidebar.markdown("---")
    val_lag = st.sidebar.text_input("Sök specifikt lag")
    pos = st.sidebar.radio("Visa matcher för laget som:", ["Båda", "Hemma", "Borta"])

    if val_lag:
        if pos == "Hemma":
            df = df[df[col_map['hemma']].str.contains(val_lag, case=False, na=False)]
        elif pos == "Borta":
            df = df[df[col_map['borta']].str.contains(val_lag, case=False, na=False)]
        else:
            df = df[(df[col_map['hemma']].str.contains(val_lag, case=False, na=False)) | 
                    (df[col_map['borta']].str.contains(val_lag, case=False, na=False))]

    # --- DISPLAY ---
    st.metric("Matcher som matchar filtren", len(df))
    
    # Vi kan dölja fler kolumner här om det behövs, men nu är de värsta borta!
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod. Kontrollera din data. Fel: {e}")
