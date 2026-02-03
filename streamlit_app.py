import streamlit as st
import pandas as pd

# Inställningar för sidan
st.set_page_config(page_title="Stats Hub - Football Analysis", layout="wide")

# Länk till din data
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    data = pd.read_csv(CSV_URL)
    return data

# Själva programmet
try:
    df = load_data()

    st.title("⚽ Football Stats Hub")
    st.write("Välkommen till din personliga databas.")

    # KPI-Rutor
    col1, col2, col3 = st.columns(3)
    col1.metric("Totalt antal matcher", len(df))
    
    # Sökfunktion
    search = st.text_input("Sök efter lag eller domare")
    if search:
        mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df = df[mask]

    # Visa tabellen
    st.subheader("Data")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
