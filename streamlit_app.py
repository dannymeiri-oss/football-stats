import streamlit as st
import pandas as pd

# --- KONFIGURATION ---
st.set_page_config(page_title="Fotbollsanalys 2026", layout="wide")

# Din CSV-länk
SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        # Rensar bort helt tomma rader baserat på Fixture ID
        data = data.dropna(subset=['response.fixture.id'])
        return data
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return None

# --- LADDA DATA ---
df = load_data()

if df is not None:
    # --- NAVIGATION ---
    tab1, tab2 = st.tabs(["⚽ Dagens Matcher", "🛡️ Lagstatistik (Snitt)"])

    # --- FLIK 1: DAGENS MATCHER ---
    with tab1:
        st.title("Dagens Analys")
        # Din befintliga vy (justerad för att visa de senaste raderna)
        st.dataframe(df[[
            'response.fixture.date', 
            'response.teams.home.name', 
            'response.teams.away.name', 
            'response.fixture.status.short'
        ]].tail(20))

    # --- FLIK 2: LAGSTATISTIK (NU HELT KORREKT MAPPAD) ---
    with tab2:
        st.header("Laganalys & Medelvärden")
        
        # Exakta kolumnnamn från din lista
        HOME_TEAM_COL = 'response.teams.home.name'
        AWAY_TEAM_COL = 'response.teams.away.name'
        STATUS_COL = 'response.fixture.status.short'
        
        # Skapa lista på alla unika lag
        all_teams = sorted(pd.concat([df[HOME_TEAM_COL], df[AWAY_TEAM_COL]]).unique())
        selected_team = st.selectbox("Välj ett lag för analys:", all_teams)

        if selected_team:
            # Filtrera fram matcher där laget deltagit och status är FT (klara)
            team_df = df[((df[HOME_TEAM_COL] == selected_team) | 
                         (df[AWAY_TEAM_COL] == selected_team)) & 
                        (df[STATUS_COL] == 'FT')].copy()

            if not team_df.empty:
                # Funktion för att hämta statistik baserat på om laget var hemma eller borta
                # Vi mappar här mot dina exakta kolumner (47 till 78 i din lista)
                def calculate_team_metrics(row):
                    if row[HOME_TEAM_COL] == selected_team:
                        return pd.Series([
                            row.get('response.goals.home', 0),
                            row.get('xG Hemma', 0),
                            row.get('Gula kort Hemma', 0),
                            row.get('Hörnor Hemma', 0),
                            row.get('Skott på mål Hemma', 0)
                        ])
                    else:
                        return pd.Series([
                            row.get('response.goals.away', 0),
                            row.get('xG Borta', 0),
                            row.get('Gula Kort Borta', 0), # Notera stort K här från din lista
                            row.get('Hörnor Borta', 0),
                            row.get('Skott på mål Borta', 0)
                        ])

                # Applicera logiken
                stats_df = team_df.apply(calculate_team_metrics, axis=1)
                stats_df.columns = ['Mål', 'xG', 'Gula Kort', 'Hörnor', 'Skott på mål']

                # Visa medelvärden i boxar
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Snitt Mål", round(stats_df['Mål'].mean(), 2))
                m2.metric("Snitt xG", round(stats_df['xG'].mean(), 2))
                m3.metric("Snitt Gula", round(stats_df['Gula Kort'].mean(), 2))
                m4.metric("Snitt Hörnor", round(stats_df['Hörnor'].mean(), 2))
                m5.metric("Matcher spelade", len(team_df))

                st.divider()
                st.subheader(f"Historik: {selected_team}")
                # Visar de viktigaste kolumnerna i tabellen
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
                st.warning(f"Ingen färdigspelad historik hittades för {selected_team}.")

else:
    st.error("Datan kunde inte laddas. Kontrollera att Google Sheet är publikt delat.")
