import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pro Football Stats", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    
    # --- TVÄTTMASKIN: Ta bort teknisk metadata ---
    # Vi lägger till 'results' i listan här
    cols_to_exclude = ['get', 'parameters', 'paging', 'errors', 'results']
    df = df[[c for c in df.columns if not any(c.startswith(bad) for bad in cols_to_exclude)]]
    
    # --- SNYGGARE NAMN: Döper om de tekniska namnen till läsbara namn ---
    rename_dict = {
        'response.league.country': 'Land',
        'response.league.name': 'Serie',
        'response.league.season': 'Säsong',
        'response.fixture.referee': 'Domare',
        'response.teams.home.name': 'Hemmalag',
        'response.teams.away.name': 'Bortalag',
        'response.fixture.date': 'Datum'
    }
    # Vi mappar bara de kolumner som faktiskt finns i df
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
    
    # Snygga till säsongs-formatet och datum
    if 'Säsong' in df.columns:
        df['Säsong'] = df['Säsong'].astype(str).str.replace('.0', '', regex=False)
    if 'Datum' in df.columns:
        df['Datum'] = pd.to_datetime(df['Datum']).dt.date
        
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    st.title("⚽ Renodlad Matchanalys")
    
    # --- SIDEBAR FILTRERING ---
    st.sidebar.header("Filtreringsverktyg")

    # 1. Land
    land_list = ['Alla'] + sorted(df['Land'].dropna().unique().tolist()) if 'Land' in df.columns else ['Alla']
    val_land = st.sidebar.selectbox("Välj Land", land_list)
    if val_land != 'Alla':
        df = df[df['Land'] == val_land]

    # 2. Serie
    serie_list = ['Alla'] + sorted(df['Serie'].dropna().unique().tolist()) if 'Serie' in df.columns else ['Alla']
    val_serie = st.sidebar.selectbox("Välj Serie", serie_list)
    if val_serie != 'Alla':
        df = df[df['Serie'] == val_serie]

    # 3. Säsong
    sasong_list = ['Alla'] + sorted(df['Säsong'].dropna().unique().tolist(), reverse=True) if 'Säsong' in df.columns else ['Alla']
    val_sasong = st.sidebar.selectbox("Välj Säsong", sasong_list)
    if val_sasong != 'Alla':
        df = df[df['Säsong'] == val_sasong]

    # 4. Domare
    domare_list = ['Alla'] + sorted(df['Domare'].dropna().unique().tolist()) if 'Domare' in df.columns else ['Alla']
    val_domare = st.sidebar.selectbox("Välj Domare", domare_list)
    if val_domare != 'Alla':
        df = df[df['Domare'] == val_domare]

    # 5. Lag & Position
    st.sidebar.markdown("---")
    val_lag = st.sidebar.text_input("Sök specifikt lag")
    pos = st.sidebar.radio("Visa matcher för laget som:", ["Båda", "Hemma", "Borta"])

    if val_lag:
        if pos == "Hemma":
            df = df[df['Hemmalag'].str.contains(val_lag, case=False, na=False)]
        elif pos == "Borta":
            df = df[df['Bortalag'].str.contains(val_lag, case=False, na=False)]
        else:
            df = df[(df['Hemmalag'].str.contains(val_lag, case=False, na=False)) | 
                    (df['Bortalag'].str.contains(val_lag, case=False, na=False))]

    # --- DISPLAY ---
    st.metric("Matcher efter filter", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod. Kolla att kolumnnamnen stämmer i ditt Sheet. Fel: {e}")
