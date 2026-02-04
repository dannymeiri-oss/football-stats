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
        
        # Lista på alla kolumner för tvätt
        cols_to_clean = [
            'response.goals.home', 'response.goals.away', 'xG Hemma', 'xG Borta',
            'Gula kort Hemma', 'Gula Kort Borta', 'Röda Kort Hemma', 'Röda Kort Borta',
            'Bollinnehav Hemma', 'Bollinnehav Borta', 'Skott på mål Hemma', 'Skott på mål Borta',
            'Hörnor Hemma', 'Hörnor Borta', 'Fouls Hemma', 'Fouls Borta',
            'Total Skott Hemma', 'Total Skott Borta', 'Skott Utanför Hemma', 'Skott Utanför Borta',
            'Blockerade Skott Hemma', 'Blockerade Skott Borta', 'Skott i Box Hemma', 'Skott i Box Borta',
            'Skott utanför Box Hemma', 'Skott utanför Box Borta', 
            'Passningar Hemma', 'Passningar Borta', 
            'Passningssäkerhet Hemma', 'Passningssäkerhet Borta', 
            'Offside Hemma', 'Offside Borta',
            'Räddningar Hemma', 'Räddningar Borta',
            'Straffar Hemma', 'Straffar Borta'
        ]
        
        for col in cols_to_clean:
            if col in data.columns:
                data[col] = data[col].astype(str).str.replace(',', '.')
                data[col] = data[col].str.replace(r'[^0-9.]', '', regex=True)
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            else:
                data[col] = 0
        
        return data
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return None

df = load_data()

