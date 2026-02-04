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
    tab1, tab2 = st.tabs(["⚽ Matcher", "🛡️ Lagstatistik"])

    with tab1:
        st.dataframe(df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.status.short', 'response.goals.home', 'response.goals.away']].sort_values('response.fixture.date', ascending=False), use_container_width=True)

    with tab2:
        HOME_COL, AWAY_COL, SEASON_COL = 'response.teams.home.name', 'response.teams.away.name', 'response.league.season'
        
        # Filter
        f1, f2, f3 = st.columns(3)
        with f1:
            selected_team = st.selectbox("Välj lag:", sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique()))
        with f2:
            selected_season = st.selectbox("Säsong:", ["Alla"] + sorted(list(df[SEASON_COL].unique()), reverse=True))
        with f3:
            num_matches = st.radio("Urval:", ["Samtliga", "Senaste 20"], horizontal=True)

        if selected_team:
            # Filtrera spelade matcher
            s_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()
            if selected_season != "Alla": s_df = s_df[s_df[SEASON_COL] == selected_season]
            s_df = s_df.sort_values('response.fixture.date', ascending=False)
            if num_matches == "Senaste 20": s_df = s_df.head(20)

            def get_stats(target_df, team_name):
                if target_df.empty: return None
                def map_row(row):
                    is_h = row[HOME_COL] == team_name
                    s = " Hemma" if is_h else " Borta"
                    g_key = "Gula kort Hemma" if is_h else "Gula Kort Borta"
                    return pd.Series({
                        'Mål': row['response.goals.home'] if is_h else row['response.goals.away'],
                        'xG': row.get(f'xG{s}', 0), 'Hörnor': row.get(f'Hörnor{s}', 0), 'Boll': row.get(f'Bollinnehav{s}', 0),
                        'S_mål': row.get(f'Skott på mål{s}', 0), 'S_tot': row.get(f'Total Skott{s}', 0),
                        'S_ut': row.get(f'Skott Utanför{s}', 0), 'S_block': row.get(f'Blockerade Skott{s}', 0),
                        'S_box': row.get(f'Skott i Box{s}', 0), 'S_ut_box': row.get(f'Skott utanför Box{s}', 0),
                        'Pass': row.get(f'Passningar{s}', 0), 'Pass_%': row.get(f'Passningssäkerhet{s}', 0),
                        'Fouls': row.get(f'Fouls{s}', 0), 'Gula': row.get(g_key, 0), 'Röda': row.get(f'Röda Kort{s}', 0),
                        'Offside': row.get(f'Offside{s}', 0), 'Rädd': row.get(f'Räddningar{s}', 0)
                    })
                return target_df.apply(map_row, axis=1).mean().round(2)

            avg_t = get_stats(s_df, selected_team)
            avg_h = get_stats(s_df[s_df[HOME_COL] == selected_team], selected_team)
            avg_a = get_stats(s_df[s_df[AWAY_COL] == selected_team], selected_team)

            # --- PRESENTATION UTAN EXPANDERS ---
            st.header(f"Statistik: {selected_team}")
            
            # Gruppera statistik för snyggare layout
            stat_groups = [
                ("Huvudstatistik", [('Mål', 'Mål'), ('xG', 'xG'), ('Hörnor', 'Hörnor'), ('Bollinnehav %', 'Boll')]),
                ("Anfall", [('Skott på mål', 'S_mål'), ('Totala skott', 'S_tot'), ('Skott i box', 'S_box'), ('Skott utanför box', 'S_ut_box'), ('Blockerade skott', 'S_block')]),
                ("Speluppbyggnad", [('Passningar', 'Pass'), ('Passningssäkerhet %', 'Pass_%'), ('Offside', 'Offside')]),
                ("Defensiv & Disciplin", [('Fouls', 'Fouls'), ('Gula kort', 'Gula'), ('Röda kort', 'Röda'), ('Räddningar', 'Rädd')])
            ]

            for group_name, stats in stat_groups:
                st.subheader(group_name)
                for label, key in stats:
                    # Skapa en rad för varje stat med etikett och tre värden
                    col_label, col_t, col_h, col_a = st.columns([2, 1, 1, 1])
                    col_label.write(f"**{label}**")
                    col_t.metric("TOTALT", avg_t[key] if avg_t is not None else "-")
                    col_h.metric("HEMMA", avg_h[key] if avg_h is not None else "-")
                    col_a.metric("BORTA", avg_a[key] if avg_a is not None else "-")
                st.divider()
