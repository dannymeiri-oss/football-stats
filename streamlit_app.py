import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

# Din CSV-länk
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # 1. Mappa om de tekniska namnen till snygga namn
    # Här väljer vi ut EXAKT de kolumner vi vill se. 
    # Om en kolumn inte finns i ditt ark än (t.ex. xG), lägg till den i listan sen.
    keep_and_rename = {
        'response.fixture.date': 'Datum',
        'response.league.country': 'Land',
        'response.league.name': 'Serie',
        'response.teams.home.name': 'Hemmalag',
        'response.teams.away.name': 'Bortalag',
        'response.fixture.referee': 'Domare',
        'response.fixture.venue.name': 'Arena',
        'response.fixture.venue.city': 'Stad',
        'response.goals.home': 'Mål H',
        'response.goals.away': 'Mål B',
        'response.league.season': 'Säsong'
    }
    
    # Behåll bara de vi definierat ovan som faktiskt finns i filen
    existing_cols = [c for c in keep_and_rename.keys() if c in df.columns]
    df = df[existing_cols].copy()
    df = df.rename(columns=keep_and_rename)
    
    # 2. Snygga till formatet
    if 'Säsong' in df.columns:
        df['Säsong'] = df['Säsong'].astype(str).str.replace('.0', '', regex=False)
    if 'Datum' in df.columns:
        df['Datum'] = pd.to_datetime(df['Datum']).dt.strftime('%Y-%m-%d %H:%M')
        
    return df

try:
    df_display = load_data()

    st.title("⚽ Matchanalys")

    # --- SIDEBAR FILTER ---
    st.sidebar.header("Filtrera")
    
    # Dynamiska filter baserat på de snygga namnen
    for col in ['Land', 'Serie', 'Domare']:
        if col in df_display.columns:
            options = ['Alla'] + sorted(df_display[col].dropna().unique().tolist())
            choice = st.sidebar.selectbox(f"Välj {col}", options)
            if choice != 'Alla':
                df_display = df_display[df_display[col] == choice]

    # Lag-sök
    search = st.sidebar.text_input("Sök lag (Hemma eller Borta)")
    if search:
        mask = (df_display['Hemmalag'].str.contains(search, case=False, na=False)) | \
               (df_display['Bortalag'].str.contains(search, case=False, na=False))
        df_display = df_display[mask]

    # --- VISA DATA ---
    st.metric("Antal matcher i urval", len(df_display))
    st.dataframe(df_display, use_container_width=True)

except Exception as e:
    st.error("Kunde inte ladda tabellen. Kontrollera att kolumnnamnen i Google Sheets stämmer med koden.")
    st.info(f"Felmeddelande: {e}")
