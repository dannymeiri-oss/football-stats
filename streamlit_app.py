import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except:
        return None

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    
    # ALLA 32+ PUNKTER SÄKERSTÄLLS
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Röda Kort Hemma', 'Röda Kort Borta',
        'Skott på mål Hemma', 'Skott på mål Borta', 'Hörnor Hemma', 'Hörnor Borta',
        'Fouls Hemma', 'Fouls Borta', 'Total Skott Hemma', 'Total Skott Borta',
        'Skott Utanför Hemma', 'Skott Utanför Borta', 'Blockerade Skott Hemma', 'Blockerade Skott Borta',
        'Skott i Box Hemma', 'Skott i Box Borta', 'Skott utanför Box Hemma', 'Skott utanför Box Borta',
        'Passningar Hemma', 'Passningar Borta', 'Passningssäkerhet Hemma', 'Passningssäkerhet Borta',
        'Offside Hemma', 'Offside Borta', 'Räddningar Hemma', 'Räddningar Borta',
        'response.goals.home', 'response.goals.away', 'response.fixture.status.short',
        'response.teams.home.logo', 'response.teams.away.logo', 'response.fixture.referee'
    ]
    
    for col in cols_to_ensure:
        if col not in data.columns:
            data[col] = "" if "logo" in col else 0
        elif col not in ['response.fixture.referee', 'response.fixture.status.short', 'response.teams.home.logo', 'response.teams.away.logo', 'response.teams.home.name', 'response.teams.away.name']:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            
    data['ref_clean'] = data['response.fixture.referee'].fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if 'view_match' not in st.session_state:
    st.session_state.view_match = None

# --- DETALJVY ANALYS ---
def render_match_analysis(row):
    if st.button("← Tillbaka till listan"):
        st.session_state.view_match = None
        st.rerun()
    st.title(f"{row['response.teams.home.name']} {int(row['response.goals.home'])} - {int(row['response.goals.away'])} {row['response.teams.away.name']}")
    c1, c2, c3 = st.columns([1, 0.5, 1])
    with c1:
        if row['response.teams.home.logo']: st.image(row['response.teams.home.logo'], width=80)
        st.metric("xG", row['xG Hemma']); st.metric("Innehav", f"{int(row['Bollinnehav Hemma'])}%")
    with c3:
        if row['response.teams.away.logo']: st.image(row['response.teams.away.logo'], width=80)
        st.metric("xG", row['xG Borta']); st.metric("Innehav", f"{int(row['Bollinnehav Borta'])}%")
    st.divider()
    for label, h, a in [("Skott på mål", 'Skott på mål Hemma', 'Skott på mål Borta'), ("Hörnor", 'Hörnor Hemma', 'Hörnor Borta'), ("Gula Kort", 'Gula kort Hemma', 'Gula Kort Borta')]:
        st.write(f"**{label}**: {int(row[h])} — {int(row[a])}")
        st.progress(row[h]/(row[h]+row[a]) if (row[h]+row[a])>0 else 0.5)

