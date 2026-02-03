import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # --- LISTAN PÅ KOLUMNER SOM SKALL BORT ---
    # Här kan du enkelt lägga till fler namn i framtiden
    blacklist = [
        'get', 'parameters', 'paging', 'errors', 'results',
        'response.fixture.id', 
        'response.fixture.timezone',
        'response.fixture.timestamp',
        'response.fixture.periods.first',
        'response.fixture.periods.second'
    ]
    
    # 1. Ta bort exakta namn från listan ovan
    df = df.drop(columns=[c for c in blacklist if c in df.columns])
    
    # 2. Ta bort alla kolumner som INNEHÅLLER dessa ord (smart rensning)
    # Detta tar hand om saker som fixture.id, league.id, team.id automatiskt
    smart_remove = ['.id', 'logo', 'flag', 'timezone', 'winner']
    df = df.drop(columns=[c for c in df.columns if any(word in c.lower() for word in smart_remove)])

    # 3. Logik för Kommande vs Historik
    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
        
    return df

try:
    df_raw = load_data()

    # --- NAVIGATION ---
    sida = st.sidebar.radio("Välj vy:", ["Historik", "Kommande matcher"])

    if sida == "Historik":
        st.title("⚽ Matchhistorik")
        df_view = df_raw[df_raw['spelad'] == True].copy()
    else:
        st.title("📅 Kommande matcher")
        df_view = df_raw[df_raw['spelad'] == False].copy()

    # --- VISA ---
    st.metric(f"Antal matcher ({sida})", len(df_view))
    st.dataframe(df_view, use_container_width=True)
    
    if st.sidebar.button("Uppdatera från Google Sheets"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
