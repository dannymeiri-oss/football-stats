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
            'Räddningar Hemma', 'Räddningar Borta', 'response.league.season'
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

    with tab2:
        st.header("Laganalys & Medelvärden")
        
        HOME_COL = 'response.teams.home.name'
        AWAY_COL = 'response.teams.away.name'
        SEASON_COL = 'response.league.season'
        
        # Filter-rad
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_teams = sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique())
            selected_team = st.selectbox("Välj lag:", all_teams)
        with f_col2:
            seasons = sorted(df[SEASON_COL].unique(), reverse=True)
            selected_season = st.selectbox("Välj säsong:", ["Alla"] + list(seasons))
        with f_col3:
            num_matches = st.radio("Visa data för:", ["Samtliga matcher", "Senaste 20 matcher"], horizontal=True)

        if selected_team:
            # Grundfilter
            base_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()
            if selected_season != "Alla":
                base_df = base_df[base_df[SEASON_COL] == selected_season]
            base_df = base_df.sort_values('response.fixture.date', ascending=False)
            if num_matches == "Senaste 20 matcher":
                base_df = base_df.head(20)

            if not base_df.empty:
                # Hjälpfunktion för att räkna ut snitt
                def get_averages(target_df, team_name):
                    def map_row(row):
                        is_home = row[HOME_COL] == team_name
                        s = " Hemma" if is_home else " Borta"
                        g_key = "Gula kort Hemma" if is_home else "Gula Kort Borta"
                        return pd.Series({
                            'Mål': row['response.goals.home'] if is_home else row['response.goals.away'],
                            'xG': row.get(f'xG{s}', 0),
                            'Hörnor': row.get(f'Hörnor{s}', 0),
                            'Skott på mål': row.get(f'Skott på mål{s}', 0),
                            'Gula': row.get(g_key, 0)
                        })
                    return target_df.apply(map_row, axis=1).mean().round(2)

                # 1. TOTAL-KORT (Överst)
                avg_total = get_averages(base_df, selected_team)
                st.subheader(f"Totalstatistik ({len(base_df)} matcher)")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Snitt Mål", avg_total['Mål'])
                c2.metric("Snitt xG", avg_total['xG'])
                c3.metric("Snitt Hörnor", avg_total['Hörnor'])
                c4.metric("Snitt Gula", avg_total['Gula'])

                st.divider()

                # 2. HEMMA OCH BORTA KORT (Sida vid sida)
                col_home_card, col_away_card = st.columns(2)

                with col_home_card:
                    st.markdown("### 🏠 Hemma")
                    h_df = base_df[base_df[HOME_COL] == selected_team]
                    if not h_df.empty:
                        avg_h = get_averages(h_df, selected_team)
                        st.write(f"Baserat på {len(h_df)} hemmamatcher")
                        st.metric("Mål Hemma", avg_h['Mål'])
                        st.metric("xG Hemma", avg_h['xG'])
                        st.metric("Hörnor Hemma", avg_h['Hörnor'])
                    else:
                        st.info("Inga hemmamatcher i urvalet.")

                with col_away_card:
                    st.markdown("### ✈️ Borta")
                    a_df = base_df[base_df[AWAY_COL] == selected_team]
                    if not a_df.empty:
                        avg_a = get_averages(a_df, selected_team)
                        st.write(f"Baserat på {len(a_df)} bortamatcher")
                        st.metric("Mål Borta", avg_a['Mål'])
                        st.metric("xG Borta", avg_a['xG'])
                        st.metric("Hörnor Borta", avg_a['Hörnor'])
                    else:
                        st.info("Inga bortamatcher i urvalet.")
            else:
                st.info("Hittade ingen data för valda filter.")
