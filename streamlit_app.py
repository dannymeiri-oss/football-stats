import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # 1. FIXA SNYGGASTE DATUMFORMATET: "20 Feb 2024 20:15"
    if 'response.fixture.date' in df.columns:
        # Vi skapar först en riktig tidskolumn för att kunna sortera korrekt
        df['dt_object'] = pd.to_datetime(df['response.fixture.date'])
        # Sen skapar vi den snygga texten för visning
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    df['-'] = '-'
    
    # 2. DEFINIERA ORDNINGEN
    desired_order = [
        'Datum',
        'response.league.logo',
        'response.teams.home.logo', 
        'response.teams.home.name', 
        'response.goals.home', 
        '-', 
        'response.goals.away', 
        'response.teams.away.name', 
        'response.teams.away.logo'
    ]
    
    blacklist = ['get', 'parameters', 'paging', 'errors', 'results', 'id', 'timezone', 'timestamp', 'periods', 'status', 'venue', 'winner', 'flag', 'response.fixture.date', 'dt_object']
    remaining_cols = [c for c in df.columns if c not in desired_order and not any(b in c.lower() for b in blacklist) and c != 'spelad']
    
    final_order = desired_order + remaining_cols
    df = df.reindex(columns=[c for c in final_order if c in df.columns])

    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
    
    return df

try:
    df_raw = load_data()

    st.sidebar.title("Meny")
    sida = st.sidebar.radio("Visa:", ["Historik", "Kommande matcher"])

    if sida == "Historik":
        st.title("⚽ Resultat")
        df_view = df_raw[df_raw['spelad'] == True].copy()
        # Sortera på det dolda tidsobjektet för att få rätt ordning
        if 'dt_object' in df_raw.columns:
            df_view = df_view.sort_values(by='dt_object', ascending=False)
    else:
        st.title("📅 Schema")
        df_view = df_raw[df_raw['spelad'] == False].copy()
        if 'dt_object' in df_raw.columns:
            df_view = df_view.sort_values(by='dt_object', ascending=True)
            
        cols_to_hide = ['response.goals.home', '-', 'response.goals.away']
        df_view = df_view.drop(columns=[c for c in cols_to_hide if c in df_view.columns])

    # Filter
    search = st.sidebar.text_input("Sök lag")
    if search:
        df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # --- RENDERERING ---
    st.dataframe(
        df_view,
        column_config={
            "Datum": st.column_config.TextColumn("Datum & Tid", width="medium"),
            "response.league.logo": st.column_config.ImageColumn("", width="small"),
            "response.teams.home.logo": st.column_config.ImageColumn("", width="small"),
            "response.teams.home.name": st.column_config.TextColumn("Hemmalag", width="medium"),
            "response.goals.home": st.column_config.TextColumn("", width="small"),
            "-": st.column_config.TextColumn("", width="small"),
            "response.goals.away": st.column_config.TextColumn("", width="small"),
            "response.teams.away.name": st.column_config.TextColumn("Bortalag", width="medium"),
            "response.teams.away.logo": st.column_config.ImageColumn("", width="small"),
        },
        use_container_width=False,
        hide_index=True
    )

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
