import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 
SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "1363673756" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. LIGA-MAPPNING ---
def get_sport_key_from_league_name(league_name):
    ln = str(league_name).lower()
    mapping = {
        "premier league": "soccer_epl",
        "allsvenskan": "soccer_sweden_allsvenskan",
        "championship": "soccer_england_efl_championship",
        "la liga": "soccer_spain_la_liga",
        "serie a": "soccer_italy_serie_a",
        "bundesliga": "soccer_germany_bundesliga",
        "ligue 1": "soccer_france_ligue_1",
        "superettan": "soccer_sweden_superettan",
        "eredivisie": "soccer_netherlands_eredivisie",
        "champions league": "soccer_uefa_champions_league"
    }
    return mapping.get(ln, "soccer_epl")

# --- 3. ODDS-MOTOR (MULTIPLE ENDPOINT STRATEGY) ---
@st.cache_data(ttl=600)
def fetch_odds_robust(sport_key):
    if not ODDS_API_KEY: return None, "Ingen API-nyckel"
    
    # Vi försöker hämta alla marknader i ett svep först
    markets = "h2h,totals,btts,double_chance,draw_no_bet"
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets={markets}&bookmakers=unibet"
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json(), "OK - Alla marknader"
        else:
            # Om det skiter sig (422), hämta bara 1X2 som säkerhet
            fallback_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&bookmakers=unibet"
            res_fb = requests.get(fallback_url)
            if res_fb.status_code == 200:
                return res_fb.json(), f"FALLBACK - Endast 1X2 (Felkod {res.status_code})"
        return None, f"API Error: {res.status_code}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_match_odds_from_cache(home_sheet, away_sheet, all_odds):
    if not isinstance(all_odds, list): return None
    
    def clean(name):
        name = str(name).lower()
        # Utökad rensning för bättre matchning (ref bild 5 i din prompt)
        for r in ["fc", "afc", "town", "city", "united", "hotspur", "wanderers", "wolves", "spurs", "forest"]:
            name = name.replace(r, "")
        return "".join(filter(str.isalnum, name)).strip()
    
    h_s, a_s = clean(home_sheet), clean(away_sheet)
    for match in all_odds:
        h_api, a_api = clean(match['home_team']), clean(match['away_team'])
        if (h_s in h_api or h_api in h_s) and (a_s in a_api or a_api in a_s):
            m_found = {}
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                for mkt in match['bookmakers'][0]['markets']:
                    m_found[mkt['key']] = mkt['outcomes']
            return m_found
    return None

# --- 4. DATAHANTERING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = [col.strip() for col in data.columns]
        return data
    except: return None

def clean_stats(data):
    if data is None: return None
    if 'response.fixture.date' in data.columns:
        data['datetime'] = pd.to_datetime(data['response.fixture.date'], errors='coerce')
    cols = ['xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta', 'response.goals.home', 'response.goals.away']
    for col in cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    data['ref_clean'] = data.get('response.fixture.referee', "Okänd").fillna("Okänd").apply(lambda x: str(x).split(',')[0].strip())
    return data

df_raw = load_data(RAW_DATA_URL)
df = clean_stats(df_raw)
standings_df = load_data(STANDINGS_URL)

if 'view_match' not in st.session_state: st.session_state.view_match = None
if 'view_h2h' not in st.session_state: st.session_state.view_h2h = None

