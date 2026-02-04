import streamlit as st
import pandas as pd  # <--- Fixat här!

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
        HOME_COL = 'response.teams.home.name'
        AWAY_COL = 'response.teams.away.name'
        SEASON_COL = 'response.league.season'
        
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
                def map_row(row):
                    is_h = row[HOME_COL] == team_name
                    s = " Hemma" if is_h else " Borta"
                    g_key = "Gula kort Hemma" if is_h else "Gula Kort Borta"
                    return pd.Series({
                        'Mål': row['response.goals.home'] if is_h else row['response.goals.away'],
                        'xG': row.get(f'xG{s}', 0),
                        'Hörnor': row.get(f'Hörnor{s}', 0),
                        'Bollinnehav': row.get(f'Bollinnehav{s}', 0),
                        'Skott på mål': row.get(f'Skott på mål{s}', 0),
                        'Totala Skott': row.get(f'Total Skott{s}', 0),
                        'Skott Utanför': row.get(f'Skott Utanför{s}', 0),
                        'Blockerade Skott': row.get(f'Blockerade Skott{s}', 0),
                        'Skott i Box': row.get(f'Skott i Box{s}', 0),
                        'Skott utanför Box': row.get(f'Skott utanför Box{s}', 0),
                        'Passningar': row.get(f'Passningar{s}', 0),
                        'Passningssäkerhet': row.get(f'Passningssäkerhet{s}', 0),
                        'Fouls': row.get(f'Fouls{s}', 0),
                        'Gula Kort': row.get(g_key, 0),
                        'Röda Kort': row.get(f'Röda Kort{s}', 0),
                        'Offside': row.get(f'Offside{s}', 0),
                        'Räddningar': row.get(f'Räddningar{s}', 0)
                    })
                return target_df.apply(map_row, axis=1).mean().round(2)

            def display_stat_block(label, data_series, count):
                st.subheader(f"{label} ({count} matcher)")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Mål", data_series['Mål'])
                k2.metric("xG", data_series['xG'])
                k3.metric("Hörnor", data_series['Hörnor'])
                k4.metric("Boll", f"{data_series['Bollinnehav']}%")
                
                with st.expander(f"Visa all statistik för {label.lower()}"):
                    ca, cb, cc = st.columns(3)
                    with ca:
                        st.write("**Anfall**")
                        st.write(f"Skott på mål: {data_series['Skott på mål']}")
                        st.write(f"Totala skott: {data_series['Totala Skott']}")
                        st.write(f"Skott i box: {data_series['Skott i Box']}")
                    with cb:
                        st.write("**Speluppbyggnad**")
                        st.write(f"Passningar: {data_series['Passningar']}")
                        st.write(f"Säkerhet: {data_series['Passningssäkerhet']}%")
                        st.write(f"Offside: {data_series['Offside']}")
                    with cc:
                        st.write("**Defensiv/Disciplin**")
                        st.write(f"Fouls: {data_series['Fouls']}")
                        st.write(f"Gula kort: {data_series['Gula Kort']}")
                        st.write(f"Räddningar: {data_series['Räddningar']}")

            # 1. TOTALT
            avg_total = get_full_stats(stats_df, selected_team)
            display_stat_block("TOTALT", avg_total, len(stats_df))
            
            st.divider()
            
            # 2. HEMMA & BORTA
            col_h, col_a = st.columns(2)
            with col_h:
                h_df = stats_df[stats_df[HOME_COL] == selected_team]
                if not h_df.empty:
                    avg_h = get_full_stats(h_df, selected_team)
                    display_stat_block("🏠 HEMMA", avg_h, len(h_df))
            with col_a:
                a_df = stats_df[stats_df[AWAY_COL] == selected_team]
                if not a_df.empty:
                    avg_a = get_full_stats(a_df, selected_team)
                    display_stat_block("✈️ BORTA", avg_a, len(a_df))
