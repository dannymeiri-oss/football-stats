import streamlit as st
import pandas as pd

# --- 1. LADDA DATA (Samma som förut) ---
@st.cache_data(ttl=600)
def load_data():
    # Här använder du din befintliga länk till Google Sheets CSV-export
    sheet_url = "DIN_GOOGLE_SHEETS_URL_HÄR" 
    df = pd.read_csv(sheet_url)
    return df

df = load_data()

# --- 2. NAVIGATION I SIDOFÄLTET ---
st.sidebar.title("⚽ Fotbollsanalys v1.0")
sida = st.sidebar.radio("Gå till:", ["Dagens Matcher", "Lagstatistik & Snitt"])

# --- FLIK 1: DIN BEFINTLIGA MATCHLISTA ---
if sida == "Dagens Matcher":
    st.title("Dagens Matcher")
    # ... här ligger din nuvarande kod för att visa listan och analysen ...
    st.write("Här visas din nuvarande matchlista...")

# --- FLIK 2: DEN NYA LAGSTATISTIKEN ---
elif sida == "Lagstatistik & Snitt":
    st.title("🛡️ Laganalys & Medelvärden")
    
    # Hämta alla unika lag
    alla_lag = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
    valt_lag = st.selectbox("Välj ett lag:", alla_lag)

    if valt_lag:
        # Filtrera ut matcher som är klara (FT) för det valda laget
        lag_df = df[((df['response.teams.home.name'] == valt_lag) | 
                     (df['response.teams.away.name'] == valt_lag)) & 
                    (df['response.fixture.status.short'] == 'FT')].copy()

        if not lag_df.empty:
            # Funktion för att plocka rätt siffra oavsett om laget spela Hemma eller Borta
            def get_team_metrics(row):
                if row['response.teams.home.name'] == valt_lag:
                    return pd.Series([row['response.goals.home'], row['expected_goals H'], row['Gula kort Hemma'], row['Hörnor Hemma']])
                else:
                    return pd.Series([row['response.goals.away'], row['expected_goals B'], row['Gula kort Borta'], row['Hörnor Borta']])

            # Vi mappar mot dina kolumner i Raw Data
            team_stats = lag_df.apply(get_team_metrics, axis=1)
            team_stats.columns = ['Mål', 'xG', 'Gula', 'Hörnor']

            # Visa snygga "KPI-boxar"
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mål/match", round(team_stats['Mål'].mean(), 2))
            c2.metric("xG/match", round(team_stats['xG'].mean(), 2))
            c3.metric("Gula/match", round(team_stats['Gula'].mean(), 2))
            c4.metric("Hörnor/match", round(team_stats['Hörnor'].mean(), 2))

            st.divider()
            st.subheader(f"Historik: {valt_lag}")
            st.dataframe(lag_df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.goals.home', 'response.goals.away']])
        else:
            st.warning("Inga spelade matcher (FT) hittades för detta lag än.")
