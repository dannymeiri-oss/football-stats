import streamlit as st
import pandas as pd

# 1. Hämta datan
SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(SHEET_URL)

df = load_data()

# 2. Skapa flikar istället för radiobuttons (Snyggare och stör inte din layout)
tab1, tab2 = st.tabs(["⚽ Dagens Matcher", "🛡️ Lagstatistik (Snitt)"])

with tab1:
    # HÄR KLISTRAR DU IN DIN BEFINTLIGA KOD FÖR MATCHLISTAN
    # Den kommer se ut exakt som du vill ha den
    st.title("Dagens Matcher")
    st.write("Din nuvarande analysvy...")

with tab2:
    st.header("Laganalys per Lag")
    
    # Hämta lag från kolumnerna i din bild (G, H, etc)
    all_teams = sorted(list(set(df['response.teams.home.name']) | set(df['response.teams.away.name'])))
    selected_team = st.selectbox("Välj ett lag för medelvärden:", all_teams)
    
    if selected_team:
        # Filtrera matcher för valt lag som är klara (FT)
        team_df = df[((df['response.teams.home.name'] == selected_team) | 
                     (df['response.teams.away.name'] == selected_team)) & 
                    (df['response.fixture.status.short'] == 'FT')].copy()
        
        if not team_df.empty:
            # Räkna ut snitt för Mål, xG och Gula kort
            def get_stats(row):
                if row['response.teams.home.name'] == selected_team:
                    return pd.Series([row['response.goals.home'], row['expected_goals H'], row['Gula kort Hemma']])
                else:
                    return pd.Series([row['response.goals.away'], row['expected_goals B'], row['Gula kort Borta']])

            res = team_df.apply(get_stats, axis=1)
            res.columns = ['Mål', 'xG', 'Gula']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Mål/match", round(res['Mål'].mean(), 2))
            c2.metric("xG/match", round(res['xG'].mean(), 2))
            c3.metric("Gula/match", round(res['Gula'].mean(), 2))
            
            st.divider()
            st.subheader("Historik")
            st.dataframe(team_df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.goals.home', 'response.goals.away']])
