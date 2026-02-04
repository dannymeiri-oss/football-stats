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
        st.title("Matchlista")
        st.dataframe(df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.status.short', 'response.goals.home', 'response.goals.away']].sort_values('response.fixture.date', ascending=False), use_container_width=True)

    with tab2:
        HOME_COL, AWAY_COL, SEASON_COL = 'response.teams.home.name', 'response.teams.away.name', 'response.league.season'
        
        f1, f2, f3 = st.columns(3)
        with f1:
            selected_team = st.selectbox("Välj lag:", sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique()))
        with f2:
            selected_season = st.selectbox("Säsong:", ["Alla"] + sorted(list(df[SEASON_COL].unique()), reverse=True))
        with f3:
            num_matches = st.radio("Urval:", ["Samtliga", "Senaste 20"], horizontal=True)

        if selected_team:
            # Filtrera spelade matcher för statistik
            s_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()
            if selected_season != "Alla": s_df = s_df[s_df[SEASON_COL] == selected_season]
            s_df = s_df.sort_values('response.fixture.date', ascending=False)
            if num_matches == "Senaste 20": s_df = s_df.head(20)

            def get_full_metrics(target_df, team_name):
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

            def render_full_view(title, data, count):
                if data is None: 
                    st.warning(f"Ingen data tillgänglig för {title}")
                    return
                st.markdown(f"---")
                st.header(f"{title} ({count} matcher)")
                
                # Rad 1: Huvudfokus
                r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                r1_1.metric("Mål", data['Mål'])
                r1_2.metric("xG", data['xG'])
                r1_3.metric("Hörnor", data['Hörnor'])
                r1_4.metric("Bollinnehav", f"{data['Boll']}%")

                # Rad 2: Skottdetaljer
                r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                r2_1.metric("Skott på mål", data['S_mål'])
                r2_2.metric("Totala skott", data['S_tot'])
                r2_3.metric("Skott i Box", data['S_box'])
                r2_4.metric("Blockerade skott", data['S_block'])

                # Rad 3: Fler skott & Passningar
                r3_1, r3_2, r3_3, r3_4 = st.columns(4)
                r3_1.metric("Skott Utanför", data['S_ut'])
                r3_2.metric("Skott utanför Box", data['S_ut_box'])
                r3_3.metric("Passningar", data['Pass'])
                r3_4.metric("Passningssäkerhet", f"{data['Pass_%']}%")

                # Rad 4: Disciplin & Defensiv
                r4_1, r4_2, r4_3, r4_4 = st.columns(4)
                r4_1.metric("Gula kort", data['Gula'])
                r4_2.metric("Fouls", data['Fouls'])
                r4_3.metric("Offside", data['Offside'])
                r4_4.metric("Räddningar", data['Rädd'])

            # Beräkna allt
            avg_t = get_full_metrics(s_df, selected_team)
            avg_h = get_full_metrics(s_df[s_df[HOME_COL] == selected_team], selected_team)
            avg_a = get_full_metrics(s_df[stats_df[AWAY_COL] == selected_team], selected_team) if 'stats_df' not in locals() else get_full_metrics(s_df[s_df[AWAY_COL] == selected_team], selected_team)

            # Visa allt direkt på sidan
            render_full_view("📊 TOTALT", avg_t, len(s_df))
            render_full_view("🏠 HEMMA", avg_h, len(s_df[s_df[HOME_COL] == selected_team]))
            render_full_view("✈️ BORTA", avg_a, len(s_df[s_df[AWAY_COL] == selected_team]))
