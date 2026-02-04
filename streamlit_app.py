import streamlit as st
import pandas as pd
import numpy as np

# --- KONFIGURATION ---
st.set_page_config(page_title="Fotbollsanalys 2026", layout="wide")

# Din CSV-länk
SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    try:
        # Läs in data och tvinga vissa kolumner att hanteras som strängar för att undvika fel vid inläsning
        data = pd.read_csv(SHEET_URL)
        data = data.dropna(subset=['response.fixture.id'])
        
        # Säkerställ att statistik-kolumner är numeriska (viktigt för medelvärden)
        cols_to_fix = ['xG Hemma', 'xG Borta', 'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta']
        for col in cols_to_fix:
            if col in data.columns:
                # Gör om '-' eller tomma celler till 0
                data[col] = pd.to_numeric(data[col].replace('-', 0), errors='coerce').fillna(0)
        
        return data
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return None

# --- LADDA DATA ---
df = load_data()

if df is not None:
    # --- NAVIGATION (Bevarar dina flikar) ---
    tab1, tab2 = st.tabs(["⚽ Dagens Matcher", "🛡️ Lagstatistik (Snitt)"])

    # --- FLIK 1: DAGENS MATCHER (DIN ORIGINAL-VY) ---
    with tab1:
        st.title("Dagens Matcher")
        # Visar de 20 senaste raderna precis som förut
        st.dataframe(df[[
            'response.fixture.date', 
            'response.teams.home.name', 
            'response.teams.away.name', 
            'response.fixture.status.short'
        ]].tail(20))

    # --- FLIK 2: LAGSTATISTIK (HELT KORREKT MAPPAD) ---
    with tab2:
        st.header("Laganalys & Medelvärden")
        
        HOME_TEAM_COL = 'response.teams.home.name'
        AWAY_TEAM_COL = 'response.teams.away.name'
        STATUS_COL = 'response.fixture.status.short'
        
        # Skapa laglista
        all_teams = sorted(pd.concat([df[HOME_TEAM_COL], df[AWAY_TEAM_COL]]).unique())
        selected_team = st.selectbox("Välj ett lag för analys:", all_teams)

        if selected_team:
            # Filtrera matcher (bara FT)
            team_df = df[((df[HOME_TEAM_COL] == selected_team) | 
                         (df[AWAY_TEAM_COL] == selected_team)) & 
                        (df[STATUS_COL] == 'FT')].copy()

            if not team_df.empty:
                # Logik för att plocka data baserat på Hemma/Borta
                def calculate_team_metrics(row):
                    if row[HOME_TEAM_COL] == selected_team:
                        return pd.Series([
                            row.get('response.goals.home', 0),
                            row.get('xG Hemma', 0),
                            row.get('Gula kort Hemma', 0),
                            row.get('Hörnor Hemma', 0)
                        ])
                    else:
                        return pd.Series([
                            row.get('response.goals.away', 0),
                            row.get('xG Borta', 0),
                            row.get('Gula Kort Borta', 0),
                            row.get('Hörnor Borta', 0)
                        ])

                stats_df = team_df.apply(calculate_team_metrics, axis=1)
                stats_df.columns = ['Mål', 'xG', 'Gula', 'Hörnor']

                # Visa medelvärden i boxar
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Snitt Mål", round(stats_df['Mål'].mean(), 2))
                m2.metric("Snitt xG", round(stats_df['xG'].mean(), 2))
                m3.metric("Snitt Gula", round(stats_df['Gula'].mean(), 2))
                m4.metric("Snitt Hörnor", round(stats_df['Hörnor'].mean(), 2))

                st.divider()
                st.subheader(f"Historik: {selected_team}")
                st.dataframe(team_df[[
                    'response.fixture.date', 
                    HOME_TEAM_COL, 
                    AWAY_TEAM_COL, 
                    'response.goals.home', 
                    'response.goals.away',
                    'xG Hemma',
                    'xG Borta'
                ]].sort_values('response.fixture.date', ascending=False))
            else:
                st.info(f"Hittade inga spelade matcher (FT) för {selected_team}.")

else:
    st.error("Datan kunde inte laddas. Kontrollera att arket är publikt delat.")
