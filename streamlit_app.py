import streamlit as st
import pandas as pd

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Deep Stats 2026", layout="wide")

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
        st.title("Matchlista")
        st.dataframe(df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.status.short', 'response.goals.home', 'response.goals.away']].sort_values('response.fixture.date'), use_container_width=True)

    with tab2:
        HOME_COL, AWAY_COL, SEASON_COL = 'response.teams.home.name', 'response.teams.away.name', 'response.league.season'
        
        f1, f2, f3 = st.columns(3)
        with f1:
            all_teams = sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique())
            selected_team = st.selectbox("Välj lag:", all_teams)
        with f2:
            seasons = sorted(df[SEASON_COL].unique(), reverse=True)
            selected_season = st.selectbox("Säsong:", ["Alla"] + list(seasons))
        with f3:
            num_matches = st.radio("Urval:", ["Samtliga", "Senaste 20"], horizontal=True)

        if selected_team:
            stats_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()
            if selected_season != "Alla":
                stats_df = stats_df[stats_df[SEASON_COL] == selected_season]
            stats_df = stats_df.sort_values('response.fixture.date', ascending=False)
            if num_matches == "Senaste 20":
                stats_df = stats_df.head(20)

            def get_full_stats(target_df, team_name):
                if target_df.empty: return None
                def map_row(row):
                    is_h = row[HOME_COL] == team_name
                    s = " Hemma" if is_h else " Borta"
                    g_key = "Gula kort Hemma" if is_h else "Gula Kort Borta"
                    return pd.Series({
                        'Mål': row['response.goals.home'] if is_h else row['response.goals.away'],
                        'xG': row.get(f'xG{s}', 0), 'Hörnor': row.get(f'Hörnor{s}', 0),
                        'Bollinnehav': row.get(f'Bollinnehav{s}', 0), 'Skott på mål': row.get(f'Skott på mål{s}', 0),
                        'Totala Skott': row.get(f'Total Skott{s}', 0), 'Skott Utanför': row.get(f'Skott Utanför{s}', 0),
                        'Blockerade Skott': row.get(f'Blockerade Skott{s}', 0), 'Skott i Box': row.get(f'Skott i Box{s}', 0),
                        'Skott utanför Box': row.get(f'Skott utanför Box{s}', 0), 'Passningar': row.get(f'Passningar{s}', 0),
                        'Passningssäkerhet': row.get(f'Passningssäkerhet{s}', 0), 'Fouls': row.get(f'Fouls{s}', 0),
                        'Gula Kort': row.get(g_key, 0), 'Röda Kort': row.get(f'Röda Kort{s}', 0),
                        'Offside': row.get(f'Offside{s}', 0), 'Räddningar': row.get(f'Räddningar{s}', 0)
                    })
                return target_df.apply(map_row, axis=1).mean().round(2)

            # Hämta data
            avg_t = get_full_stats(stats_df, selected_team)
            avg_h = get_full_stats(stats_df[stats_df[HOME_COL] == selected_team], selected_team)
            avg_a = get_full_stats(stats_df[stats_df[AWAY_COL] == selected_team], selected_team)

            # --- PRESENTATION I TABELLFORM FÖR DIREKT ÖVERBLICK ---
            st.subheader(f"Statistik för {selected_team}")
            
            # Vi skapar en snygg lista för alla rader
            metrics = [
                ('⚽ Mål', 'Mål'), ('📈 xG', 'xG'), ('🚩 Hörnor', 'Hörnor'), ('⏱️ Bollinnehav (%)', 'Bollinnehav'),
                ('🎯 Skott på mål', 'Skott på mål'), ('🚀 Totala Skott', 'Totala Skott'), ('📉 Skott Utanför', 'Skott Utanför'),
                ('🛡️ Blockerade Skott', 'Blockerade Skott'), ('📦 Skott i Box', 'Skott i Box'), ('🏟️ Skott utanför Box', 'Skott utanför Box'),
                ('🔄 Passningar', 'Passningar'), ('✅ Passningssäkerhet (%)', 'Passningssäkerhet'), ('⚠️ Fouls', 'Fouls'),
                ('🟨 Gula Kort', 'Gula Kort'), ('🟥 Röda Kort', 'Röda Kort'), ('🚩 Offside', 'Offside'), ('🧤 Räddningar', 'Räddningar')
            ]

            # Header
            head_col1, head_col2, head_col3, head_col4 = st.columns([2, 1, 1, 1])
            head_col1.write("**Kategori**")
            head_col2.write("**TOTALT**")
            head_col3.write("**HEMMA**")
            head_col4.write("**BORTA**")
            st.divider()

            for label, key in metrics:
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(label)
                c2.write(f"**{avg_t[key]}**" if avg_t is not None else "-")
                c3.write(str(avg_h[key]) if avg_h is not None else "-")
                c4.write(str(avg_a[key]) if avg_a is not None else "-")
                st.write("---") # En tunn linje mellan varje rad för läsbarhet
