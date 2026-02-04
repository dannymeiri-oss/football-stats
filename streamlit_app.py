import streamlit as st
import pandas as pd

# --- KONFIGURATION ---
st.set_page_config(page_title="Fotbollsanalys 2026", layout="wide")

# Din CSV-länk (GID 0 för Raw Data)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        # Rensar bort eventuella helt tomma rader
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

    # --- FLIK 1: DAGENS MATCHER (DIN URSPRUNGLIGA VY) ---
    with tab1:
        st.title("Dagens Analys")
        
        # Här filtrerar vi fram matcher som inte är klara eller dagens matcher
        # (Detta är din befintliga logik)
        st.dataframe(df[[
            'response.fixture.date', 
            'response.teams.home.name', 
            'response.teams.away.name', 
            'response.fixture.status.short'
        ]].tail(20))
        
        st.info("Klicka på fliken ovan för att se fördjupad lagstatistik.")

    # --- FLIK 2: LAGSTATISTIK (DEN NYA SIDAN) ---
    with tab2:
        st.header("Laganalys & Medelvärden")
        
        # Definiera kolumnnamn baserat på din filstruktur
        col_home_team = 'response.teams.home.name'
        col_away_team = 'response.teams.away.name'
        col_status = 'response.fixture.status.short'
        
        # Skapa en lista på alla unika lag
        all_teams = sorted(pd.concat([df[col_home_team], df[col_away_team]]).unique())
        selected_team = st.selectbox("Välj ett lag att analysera:", all_teams)

        if selected_team:
            # Filtrera fram matcher där laget deltagit och matchen är klar (FT)
            team_df = df[((df[col_home_team] == selected_team) | 
                         (df[col_away_team] == selected_team)) & 
                        (df[col_status] == 'FT')].copy()

            if not team_df.empty:
                # Funktion för att hämta statistik oavsett om laget var hemma eller borta
                def calculate_metrics(row):
                    if row[col_home_team] == selected_team:
                        return pd.Series([
                            row.get('response.goals.home', 0), 
                            row.get('expected_goals H', 0), 
                            row.get('Gula kort Hemma', 0)
                        ])
                    else:
                        return pd.Series([
                            row.get('response.goals.away', 0), 
                            row.get('expected_goals B', 0), 
                            row.get('Gula kort Borta', 0)
                        ])

                # Beräkna värden
                stats_df = team_df.apply(calculate_metrics, axis=1)
                stats_df.columns = ['Mål', 'xG', 'Gula Kort']

                # Visa medelvärden i snygga boxar
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Snitt Mål", round(stats_df['Mål'].mean(), 2))
                m2.metric("Snitt xG", round(stats_df['xG'].mean(), 2))
                m3.metric("Snitt Gula Kort", round(stats_df['Gula Kort'].mean(), 2))
                m4.metric("Matcher spelade", len(team_df))

                st.divider()
                st.subheader(f"Senaste matcher för {selected_team}")
                st.dataframe(team_df[[
                    'response.fixture.date', 
                    col_home_team, 
                    col_away_team, 
                    'response.goals.home', 
                    'response.goals.away'
                ]].sort_values('response.fixture.date', ascending=False))
            else:
                st.warning(f"Ingen historik (status FT) hittades för {selected_team} än.")

    # --- FELSÖKARE (Dold som standard) ---
    with st.expander("🛠️ Felsökning: Se kolumnnamn"):
        st.write("Om statistiken visar 0 kan det bero på att kolumnnamnen i Google Sheets ändrats.")
        st.write(df.columns.tolist())

else:
    st.error("Datan kunde inte läsas in. Kontrollera att ditt Google Sheet är delat publikt.")
