import streamlit as st
import pandas as pd

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Fotbollsanalys 2026", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data.columns = [col.strip() for col in data.columns]
        data = data.dropna(subset=['response.fixture.id'])
        
        cols_to_clean = [
            'response.goals.home', 'response.goals.away', 'xG Hemma', 'xG Borta',
            'Gula kort Hemma', 'Gula Kort Borta', 'Röda Kort Hemma', 'Röda Kort Borta',
            'Bollinnehav Hemma', 'Bollinnehav Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
            'Hörnor Hemma', 'Hörnor Borta', 'Fouls Hemma', 'Fouls Borta',
            'Total Skott Hemma', 'Total Skott Borta', 'Skott Utanför Hemma', 'Skott Utanför Borta',
            'Blockerade Skott Hemma', 'Blockerade Skott Borta', 'Skott i Box Hemma', 'Skott i Box Borta',
            'Skott utanför Box Hemma', 'Skott utanför Box Borta', 'Passningar Hemma', 'Passningar Borta',
            'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 'Offside Hemma', 'Offside Borta',
            'Räddningar Hemma', 'Räddningar Borta'
        ]
        
        for col in cols_to_clean:
            if col in data.columns:
                data[col] = data[col].astype(str).str.replace('%', '').str.replace(',', '.')
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
        return data
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return None

df = load_data()

if df is not None:
    tab1, tab2 = st.tabs(["⚽ Matcher", "🛡️ Djupgående Lagstatistik"])

    with tab1:
        st.title("Matcher i Arket")
        st.dataframe(df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.status.short']].tail(50))

    # --- FLIK 2: UPPDATERAD MED FILTER FÖR SÄSONG OCH ANTAL MATCHER ---
    with tab2:
        st.header("Laganalys & Medelvärden")
        
        HOME_COL = 'response.teams.home.name'
        AWAY_COL = 'response.teams.away.name'
        SEASON_COL = 'response.league.season'
        
        # 1. Rad med filter
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            all_teams = sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique())
            selected_team = st.selectbox("Välj lag:", all_teams)
            
        with f_col2:
            # Hämtar unika säsonger från arket
            seasons = sorted(df[SEASON_COL].unique(), reverse=True)
            selected_season = st.selectbox("Välj säsong:", ["Alla"] + list(seasons))
            
        with f_col3:
            num_matches = st.radio("Visa data för:", ["Samtliga matcher", "Senaste 20 matcher"], horizontal=True)

        if selected_team:
            # Filtrera fram lagets matcher (status FT)
            team_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()

            # Applicera Säsongsfilter
            if selected_season != "Alla":
                team_df = team_df[team_df[SEASON_COL] == selected_season]

            # Sortera efter datum (senaste först)
            team_df = team_df.sort_values('response.fixture.date', ascending=False)

            # Applicera filter för "Senaste 20"
            if num_matches == "Senaste 20 matcher":
                team_df = team_df.head(20)

            if not team_df.empty:
                def get_all_stats(row):
                    is_home = row[HOME_COL] == selected_team
                    suffix = " Hemma" if is_home else " Borta"
                    gula_key = "Gula kort Hemma" if is_home else "Gula Kort Borta"
                    
                    return pd.Series({
                        'Mål': row['response.goals.home'] if is_home else row['response.goals.away'],
                        'xG': row.get(f'xG{suffix}', 0),
                        'Gula': row.get(gula_key, 0),
                        'Röda': row.get(f'Röda Kort{suffix}', 0),
                        'Bollinnehav': row.get(f'Bollinnehav{suffix}', 0),
                        'Hörnor': row.get(f'Hörnor{suffix}', 0),
                        'Skott på mål': row.get(f'Skott på mål{suffix}', 0),
                        'Total Skott': row.get(f'Total Skott{suffix}', 0),
                        'Skott Utanför': row.get(f'Skott Utanför{suffix}', 0),
                        'Blockerade Skott': row.get(f'Blockerade Skott{suffix}', 0),
                        'Skott i Box': row.get(f'Skott i Box{suffix}', 0),
                        'Skott utanför Box': row.get(f'Skott utanför Box{suffix}', 0),
                        'Fouls': row.get(f'Fouls{suffix}', 0),
                        'Passningar': row.get(f'Passningar{suffix}', 0),
                        'Passningssäkerhet': row.get(f'Passningssäkerhet{suffix}', 0),
                        'Offside': row.get(f'Offside{suffix}', 0),
                        'Räddningar': row.get(f'Räddningar{
