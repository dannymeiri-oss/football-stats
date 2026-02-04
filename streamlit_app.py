import streamlit as st
import pandas as pd

# --- KONFIGURATION ---
# Ersätt med din faktiska länk från Google Sheets (viktigt att den slutar på export?format=csv)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(SHEET_URL)

try:
    df = load_data()
    
    # NAVIGATION
    st.sidebar.title("📊 Navigering")
    page = st.sidebar.radio("Välj sida:", ["Dagens Matcher", "Lagstatistik (Medel)"])

    # --- SIDA: DAGENS MATCHER ---
    if page == "Dagens Matcher":
        st.title("⚽ Dagens Matcher")
        st.write("Här kan du se dina vanliga analyser.")
        # [Här klistrar du in din gamla kod för matchlistan]

    # --- SIDA: LAGSTATISTIK ---
    elif page == "Lagstatistik (Medel)":
        st.title("🛡️ Laganalys per Lag")
        
        # Hämta unika lag (vi använder kolumnnamnen från din bild)
        home_teams = df['response.teams.home.name'].unique()
        away_teams = df['response.teams.away.name'].unique()
        all_teams = sorted(list(set(home_teams) | set(away_teams)))
        
        selected_team = st.selectbox("Välj ett lag för att se snittstatistik:", all_teams)
        
        if selected_team:
            # Filtrera fram bara matcher som är klara (FT)
            finished_games = df[df['response.fixture.status.short'] == 'FT']
            
            # Matcher där laget spelat hemma ELLER borta
            team_df = finished_games[(finished_games['response.teams.home.name'] == selected_team) | 
                                    (finished_games['response.teams.away.name'] == selected_team)]
            
            if not team_df.empty:
                # Beräkna medelvärden (Vi anpassar efter dina kolumner)
                total_games = len(team_df)
                
                # Exempel på logik för att hämta RÄTT mål oavsett hemma/borta
                goals = team_df.apply(lambda x: x['response.goals.home'] if x['response.teams.home.name'] == selected_team else x['response.goals.away'], axis=1)
                
                # Här mappar vi mot de nya statistik-kolumnerna vi skapade (AV-CA)
                # OBS: Se till att namnen matchar exakt dina rubriker i arket!
                yellow_cards = team_df.apply(lambda x: x['Gula kort Hemma'] if x['response.teams.home.name'] == selected_team else x['Gula kort Borta'], axis=1)
                
                st.subheader(f"Statistik för {selected_team} (Baserat på {total_games} matcher)")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Medel mål", round(goals.mean(), 2))
                col2.metric("Medel Gula kort", round(yellow_cards.mean(), 2))
                col3.metric("Antal spelade", total_games)
                
                st.divider()
                st.write("Senaste resultaten:")
                st.dataframe(team_df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.goals.home', 'response.goals.away']])
            else:
                st.info("Hittade inga spelade matcher (FT) för detta lag ännu.")

except Exception as e:
    st.error(f"Kunde inte ladda datan. Kontrollera URL:en. Felmeddelande: {e}")