def stat_comparison_row(label, val1, val2, is_pct=False):
    c1, c2, c3 = st.columns([2, 1, 2])
    suffix = "%" if is_pct else ""
    c1.markdown(f"<div style='text-align:right; font-size:1.1em;'>{val1}{suffix}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 5. VISUALISERING ---
if df is not None:
    # --- RESULTAT-VY ---
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h1 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>", unsafe_allow_html=True)
        st.divider()
        stat_comparison_row("xG", round(r['xG Hemma'], 2), round(r['xG Borta'], 2))
        stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
        stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    # --- H2H ANALYS ---
    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        st.markdown(f"<h1 style='text-align: center;'>H2H: {h_team} vs {a_team}</h1>", unsafe_allow_html=True)
        
        h_stats = df[(df['response.teams.home.name'] == h_team) & (df['response.fixture.status.short'] == 'FT')]
        a_stats = df[(df['response.teams.away.name'] == a_team) & (df['response.fixture.status.short'] == 'FT')]
        
        if not h_stats.empty and not a_stats.empty:
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("Mål snitt", round(h_stats['response.goals.home'].mean() + a_stats['response.goals.away'].mean(), 2))
            tc2.metric("xG snitt", round(h_stats['xG Hemma'].mean() + a_stats['xG Borta'].mean(), 2))
            tc3.metric("Hörnor", round(h_stats['Hörnor Hemma'].mean() + a_stats['Hörnor Borta'].mean(), 1))
            tc4.metric("Gula", round(h_stats['Gula kort Hemma'].mean() + a_stats['Gula Kort Borta'].mean(), 1))
            
            st.divider()
            
            st.markdown("<h4 style='text-align: center;'>💸 Marknadsodds (Unibet)</h4>", unsafe_allow_html=True)
            sk = get_sport_key_from_league_name(m.get('response.league.name', ''))
            api_res, status_msg = fetch_odds_robust(sk)
            odds = get_match_odds_from_cache(h_team, a_team, api_res)
            
            if odds:
                o1, o2, o3 = st.columns(3)
                with o1:
                    if 'h2h' in odds:
                        st.write("**1X2 Odds**")
                        for o in odds['h2h']: st.write(f"{o['name']}: **{o['price']}**")
                    if 'double_chance' in odds:
                        st.write("**Dubbelchans**")
                        for o in odds['double_chance']: st.write(f"{o['name']}: **{o['price']}**")
                with o2:
                    if 'btts' in odds:
                        st.write("**Båda lagen gör mål**")
                        for o in odds['btts']: st.write(f"{o['name']}: **{o['price']}**")
                    if 'draw_no_bet' in odds:
                        st.write("**Draw No Bet**")
                        for o in odds['draw_no_bet']: st.write(f"{o['name']}: **{o['price']}**")
                with o3:
                    if 'totals' in odds:
                        st.write("**Över/Under 2.5**")
                        for o in odds['totals']:
                            if o.get('point') == 2.5: st.write(f"{o['name']}: **{o['price']}**")
            else:
                st.info("Inga odds matchades för denna match just nu.")

            st.divider()
            st.markdown("<h4 style='text-align: center;'>📊 Detaljerad Lagjämförelse</h4>", unsafe_allow_html=True)
            stat_comparison_row("Mål", round(h_stats['response.goals.home'].mean(), 2), round(a_stats['response.goals.away'].mean(), 2))
            stat_comparison_row("xG", round(h_stats['xG Hemma'].mean(), 2), round(a_stats['xG Borta'].mean(), 2))
            stat_comparison_row("Hörnor", round(h_stats['Hörnor Hemma'].mean(), 1), round(a_stats['Hörnor Borta'].mean(), 1))
            stat_comparison_row("Gula Kort", round(h_stats['Gula kort Hemma'].mean(), 1), round(a_stats['Gula Kort Borta'].mean(), 1))

            with st.expander("🛠️ Debut Console: API-status"):
                st.write(f"Liga: {sk} | Status: {status_msg}")
                st.write(f"Matchning sökt: {h_team} vs {a_team}")
                st.write(f"Antal matcher i API: {len(api_res) if isinstance(api_res, list) else 0}")

    # --- HUVUDMENY ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matchcenter", "🏆 Tabell", "🛡️ Laganalys", "⚖️ Domare"])
        
        with tab1:
            mode = st.radio("Visa:", ["Nästa matcher", "Resultat"], horizontal=True)
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa matcher" else 'FT')]
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa matcher")).head(40).iterrows():
                h_name, a_name = r['response.teams.home.name'], r['response.teams.away.name']
                h_logo, a_logo = r.get('response.teams.home.logo', ''), r.get('response.teams.away.logo', '')
                
                show_alert = False
                if mode == "Nästa matcher":
                    h_c = df[df['response.teams.home.name'] == h_name]['Gula kort Hemma'].mean()
                    a_c = df[df['response.teams.away.name'] == a_name]['Gula Kort Borta'].mean()
                    if (pd.Series(h_c).fillna(0).iloc[0] + pd.Series(a_c).fillna(0).iloc[0]) >= 3.4: show_alert = True

                c_i, c_b = st.columns([5, 1.5])
                score_text = f"{int(r['response.goals.home'])} - {int(r['response.goals.away'])}" if mode=="Resultat" else "VS"
                
                with c_i:
                    st.markdown(f'''
                        <div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;">
                            <div style="width:70px; font-size:0.8em; color:gray;">{r["datetime"].strftime("%d %b")}</div>
                            <div style="flex:1; text-align:right; font-weight:bold;">{h_name} <img src="{h_logo}" width="22"></div>
                            <div style="background:#222; color:white; padding:2px 12px; margin:0 15px; border-radius:4px; font-weight:bold; min-width:65px; text-align:center;">{score_text}</div>
                            <div style="flex:1; text-align:left; font-weight:bold;"><img src="{a_logo}" width="22"> {a_name}</div>
                            <div style="margin-left:10px; font-size:0.7em; color:blue; width:100px;">{r.get("response.league.name", "")}</div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c_b:
                    btn_col, bell_col = st.columns([1, 0.3])
                    with btn_col:
                        if st.button("Analys" if mode=="Nästa matcher" else "Statistik", key=f"btn{idx}", use_container_width=True):
                            if mode=="Nästa matcher": st.session_state.view_h2h = r
                            else: st.session_state.view_match = r
                            st.rerun()
                    with bell_col:
                        if show_alert: st.markdown("<div style='font-size:1.6em; margin-top:2px;'>🔔</div>", unsafe_allow_html=True)

        with tab2:
            st.header("🏆 Ligatabell")
            if standings_df is not None: st.dataframe(standings_df, use_container_width=True)
            else: st.info("Laddar tabell...")

        with tab3:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                st.dataframe(df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)].head(10))

        with tab4:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                st.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))
else:
    st.error("Kunde inte ladda data.")
