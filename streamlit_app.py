import streamlit as st
import pandas as pd

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Matchcenter", layout="wide")

BASE_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid=0"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

df = load_data(RAW_DATA_URL)

if df is not None:
    st.title("⚽ Kommande Matcher")

    # 1. Säkerställ att datumet är sökbart
    df['datetime'] = pd.to_datetime(df['response.fixture.date'], errors='coerce')

    # 2. Filtrera fram endast matcher som inte startat (NS eller TBD)
    # Vi kollar kolumnen 'response.fixture.status.short'
    kommande_matcher = df[df['response.fixture.status.short'].isin(['NS', 'TBD'])]

    # 3. Sortera: Närmast i tid först
    kommande_matcher = kommande_matcher.sort_values('datetime', ascending=True)

    # 4. Ta de 50 närmaste
    nasta_50 = kommande_matcher.head(50)

    if nasta_50.empty:
        st.info("Hittade inga matcher med status 'NS' i ditt ark.")
    else:
        for index, row in nasta_50.iterrows():
            # Snygga till datumet: "Lördag 14 Feb 21:00"
            tid_str = row['datetime'].strftime('%d %b %H:%M') if pd.notnull(row['datetime']) else "Tid ej satt"
            
            h_team = row['response.teams.home.name']
            a_team = row['response.teams.away.name']
            liga = row.get('response.league.name', 'Liga')

            # Renderar matchkortet
            st.markdown(f"""
            <div style="background:white; padding:12px; border-radius:10px; border:1px solid #eee; margin-bottom:8px; display:flex; align-items:center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="width:110px; color:#555; font-size:0.85em; font-weight:bold;">{tid_str}</div>
                <div style="flex:1; text-align:right; font-size:1.1em; padding-right:15px;">{h_team}</div>
                <div style="background:#f8f9fa; color:#333; padding:4px 10px; border-radius:4px; font-weight:bold; border:1px solid #ddd;">VS</div>
                <div style="flex:1; text-align:left; font-size:1.1em; padding-left:15px;">{a_team}</div>
                <div style="width:120px; text-align:right; color:#888; font-size:0.8em; font-style:italic;">{liga}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.error("Kunde inte läsa in Google Sheet-data.")
