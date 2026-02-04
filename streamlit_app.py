import streamlit as st
import pandas as pd

# --- KONFIGURATION ---
st.set_page_config(page_title="Deep Stats 2026", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data.columns = [col.strip() for col in data.columns]
        data = data.dropna(subset=['response.fixture.id'])
        
        # Lista på ALLA kolumner som ska tvättas till siffror
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
        st.dataframe(df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.fixture.status.short']].tail(10))

    with tab2:
        HOME_COL = 'response.teams.home.name'
        AWAY_COL = 'response.teams.away.name'
        
        all_teams = sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique())
        selected_team = st.selectbox("Välj lag för djupanalys:", all_teams)

        if selected_team:
            team_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()

            if not team_df.empty:
                # Funktion för att mappa ALLA datapunkter
                def get_all_stats(row):
                    is_home = row[HOME_COL] == selected_team
                    suffix = " Hemma" if is_home else " Borta"
                    # Specialfall för vissa kolumner med udda stor bokstav (från din lista)
                    gula_suffix = " Hemma" if is_home else " Borta"
                    gula_key = f"Gula {'kort' if is_home else 'Kort'}{gula_suffix}"
                    
                    return pd.Series({
                        'Mål': row['response.goals.home'] if is_home else row['response.goals.away'],
                        'xG': row[f'xG{suffix}'],
                        'Gula': row.get(gula_key, 0),
                        'Röda': row[f'Röda Kort{suffix}'],
                        'Bollinnehav': row[f'Bollinnehav{suffix}'],
                        'Hörnor': row[f'Hörnor{suffix}'],
                        'Skott på mål': row[f'Skott på mål{suffix}'],
                        'Total Skott': row[f'Total Skott{suffix}'],
                        'Skott Utanför': row[f'Skott Utanför{suffix}'],
                        'Blockerade Skott': row[f'Blockerade Skott{suffix}'],
                        'Skott i Box': row[f'Skott i Box{suffix}'],
                        'Skott utanför Box': row[f'Skott utanför Box{suffix}'],
                        'Fouls': row[f'Fouls{suffix}'],
                        'Passningar': row[f'Passningar{suffix}'],
                        'Passningssäkerhet': row[f'Passningssäkerhet{suffix}'],
                        'Offside': row[f'Offside{suffix}'],
                        'Räddningar': row[f'Räddningar{suffix}']
                    })

                stats_df = team_df.apply(get_all_stats, axis=1)
                avg = stats_df.mean().round(2)

                # --- VISUALISERING ---
                st.subheader(f"Genomsnitt per match ({len(team_df)} matcher)")
                
                # Övergripande
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Mål", avg['Mål'])
                c2.metric("xG", avg['xG'])
                c3.metric("Bollinnehav", f"{avg['Bollinnehav']}%")
                c4.metric("Hörnor", avg['Hörnor'])

                # Kategorier i expanders
                with st.expander("🎯 Offensiv & Skott", expanded=True):
                    col_a, col_b, col_c = st.columns(3)
                    col_a.write(f"**Totala skott:** {avg['Total Skott']}")
                    col_a.write(f"**Skott på mål:** {avg['Skott på mål']}")
                    col_b.write(f"**Skott utanför:** {avg['Skott Utanför']}")
                    col_b.write(f"**Blockerade skott:** {avg['Blockerade Skott']}")
                    col_c.write(f"**Skott i box:** {avg['Skott i Box']}")
                    col_c.write(f"**Skott utanför box:** {avg['Skott utanför Box']}")

                with st.expander("🛡️ Försvar & Disciplin"):
                    col_d, col_e = st.columns(2)
                    col_d.write(f"**Gula kort:** {avg['Gula']}")
                    col_d.write(f"**Röda kort:** {avg['Röda']}")
                    col_d.write(f"**Fouls:** {avg['Fouls']}")
                    col_e.write(f"**Räddningar:** {avg['Räddningar']}")
                    col_e.write(f"**Offside:** {avg['Offside']}")

                with st.expander("🔄 Passningsspel"):
                    col_f, col_g = st.columns(2)
                    col_f.write(f"**Antal passningar:** {avg['Passningar']}")
                    col_g.write(f"**Passningssäkerhet:** {avg['Passningssäkerhet']}%")

            else:
                st.info("Ingen statistik tillgänglig för detta lag.")
