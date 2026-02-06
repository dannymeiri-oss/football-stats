import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIG & SETUP ---
st.set_page_config(page_title="Perfect Layout - Football Analysis", layout="wide")

# Ditt specifika Sheet ID från länken
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
RAW_DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Raw+Data"
STANDINGS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Standings"

@st.cache_data(ttl=600)
def load_data():
    try:
        # Hämta Raw Data
        df = pd.read_csv(RAW_DATA_URL)
        # Hämta Standings (om den finns, annars None)
        try:
            st_df = pd.read_csv(STANDINGS_URL)
        except:
            st_df = None
        return df, st_df
    except Exception as e:
        st.error(f"Fel vid inläsning av Google Sheets: {e}")
        return None, None

def format_referee(name):
    if pd.isna(name) or str(name).strip().lower() in ["nan", "unknown", "okänd", ""]:
        return "Domare: Okänd"
    parts = str(name).split(',')
    main_name = parts[0].strip()
    name_parts = main_name.split()
    if len(name_parts) > 1:
        return f"{name_parts[0][0]}. {' '.join(name_parts[1:])}"
    return main_name

def clean_stats(data):
    if data is None: return None
    
    # --- SÄKERHETSSPÄRR MOT DUBLETTER ---
    # Tar bort rader med samma Match-ID (Fixture ID)
    if 'response.fixture.id' in data.columns:
        data = data.drop_duplicates(subset=['response.fixture.id'], keep='first')
    
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    
    # Formatera domarnamn direkt i datan
    if 'response.fixture.referee' in data.columns:
        data['referee_clean'] = data['response.fixture.referee'].apply(format_referee)
    else:
        data['referee_clean'] = "Domare: Okänd"
        
    return data

# --- LOAD DATA ---
raw_df, standings_df = load_data()
df = clean_stats(raw_df)

if df is not None:
    # Sidomeny - Filter
    st.sidebar.header("Filter")
    ligor = sorted(df['response.league.name'].dropna().unique())
    vald_liga = st.sidebar.selectbox("Välj Liga", ["Alla"] + ligor)
    
    filtered_df = df if vald_liga == "Alla" else df[df['response.league.name'] == vald_liga]
    
    # Huvudvy - Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "📊 Team Analysis", "⚖️ Referee Analysis", "🏆 Tabell"])

    # --- TAB 1: MATCHER & H2H ---
    with tab1:
        st.subheader("Kommande & Spelade Matcher")
        
        # Sortera efter datum (senaste först)
        display_df = filtered_df.sort_values('datetime', ascending=False)
        
        for idx, row in display_df.head(20).iterrows():
            h_team = row['response.teams.home.name']
            a_team = row['response.teams.away.name']
            date_str = row['datetime'].strftime('%Y-%m-%d %H:%M') if not pd.isna(row['datetime']) else "Datum saknas"
            
            with st.expander(f"{date_str}: {h_team} vs {a_team}"):
                # --- H2H SEKTION ---
                st.markdown("### Head-to-Head (H2H)")
                
                # 1. Domarrad (Ligger överst i H2H enligt önskemål)
                ref_name = row['referee_clean']
                ref_stats = "N/A"
                if ref_name != "Domare: Okänd":
                    # Räkna snitt på de 10 senaste matcherna för denna domare
                    ref_matches = df[df['referee_clean'] == ref_name].sort_values('datetime', ascending=False).head(10)
                    if not ref_matches.empty:
                        avg_cards = (ref_matches['response.statistics.0.Yellow Cards'].fillna(0) + 
                                     ref_matches['response.statistics.1.Yellow Cards'].fillna(0)).mean()
                        ref_stats = f"{avg_cards:.2f} gula (snitt 10 matcher)"
                
                st.info(f"👤 **Domare:** {ref_name} | **Statistik:** {ref_stats}")
                
                # 2. Season Averages Comparison
                st.markdown("#### SEASON AVERAGES COMPARISON")
                col1, col2, col3 = st.columns([2,1,2])
                
                # Beräkna snitt för hemma- och bortalag
                h_avg = df[df['response.teams.home.name'] == h_team].iloc[:, 48:70].mean(numeric_only=True)
                a_avg = df[df['response.teams.away.name'] == a_team].iloc[:, 48:70].mean(numeric_only=True)
                
                with col1:
                    st.write(f"**{h_team}**")
                    if not h_avg.empty:
                        st.write(f"Gula: {h_avg.get('response.statistics.0.Yellow Cards', 0):.2f}")
                        st.write(f"Fouls: {h_avg.get('response.statistics.0.Fouls', 0):.2f}")
                with col3:
                    st.write(f"**{a_team}**")
                    if not a_avg.empty:
                        st.write(f"Gula: {a_avg.get('response.statistics.1.Yellow Cards', 0):.2f}")
                        st.write(f"Fouls: {a_avg.get('response.statistics.1.Fouls', 0):.2f}")

    # --- TAB 2: TEAM ANALYSIS ---
    with tab2:
        st.header("Lagstatistik")
        valda_lag = st.multiselect("Välj lag för jämförelse", sorted(df['response.teams.home.name'].unique()))
        if valda_lag:
            compare_df = df[df['response.teams.home.name'].isin(valda_lag) | df['response.teams.away.name'].isin(valda_lag)]
            st.dataframe(compare_df.head(10))

    # --- TAB 3: REFEREE ANALYSIS ---
    with tab3:
        st.header("Domaranalys")
        ref_list = sorted([r for r in df['referee_clean'].unique() if r != "Domare: Okänd"])
        selected_ref = st.selectbox("Välj domare", ref_list)
        
        if selected_ref:
            ref_data = df[df['referee_clean'] == selected_ref].sort_values('datetime', ascending=False)
            st.metric("Antal matcher i databasen", len(ref_data))
            st.dataframe(ref_data[['datetime', 'response.teams.home.name', 'response.teams.away.name', 'response.statistics.0.Yellow Cards', 'response.statistics.1.Yellow Cards']])

    # --- TAB 4: DYNAMISK TABELL ---
    with tab4:
        st.header("🏆 Ligatabeller")
        if standings_df is not None:
            # Hämta unika ligor från Standings-fliken
            if 'League' in standings_df.columns:
                available_leagues = sorted(standings_df['League'].unique())
                
                selected_league_tab = st.selectbox("Välj liga att visa:", available_leagues)
                
                # Filtrera fram rätt liga
                league_table = standings_df[standings_df['League'] == selected_league_tab].copy()
                
                # Visa tidsstämpel om den finns
                if 'Updated' in league_table.columns:
                    st.caption(f"Senast synkad: {league_table['Updated'].iloc[0]}")
                
                # Rendera tabellen
                st.dataframe(
                    league_table.drop(columns=['League', 'Updated'], errors='ignore'),
                    column_config={
                        "Logo": st.column_config.ImageColumn("", width="small"),
                        "Rank": st.column_config.NumberColumn("Pos", format="%d"),
                        "Points": st.column_config.NumberColumn("P"),
                        "GF": "GM",
                        "GA": "IM",
                        "GD": "+/-"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Kör ditt nya script i Google Sheets för att skapa tabell-datan.")
        else:
            st.warning("Hittade ingen flik vid namn 'Standings'. Se till att scriptet 'uppdateraDynamiskaTabeller' har körts.")

else:
    st.error(f"Kunde inte ladda data. Kontrollera att SHEET_ID är korrekt och att 'Raw Data' är tillgänglig.")