if df is not None:
    tab1, tab2, tab3 = st.tabs(["⚽ Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys"])

    # --- FLIK 1: MATCHER (UPPDATERAD VISUELL VY) ---
    with tab1:
        st.header("Matchanalys & Historik")
        c1, c2 = st.columns([2, 1])
        with c1:
            search_query = st.text_input("Sök lag i matchlistan:", "")
        with c2:
            sort_order = st.selectbox("Sortera efter datum:", ["Senaste först", "Äldsta först"])

        m_df = df.copy()
        if search_query:
            m_df = m_df[(m_df['response.teams.home.name'].str.contains(search_query, case=False)) | 
                        (m_df['response.teams.away.name'].str.contains(search_query, case=False))]
        
        m_df = m_df.sort_values('response.fixture.date', ascending=(sort_order == "Äldsta först"))

        if not m_df.empty:
            st.subheader("Statistik för urvalet")
            s1, s2, s3, s4 = st.columns(4)
            total_m = len(m_df)
            home_wins = len(m_df[m_df['response.goals.home'] > m_df['response.goals.away']])
            away_wins = len(m_df[m_df['response.goals.away'] > m_df['response.goals.home']])
            over25 = len(m_df[(m_df['response.goals.home'] + m_df['response.goals.away']) > 2.5])
            
            s1.metric("Antal matcher", total_m)
            s2.metric("Hemmavinst %", f"{(home_wins/total_m*100):.1f}%")
            s3.metric("Bortavinst %", f"{(away_wins/total_m*100):.1f}%")
            s4.metric("Över 2.5 mål %", f"{(over25/total_m*100):.1f}%")

            st.divider()

            for _, row in m_df.head(40).iterrows():
                date = str(row['response.fixture.date']).split('T')[0]
                h_team = row['response.teams.home.name']
                a_team = row['response.teams.away.name']
                gh, ga = int(row['response.goals.home']), int(row['response.goals.away'])
                
                st.markdown(f"""
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 5px solid #2e7d32; margin-bottom: 10px; border: 1px solid #eee;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1; text-align: right; font-weight: bold; font-size: 1.1em;">{h_team}</div>
                        <div style="flex: 0.5; text-align: center; background: #333; color: white; padding: 5px 10px; border-radius: 4px; margin: 0 15px; font-size: 1.2em; min-width: 60px;">
                            {gh} - {ga}
                        </div>
                        <div style="flex: 1; text-align: left; font-weight: bold; font-size: 1.1em;">{a_team}</div>
                    </div>
                    <div style="display: flex; justify-content: center; gap: 20px; margin-top: 8px; font-size: 0.85em; color: #666;">
                        <span>📅 {date}</span>
                        <span>📊 xG: {row.get('xG Hemma',0)} - {row.get('xG Borta',0)}</span>
                        <span>🚩 Hörnor: {int(row.get('Hörnor Hemma',0))} - {int(row.get('Hörnor Borta',0))}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- FLIK 2: LAGSTATISTIK (MED FORMKURVA) ---
    with tab2:
        HOME_COL, AWAY_COL = 'response.teams.home.name', 'response.teams.away.name'
        
        f1, f2, f3 = st.columns(3)
        with f1:
            selected_team = st.selectbox("Välj lag:", sorted(pd.concat([df[HOME_COL], df[AWAY_COL]]).unique()))
        with f2:
            selected_season = st.selectbox("Säsong:", ["Alla"] + sorted(list(df['response.league.season'].unique()), reverse=True))
        with f3:
            num_matches = st.radio("Urval:", ["Samtliga", "Senaste 20"], horizontal=True)

        if selected_team:
            s_df = df[((df[HOME_COL] == selected_team) | (df[AWAY_COL] == selected_team)) & (df['response.fixture.status.short'] == 'FT')].copy()
            if selected_season != "Alla": s_df = s_df[s_df['response.league.season'] == selected_season]
            s_df = s_df.sort_values('response.fixture.date', ascending=False)
            
            # Formkurva
            form_matches = s_df.head(5)
            form_list = []
            for _, row in form_matches.iterrows():
                is_h = row[HOME_COL] == selected_team
                gf = row['response.goals.home'] if is_h else row['response.goals.away']
                ga = row['response.goals.away'] if is_h else row['response.goals.home']
                if gf > ga: form_list.append(('V', '#2e7d32'))
                elif gf < ga: form_list.append(('F', '#d32f2f'))
                else: form_list.append(('O', '#9e9e9e'))

            st.write(f"### Formkurva (Senaste {len(form_list)})")
            f_cols = st.columns(10)
            for i, (res, color) in enumerate(reversed(form_list)):
                with f_cols[i]:
                    st.markdown(f"<div style='background:{color};color:white;border-radius:50%;width:35px;height:35px;display:flex;align-items:center;justify-content:center;font-weight:bold;'>{res}</div>", unsafe_allow_html=True)
            st.divider()

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
                        'S_box': row.get(f'Skott i Box{s}', 0), 'Pass': row.get(f'Passningar{s}', 0),
                        'Pass_%': row.get(f'Passningssäkerhet{s}', 0), 'Fouls': row.get(f'Fouls{s}', 0),
                        'Gula': row.get(g_key, 0), 'Offside': row.get(f'Offside{s}', 0), 'Rädd': row.get(f'Räddningar{s}', 0),
                        'Straff': row.get(f'Straffar{s}', 0)
                    })
                return target_df.apply(map_row, axis=1).mean().round(2)

            def render_lag_block(title, data, bg_color="#ffffff"):
                if data is None: return
                st.markdown(f"### {title}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Mål", data['Mål']); c2.metric("xG", data['xG']); c3.metric("Hörnor", data['Hörnor']); c4.metric("Boll", f"{data['Boll']}%")
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 25px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 1;">
                            <p><b>Anfall</b></p>
                            <p>Skott på mål: {data['S_mål']}</p>
                            <p>Skott i box: {data['S_box']}</p>
                            <p>Straffar: {data['Straff']}</p>
                        </div>
                        <div style="flex: 1;">
                            <p><b>Spel</b></p>
                            <p>Passningar: {data['Pass']}</p>
                            <p>Säkerhet: {data['Pass_%']}%</p>
                            <p>Offside: {data['Offside']}</p>
                        </div>
                        <div style="flex: 1;">
                            <p><b>Disciplin</b></p>
                            <p>Fouls: {data['Fouls']}</p>
                            <p>Gula kort: {data['Gula']}</p>
                            <p>Räddningar: {data['Rädd']}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            avg_t = get_full_metrics(s_df, selected_team)
            avg_h = get_full_metrics(s_df[s_df[HOME_COL] == selected_team], selected_team)
            avg_a = get_full_metrics(s_df[s_df[AWAY_COL] == selected_team], selected_team)

            render_lag_block(f"Totalstatistik ({len(s_df)} matcher)", avg_t)
            cl, cr = st.columns(2)
            with cl: render_lag_block("🏠 HEMMA", avg_h, bg_color="#f0f7ff")
            with cr: render_lag_block("✈️ BORTA", avg_a, bg_color="#f0fff4")

    # --- FLIK 3: DOMARANALYS ---
    with tab3:
        REF_COL = 'response.fixture.referee'
        if REF_COL in df.columns:
            df[REF_COL] = df[REF_COL].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
            selected_ref = st.selectbox("Välj domare:", sorted(df[REF_COL].unique()))
            
            if selected_ref:
                r_df = df[df[REF_COL] == selected_ref].copy()
                avg_y = (r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean().round(2)
                avg_f = (r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean().round(2)
                avg_p = (r_df['Straffar Hemma'] + r_df['Straffar Borta']).mean().round(2)

                st.header(f"⚖️ {selected_ref}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Matcher", len(r_df))
                m2.metric("Gula / Match", avg_y)
                m3.metric("Fouls / Match", avg_f)
                m4.metric("Straffar / Match", avg_p)

                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-top: 20px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="flex: 1;">
                            <p><b>Hemmaplan (Snitt)</b></p>
                            <p>Gula: {r_df['Gula kort Hemma'].mean().round(2)}</p>
                            <p>Fouls: {r_df['Fouls Hemma'].mean().round(2)}</p>
                            <p>Straffar (Tot): {int(r_df['Straffar Hemma'].sum())}</p>
                        </div>
                        <div style="flex: 1;">
                            <p><b>Bortaplan (Snitt)</b></p>
                            <p>Gula: {r_df['Gula Kort Borta'].mean().round(2)}</p>
                            <p>Fouls: {r_df['Fouls Borta'].mean().round(2)}</p>
                            <p>Straffar (Tot): {int(r_df['Straffar Borta'].sum())}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(r_df[['response.fixture.date', 'response.teams.home.name', 'response.teams.away.name', 'response.goals.home', 'response.goals.away']], use_container_width=True)
