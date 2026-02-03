import streamlit as st
import pandas as pd

# Inställningar för sidan
st.set_page_config(page_title="Stats Hub - Football Analysis", layout="wide")

# CSS för att göra det lite snyggare
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Länk till din data (din specifika länk)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600) # Uppdaterar datan var 10:e minut
def load_data():
    # Läser in datan
    df = pd.read_csv(CSV_URL)
    
    # Försök hitta datumkolumnen och snygga till den
    # Vi kollar efter vanliga namn som 'Datum' eller 'Date'
    date_col = next((c for c in df.columns if c.lower() in ['datum', 'date']), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col]).dt.date
        
    return df

try:
    df = load_data()

    st.title("⚽ Football Stats Hub")
    st.write("Välkommen till din personliga databas. Här ser du analysen av dina matcher och xG.")

    # --- KPI RAD (Högst upp) ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Totalt antal matcher", len(df))
    with col2:
        # Letar efter en kolumn som innehåller xG för att räkna snitt
        xg_cols = [c for c in df.columns if 'xg' in c.lower()]
        if xg_cols:
            avg_xg = df[xg_cols[0]].mean()
            st.metric("Snitt xG (Total)", f"{avg_xg:.2f}")
        else:
            st.metric("xG Data", "Ej hittad")
    with col3:
        # Räknar unika ligor om kolumnen 'Liga' eller 'League' finns
        league_col = next((c for c in df.columns if c.lower() in ['liga', 'league']), None)
        if league_col:
            st.metric("Antal Ligor", df[league_col].nunique())
    with col4:
        st.metric("Status", "Live & Uppdaterad")

    # --- SIDEBAR FILTER ---
    st.sidebar.header("Filtrera Statistik")
    
    # Filter för Liga
    if league_col:
        all_leagues = df[league_col].unique().tolist()
        selected_leagues = st.sidebar.multiselect("Välj Ligor", options=all_leagues, default=all_leagues)
        df