# --- HUVUDLAYOUT ---
if df is not None:
    if st.session_state.view_match is not None:
        render_match_analysis(st.session_state.view_match)
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])

        with tab1:
            st.header("Matchcenter")
            m_col, s_col = st.columns(2)
            mode = m_col.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            search = s_col.text_input("Sök lag:", "")
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            if search: d_df = d_df[(d_df['response.teams.home.name'].str.contains(search, case=False)) | (d_df['response.teams.away.name'].str.contains(search, case=False))]
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1])
                score = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Senaste resultaten" else "VS"
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]} <img src="{r["response.teams.home.logo"]}" width="18"></div><div style="background:#222; color:white; padding:2px 8px; margin:0 10px; border-radius:4px; min-width:50px; text-align:center;">{score}</div><div style="flex:1; text-align:left; font-weight:bold;"><img src="{r["response.teams.away.logo"]}" width="18"> {r["response.teams.away.name"]}</div></div>', unsafe_allow_html=True)
                with c_b:
                    if mode=="Senaste resultaten" and st.button("Analys", key=f"b{idx}"):
                        st.session_state.view_match = r
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                h_df = df[(df['response.teams.home.name'] == sel_team) & (df['response.fixture.status.short'] == 'FT')]
                a_df = df[(df['response.teams.away.name'] == sel_team) & (df['response.fixture.status.short'] == 'FT')]
                
                # --- ALL STATISTIK UTAN EXPANDERS ---
                col_h, col_a = st.columns(2)
                with col_h:
                    st.subheader("🏠 HEMMA")
                    if not h_df.empty:
                        st.metric("Matcher", len(h_df))
                        st.metric("Mål / xG", f"{round(h_df['response.goals.home'].mean(),2)} / {round(h_df['xG Hemma'].mean(),2)}")
                        st.metric("Bollinnehav", f"{int(h_df['Bollinnehav Hemma'].mean())}%")
                        st.metric("Skott på mål / Totalt", f"{round(h_df['Skott på mål Hemma'].mean(),1)} / {round(h_df['Total Skott Hemma'].mean(),1)}")
                        st.metric("Skott Utanför / Block", f"{round(h_df['Skott Utanför Hemma'].mean(),1)} / {round(h_df['Blockerade Skott Hemma'].mean(),1)}")
                        st.metric("Skott i Box / Utanför Box", f"{round(h_df['Skott i Box Hemma'].mean(),1)} / {round(h_df['Skott utanför Box Hemma'].mean(),1)}")
                        st.metric("Hörnor", round(h_df['Hörnor Hemma'].mean(), 2))
                        st.metric("Fouls / Offside", f"{round(h_df['Fouls Hemma'].mean(),1)} / {round(h_df['Offside Hemma'].mean(),1)}")
                        st.metric("Gula / Röda Kort", f"{round(h_df['Gula kort Hemma'].mean(),1)} / {round(h_df['Röda Kort Hemma'].mean(),2)}")
                        st.metric("Passningar / Säkerhet", f"{int(h_df['Passningar Hemma'].mean())} / {int(h_df['Passningssäkerhet Hemma'].mean())}%")
                        st.metric("Räddningar", round(h_df['Räddningar Hemma'].mean(), 1))
                    else: st.write("Ingen hemma-data")

                with col_a:
                    st.subheader("✈️ BORTA")
                    if not a_df.empty:
                        st.metric("Matcher", len(a_df))
                        st.metric("Mål / xG", f"{round(a_df['response.goals.away'].mean(),2)} / {round(a_df['xG Borta'].mean(),2)}")
                        st.metric("Bollinnehav", f"{int(a_df['Bollinnehav Borta'].mean())}%")
                        st.metric("Skott på mål / Totalt", f"{round(a_df['Skott på mål Borta'].mean(),1)} / {round(a_df['Total Skott Borta'].mean(),1)}")
                        st.metric("Skott Utanför / Block", f"{round(a_df['Skott Utanför Borta'].mean(),1)} / {round(a_df['Blockerade Skott Borta'].mean(),1)}")
                        st.metric("Skott i Box / Utanför Box", f"{round(a_df['Skott i Box Borta'].mean(),1)} / {round(a_df['Skott utanför Box Borta'].mean(),1)}")
                        st.metric("Hörnor", round(a_df['Hörnor Borta'].mean(), 2))
                        st.metric("Fouls / Offside", f"{round(a_df['Fouls Borta'].mean(),1)} / {round(a_df['Offside Borta'].mean(),1)}")
                        st.metric("Gula / Röda Kort", f"{round(a_df['Gula Kort Borta'].mean(),1)} / {round(a_df['Röda Kort Borta'].mean(),2)}")
                        st.metric("Passningar / Säkerhet", f"{int(a_df['Passningar Borta'].mean())} / {int(a_df['Passningssäkerhet Borta'].mean())}%")
                        st.metric("Räddningar", round(a_df['Räddningar Borta'].mean(), 1))
                    else: st.write("Ingen borta-data")

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Matcher", len(r_df)); c2.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
                c3.metric("Fouls/Match", round((r_df['Fouls Hemma'] + r_df['Fouls Borta']).mean(), 2)); c4.metric("Straffar", int(r_df['Straffar Hemma'].sum() + r_df['Straffar Borta'].sum()))

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None: st.dataframe(standings_df, hide_index=True, use_container_width=True)

else:
    st.error("Kunde inte ladda data.")
