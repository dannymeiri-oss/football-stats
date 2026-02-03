import streamlit as st
import pandas as pd
from datetime import datetime
import traceback

# 1. Grundinställningar
st.set_page_config(page_title="Football Stats Pro", layout="wide")

# 2. CSS för det visuella
st.markdown("""
    <style>
    .score-big { font-size: 35px; font-weight: 900; color: #ff4b4b; text-align: center; }
    .vs-text { text-align: center; color: #888; font-size: 14px; }
    .league-header { color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    .date-text { color: #aaa; font-size: 14px; font-weight: bold; }
    .meta-small { color: #666; font-size: 12px; }
    .card { background: #fff; padding: 12px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
    "", unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYB9eRz1kLOPX8YewpfSh5KuZQQ8AoKsfkxSmNutW5adKPMFN1AvLGq3FSVw7ZXwqMYZJVkFIPIO-g/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
    except Exception as e:
        # Returnera tom df — fel visas i appen
        return pd.DataFrame({"__load_error__": [str(e)]})

    # Rensa kolumnnamn
    df.columns = df.columns.str.strip()

    # Datum: skapa dt_object om möjligt
    if 'response.fixture.date' in df.columns:
        dt = pd.to_datetime(df['response.fixture.date'], errors='coerce')
        # Försök ta bort timezone om någon finns
        try:
            dt = dt.dt.tz_localize(None)
        except Exception:
            try:
                dt = dt.dt.tz_convert(None)
            except Exception:
                # Om det fortfarande failar, behåll som är (coerce -> NaT okej)
                pass
        df['dt_object'] = dt
        df['Datum'] = dt.dt.strftime('%d %b %Y %H:%M')
    else:
        df['dt_object'] = pd.NaT
        df['Datum'] = ""

    # Bestäm om matchen är spelad
    now = datetime.now()
    goal_col = 'response.goals.home'
    if goal_col in df.columns:
        goals_numeric = pd.to_numeric(df[goal_col], errors='coerce')
        # Om vi har dt_object, använd både mål och datum; annars basera på mål
        if 'dt_object' in df.columns and not df['dt_object'].isna().all():
            df['spelad'] = (~goals_numeric.isna()) | (df['dt_object'] < now)
        else:
            df['spelad'] = ~goals_numeric.isna()
    else:
        # Om inga mål-kolumner finns, default till att kolla datum (om finns)
        if 'dt_object' in df.columns:
            df['spelad'] = df['dt_object'] < now
        else:
            df['spelad'] = False

    return df

def go_back():
    st.session_state.page = 'list'
    st.session_state.selected_match = None

try:
    df_raw = load_data()

    # Hantera laddningsfel
    if '__load_error__' in df_raw.columns:
        st.title("🏆 Matchcenter")
        st.error(f"Fel vid inläsning av data: {df_raw['__load_error__'].iat[0]}")
        st.stop()

    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_match' not in st.session_state:
        st.session_state.selected_match = None

    # --- SIDA 1: LISTVY ---
    if st.session_state.page == 'list':
        st.title("🏆 Matchcenter")
        # Sidopanel-inställningar
        st.sidebar.header("Filter")
        sida = st.sidebar.radio("Visa matcher:", ["Kommande", "Historik"])
        search = st.sidebar.text_input("Sök lag...")
        league_filter = st.sidebar.text_input("Filtrera liga (valfritt)")

        df_view = df_raw[df_raw['spelad'] == (sida == "Historik")].copy()

        if league_filter:
            df_view = df_view[df_view.astype(str).apply(lambda col: col.str.contains(league_filter, case=False, na=False)).any(axis=1)]

        if search:
            # Sök i alla kolumner (str) — robust mot NaN
            mask = df_view.apply(lambda row: row.astype(str).str.contains(search, case=False, na=False).any(), axis=1)
            df_view = df_view[mask]

        if df_view.empty:
            st.info("Inga matcher att visa.")
        else:
            df_view = df_view.sort_values(by='dt_object', ascending=(sida == "Kommande"))
            for i, match in df_view.iterrows():
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    col1, col2, col3, col4, col5 = st.columns([0.8, 3, 2, 3, 1.5])
                    # League logo
                    with col1:
                        logo = match.get('response.league.logo') if 'response.league.logo' in match.index else None
                        if pd.notna(logo) and str(logo).strip() != "":
                            st.image(logo, width=40)
                        else:
                            st.write("")  # placeholder
                    # Home team
                    with col2:
                        home_name = match.get('response.teams.home.name', '') if 'response.teams.home.name' in match.index else ''
                        away_name = match.get('response.teams.away.name', '') if 'response.teams.away.name' in match.index else ''
                        st.write(f"**{home_name}**")
                        st.markdown(f"<div class='league-header'>{match.get('response.league.name','')}</div>", unsafe_allow_html=True)
                    # Score or time
                    with col3:
                        h_goals = match.get('response.goals.home') if 'response.goals.home' in match.index else None
                        a_goals = match.get('response.goals.away') if 'response.goals.away' in match.index else None
                        if pd.notna(h_goals) and pd.notna(a_goals) and str(h_goals).strip() != "":
                            try:
                                h = int(float(h_goals))
                                a = int(float(a_goals))
                                st.markdown(f"<div class='score-big'>{h} - {a}</div>", unsafe_allow_html=True)
                            except Exception:
                                st.markdown(f"<div class='score-big'>{h_goals} - {a_goals}</div>", unsafe_allow_html=True)
                        else:
                            tid = "--:--"
                            if 'Datum' in match.index and pd.notna(match['Datum']) and match['Datum'] != "":
                                # Försök plocka ut tiddelen
                                parts = str(match['Datum']).split(' ')
                                if len(parts) >= 4:
                                    tid = parts[3]
                                else:
                                    tid = str(match['Datum'])
                            st.markdown(f"<div class='vs-text'>VS<br>{tid}</div>", unsafe_allow_html=True)
                    # Away team
                    with col4:
                        st.write(f"**{away_name}**")
                    # Button / meta
                    with col5:
                        match_date = match.get('Datum', '')
                        st.markdown(f"<div class='date-text'>{match_date}</div>", unsafe_allow_html=True)
                        btn_key = f"view_{i}"
                        if st.button("Visa", key=btn_key):
                            # Spara hela match-raden som dict i session_state
                            st.session_state.selected_match = match.to_dict()
                            st.session_state.page = 'detail'
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- SIDA 2: DETALJVY ---
    elif st.session_state.page == 'detail':
        m = st.session_state.selected_match
        if not m:
            st.warning("Ingen match vald.")
            st.session_state.page = 'list'
        else:
            st.button("← Tillbaka", on_click=go_back)
            # Rubrik
            home = m.get('response.teams.home.name', '')
            away = m.get('response.teams.away.name', '')
            st.header(f"{home} vs {away}")
            # Score / tid
            h_goals = m.get('response.goals.home')
            a_goals = m.get('response.goals.away')
            if pd.notna(h_goals) and pd.notna(a_goals) and str(h_goals).strip() != "":
                try:
                    st.subheader(f"{int(float(h_goals))} - {int(float(a_goals))}")
                except Exception:
                    st.subheader(f"{h_goals} - {a_goals}")
            else:
                st.subheader(m.get('Datum', 'Tid saknas'))
            # Visa några metadata och hela raden som json/tabell för debugging
            st.markdown(f"**League:** {m.get('response.league.name','')}")
            st.markdown(f"**Date:** {m.get('Datum','')}")
            # Visa match-data
            try:
                df_match = pd.DataFrame({k: [v] for k, v in m.items()})
                st.dataframe(df_match.T.rename(columns={0: "Value"}))
            except Exception:
                st.write(m)

except Exception as e:
    st.title("🏆 Matchcenter")
    st.error("Ett oväntat fel uppstod. Se nedan för traceback.")
    st.text(traceback.format_exc())