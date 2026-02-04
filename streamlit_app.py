import streamlit as st
import pandas as pd

# --- KONFIGURATION ---
st.set_page_config(page_title="Fotbollsanalys 2026", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        # 1. Rensa alla kolumnnamn från osynliga mellanslag i början/slutet
        data.columns = [col.strip() for col in data.columns]
        
        data = data.dropna(subset=['response.fixture.id'])
        
        # 2. Lista på kolumner att tvätta (numerisk konvertering)
        cols_to_clean = [
            'xG Hemma', 'xG Borta', 
            'Hörnor Hemma', 'Hörnor Borta', 
            'Gula kort Hemma', 'Gula Kort Borta',
            'response.goals.home', 'response.goals.away'
        ]
        
        for col in cols_to_clean:
            if col in data.columns:
                # Byt ut eventuella komman och gör till siffror
                data[col] = data[col].astype(str).str.replace(',', '.')
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
        return data
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return None

df = load_data()

if df is not None:
    tab1, tab2 = st.tabs(["⚽ Dagens Matcher", "🛡️ Lagstatistik (Snitt)"])

    # --- FLIK 1: DAGENS MATCHER ---
    with tab1:
        st.title("Dagens Matcher")
        st.dataframe(df[[
            'response.fixture.date', 
            'response.teams.home.name', 
            'response.teams.away.name', 
            'response.fixture.status.short'
        ]].tail(20))

    # --- FLIK 2: LAGSTATISTIK ---
    with tab2:
        st.header("Laganalys & Medelvärden")
        
        HOME_COL = 'response.teams.home.name'
        AWAY_COL = 'response.teams.away.name'
        
        # Hämta laglista
        all_teams = sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique())
        selected_team = st.selectbox("Välj ett lag:", all_teams)

        if selected_team:
            # Filtrera bara färdiga matcher (FT)
            team_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & 
                        (df['response.fixture.status.short'] == 'FT')].copy()

            if not team_df.empty:
                # Plocka statistik baserat på hemma/borta-roll
                def get_team_stats(row):
                    if row[HOME_COL] == selected_team:
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

                stats_df = team_df.apply(get_team_stats, axis=1)
                stats_df.columns = ['Mål', 'xG', 'Gula', 'Hörnor']

                # Visa medelvärden
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Snitt Mål", round(stats_df['Mål'].mean(), 2))
                m2.metric("Snitt xG", round(stats_df['xG'].mean(), 2))
                m3.metric("Snitt Gula", round(stats_df['Gula'].mean(), 2))
                m4.metric("Snitt Hörnor", round(stats_df['Hörnor'].mean(), 2))

                st.divider()
                st.subheader(f"Historik: {selected_team}")
                # Visa tabell för att kontrollera att siffrorna finns där
                st.dataframe(team_df[[
                    'response.fixture.date', HOME_COL, AWAY_COL, 
                    'response.goals.home', 'response.goals.away', 
                    'Hörnor Hemma', 'Hörnor Borta'
                ]].sort_values('response.fixture.date', ascending=False))
            else:
                st.info("Inga spelade matcher hittades för detta lag.")
