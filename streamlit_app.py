import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Stats Pro", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    if 'response.fixture.date' in df.columns:
        df['dt_object'] = pd.to_datetime(df['response.fixture.date'])
        df['Datum'] = df['dt_object'].dt.strftime('%d %b %Y %H:%M')
    
    df['-'] = '-'
    
    # Skapa en unik nyckel för varje match så vi kan identifiera den
    df['match_id'] = range(len(df))
    
    if 'response.goals.home' in df.columns:
        df['spelad'] = df['response.goals.home'].notna()
    else:
        df['spelad'] = False
    
    return df

def visa_matchrapport(match_data):
    """Skapar en detaljerad sida för den valda matchen"""
    st.button("⬅️ Tillbaka till listan", on_click=lambda: st.session_state.pop('selected_match'))
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.image(match_data['response.teams.home.logo'], width=100)
        st.header(match_data['response.teams.home.name'])
    
    with col2:
        st.title(f"{int(match_data['response.goals.home'])} - {int(match_data['response.goals.away'])}")
        st.caption(match_data['Datum'])
    
    with col3:
        st.image(match_data['response.teams.away.logo'], width=100)
        st.header(match_data['response.teams.away.name'])
    
    st.divider()
    
    # EXEMPEL PÅ DATA-PRESENTATION
    # Här kan du lägga till alla de kolumner du vill visa
    st.subheader("Matchstatistik")
    
    # Vi skapar en snygg jämförelse (Hemma vs Borta)
    # Här får vi anpassa kolumnnamnen efter vad som finns i ditt Google Sheet
    stats_cols = st.columns(3)
    with stats_cols[0]:
        st.metric("Serie", match_data['response.league.name'])
    with stats_cols[1]:
        st.metric("Land", match_data['response.league.country'])
    
    st.write("### Fler detaljer")
    # Här visar vi alla kolumner som inte är med i huvudvyn för den valda matchen
    st.json(match_data.to_dict()) # Tillfällig lösning för att se all tillgänglig data

try:
    df_raw = load_data()

    # Kontrollera om en match är vald i "session_state"
    if 'selected_match' in st.session_state:
        visa_matchrapport(st.session_state.selected_match)
    else:
        st.sidebar.title("Meny")
        sida = st.sidebar.radio("Visa:", ["Historik", "Kommande matcher"])

        if sida == "Historik":
            st.title("⚽ Resultat")
            df_view = df_raw[df_raw['spelad'] == True].copy()
            df_view = df_view.sort_values(by='dt_object', ascending=False)
        else:
            st.title("📅 Schema")
            df_view = df_raw[df_raw['spelad'] == False].copy()
            df_view = df_view.sort_values(by='dt_object', ascending=True)

        search = st.sidebar.text_input("Sök lag")
        if search:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # --- TABELL MED VALBARA RADER ---
        event = st.dataframe(
            df_view,
            column_config={
                "Datum": st.column_config.TextColumn("Datum & Tid", width="medium"),
                "response.league.logo": st.column_config.ImageColumn("", width="small"),
                "response.teams.home.logo": st.column_config.ImageColumn("", width="small"),
                "response.teams.home.name": "Hemmalag",
                "response.goals.home": "H",
                "-": "",
                "response.goals.away": "B",
                "response.teams.away.name": "Bortalag",
                "response.teams.away.logo": st.column_config.ImageColumn("", width="small"),
            },
            hide_index=True,
            on_select="rerun", # Detta gör att appen laddar om när man klickar
            selection_mode="single-row" # Man kan bara välja en match i taget
        )

        # Om användaren klickar på en rad
        if len(event.selection.rows) > 0:
            selected_row_index = event.selection.rows[0]
            st.session_state.selected_match = df_view.iloc[selected_row_index]
            st.rerun()

except Exception as e:
    st.error(f"Ett fel uppstod: {e}")
