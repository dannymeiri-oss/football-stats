import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pro Football Stats", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    # Konvertera Säsong till text för att undvika decimaler (t.ex. 2023 istället för 2023.0)
    if 'response.league.season' in df.columns:
        df['response.league.season'] = df['response.league.season'].astype(str).str.replace('.0', '', regex=False)
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    st.title("⚽ Avancerad Matchanalys")
    st.markdown("---")

    # --- SIDEBAR FILTRERING ---
    st.sidebar.header("Filtreringsverktyg")

    # 1. Land
    land_col = 'response.league.country'
    land_list = ['Alla'] + sorted(df[land_col].dropna().unique().tolist())
    val_land = st.sidebar.selectbox("Välj Land", land_list)
    if val_land != 'Alla':
        df = df[df[land_col] == val_land]

    # 2. Serie
    serie_col = 'response.league.name'
    serie_list = ['Alla'] + sorted(df[serie_col].dropna().unique().tolist())
    val_serie = st.sidebar.selectbox("Välj Serie", serie_list)
    if val_serie != 'Alla':
        df = df[df[serie_col] == val_serie]

    # 3. Säsong
    sasong_col = 'response.league.season'
    sasong_list = ['Alla'] + sorted(df[sasong_col].dropna().unique().tolist(), reverse=True)
    val_sasong = st.sidebar.selectbox("Välj Säsong", sasong_list)
    if val_sasong != 'Alla':
        df = df[df[sasong_col] == val_sasong]

    # 4. Domare
    domare_col = 'response.fixture.referee'
    domare_list = ['Alla'] + sorted(df[domare_col].dropna().unique().tolist())
    val_domare = st.sidebar.selectbox("Välj Domare", domare_list)
    if val_domare != 'Alla':
        df = df[df[domare_col] == val_domare]

    # 5. Lag & Position
    st.sidebar.markdown("---")
    val_lag = st.sidebar.text_input("Sök specifikt lag")
    pos = st.sidebar.radio("Visa matcher för laget som:", ["Båda", "Hemma", "Borta"])

    # Logik för lag-filtrering
    home_col = 'response.teams.home.name'
    away_col = 'response.teams.away.name'
    
    if val_lag:
        if pos == "Hemma":
            df = df[df[home_col].str.contains(val_lag, case=False, na=False)]
        elif pos == "Borta":
            df = df[df[away_col].str.contains(val_lag, case=False, na=False)]
        else:
            df = df[(df[home_col].str.contains(val_lag, case=False, na=False)) | 
                    (df[away_col].str.contains(val_lag, case=False, na=False))]

    # --- VIKTIG STATISTIK (KPI) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Antal matcher i urval", len(df))
    with c2:
        # Om du har en mål-kolumn kan vi räkna snitt här
        st.metric("Aktuellt filter", f"{val_land if val_land != 'Alla' else 'Globalt'}")
    with c3:
        st.metric("Domare vald", "Ja" if val_domare != 'Alla' else "Nej")

    # --- TABELL ---
    st.subheader("Matchresultat")
    # Vi visar en snyggare tabell där vi kan välja vilka kolumner som syns först
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod vid filtrering. Kontrollera att kolumnnamnen i din CSV är exakta.")
    st.info(f"Tekniskt felmeddelande: {e}")
