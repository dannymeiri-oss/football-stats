import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. KONFIGURATION & LÄNKAR ---
st.set_page_config(page_title="Deep Stats Pro 2026", layout="wide")

ODDS_API_KEY = "9e039bbc42554ea47425877bbba7df22" 

SHEET_ID = "1eHU1H7pqNp_kOoMqbhrL6Cxc2bV7A0OV-EOxTItaKlw"
GID_RAW = "0"
GID_STANDINGS = "DITT_GID_HÄR" 

BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
RAW_DATA_URL = f"{BASE_URL}&gid={GID_RAW}"
STANDINGS_URL = f"{BASE_URL}&gid={GID_STANDINGS}"

# --- 2. LIGA-MAPPNING ---
def get_sport_key_from_league_name(league_name):
    ln = str(league_name).lower()
    mapping = {
        "allsvenskan": "soccer_sweden_allsvenskan",
        "premier league": "soccer_epl",
        "championship": "soccer_england_efl_championship",
        "la liga": "soccer_spain_la_liga",
        "serie a": "soccer_italy_serie_a",
        "bundesliga": "soccer_germany_bundesliga",
        "ligue 1": "soccer_france_ligue_1",
        "champions league": "soccer_uefa_champions_league",
        "europa league": "soccer_uefa_europa_league",
        "superettan": "soccer_sweden_superettan",
        "eredivisie": "soccer_netherlands_eredivisie"
    }
    return mapping.get(ln, "soccer_epl")

# --- 3. SMARTA ODDS-FUNKTIONER (MED DEBUG-INFO) ---
@st.cache_data(ttl=600)
def fetch_odds_by_league(sport_key):
    if not ODDS_API_KEY: return None, "Ingen API-nyckel"
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&bookmakers=unibet"
    try:
        res = requests.get(url)
        if res.status_code == 429: return "QUOTA_EXCEEDED", url
        return (res.json() if res.status_code == 200 else None), url
    except Exception as e:
        return None, str(e)

def get_match_odds_from_cache(home_sheet, away_sheet, all_odds):
    if not all_odds or all_odds == "QUOTA_EXCEEDED": return None, None
    
    def clean(name):
        name = str(name).lower()
        if "manchester united" in name or "man utd" in name: return "manutd"
        if "manchester city" in name or "man city" in name: return "mancity"
        if "tottenham" in name: return "tottenham"
        return "".join(filter(str.isalnum, name))

    h_s, a_s = clean(home_sheet), clean(away_sheet)
    
    for match in all_odds:
        h_api, a_api = clean(match['home_team']), clean(match['away_team'])
        if h_s == h_api and a_s == a_api:
            h2h, totals = None, None
            if 'bookmakers' in match and len(match['bookmakers']) > 0:
                for mkt in match['bookmakers'][0]['markets']:
                    if mkt['key'] == 'h2h': h2h = mkt['outcomes']
                    if mkt['key'] == 'totals': totals = mkt['outcomes']
            return h2h, totals
    return None, None

# --- 4. DATA-LADDNING & TVÄTT ---
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
        data['Säsong'] = data['datetime'].dt.year.fillna(0).astype(int)
    
    cols_to_ensure = [
        'xG Hemma', 'xG Borta', 'Bollinnehav Hemma', 'Bollinnehav Borta', 
        'Gula kort Hemma', 'Gula Kort Borta', 'Hörnor Hemma', 'Hörnor Borta',
        'response.goals.home', 'response.goals.away', 'response.fixture.status.short',
        'response.teams.home.name', 'response.teams.away.name', 'response.league.name'
    ]
    for col in cols_to_ensure:
        if col not in data.columns: data[col] = 0
        elif col not in ['response.fixture.status.short', 'response.teams.home.name', 'response.teams.away.name', 'response.league.name']:
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
    c2.markdown(f"<div style='text-align:center; color:#888; font-weight:bold; font-size:0.9em;'>{label}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:left; font-size:1.1em;'>{val2}{suffix}</div>", unsafe_allow_html=True)

# --- 5. HUVUDLAYOUT ---
if df is not None:
    if st.session_state.view_match is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_match = None
            st.rerun()
        r = st.session_state.view_match
        st.markdown(f"<h1 style='text-align: center;'>{r['response.teams.home.name']} {int(r['response.goals.home'])} - {int(r['response.goals.away'])} {r['response.teams.away.name']}</h1>", unsafe_allow_html=True)
        stat_comparison_row("xG", round(r['xG Hemma'], 2), round(r['xG Borta'], 2))
        stat_comparison_row("Bollinnehav", int(r['Bollinnehav Hemma']), int(r['Bollinnehav Borta']), True)
        stat_comparison_row("Hörnor", int(r['Hörnor Hemma']), int(r['Hörnor Borta']))
        stat_comparison_row("Gula Kort", int(r['Gula kort Hemma']), int(r['Gula Kort Borta']))

    elif st.session_state.view_h2h is not None:
        if st.button("← Tillbaka"): 
            st.session_state.view_h2h = None
            st.rerun()
        m = st.session_state.view_h2h
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        league_name = m.get('response.league.name', 'Okänd liga')
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
            
            # --- ODDS-SEKTION MED DEBUG ---
            s_key = get_sport_key_from_league_name(league_name)
            all_market_odds, debug_url = fetch_odds_by_league(s_key)
            
            if all_market_odds == "QUOTA_EXCEEDED":
                st.error("Odds-kvoten är slut.")
            else:
                h2h_o, totals = get_match_odds_from_cache(h_team, a_team, all_market_odds)
                if h2h_o or totals:
                    oc1, oc2 = st.columns(2)
                    with oc1:
                        if h2h_o:
                            st.write("**1X2 Odds**")
                            for o in h2h_o: st.write(f"{o['name']}: **{o['price']}**")
                    with oc2:
                        if totals:
                            st.write("**Mål 2.5**")
                            for o in totals:
                                if o.get('point') == 2.5: st.write(f"{o['name']}: **{o['price']}**")
                else:
                    st.info(f"Inga odds hittades för {h_team} vs {a_team} i {s_key}.")

            # --- DEBUG CONSOLE (UTVIKBAR) ---
            with st.expander("🛠️ Felsökning: API-anrop"):
                st.write(f"**Identifierad liga:** {league_name}")
                st.write(f"**Använd Sport Key:** {s_key}")
                st.write(f"**Fullständig URL:** {debug_url}")
                if all_market_odds and all_market_odds != "QUOTA_EXCEEDED":
                    st.write(f"**Antal matcher i API-svar:** {len(all_market_odds)}")
                else:
                    st.write("**API Status:** Inga data eller felkod")

            st.divider()
            st.markdown("<h3 style='text-align: center;'>📊 Lagjämförelse</h3>", unsafe_allow_html=True)
            comp_cols = [("Mål", 'response.goals.home', 'response.goals.away'), ("xG", 'xG Hemma', 'xG Borta'), ("Bollinnehav", 'Bollinnehav Hemma', 'Bollinnehav Borta'), ("Hörnor", 'Hörnor Hemma', 'Hörnor Borta'), ("Gula Kort", 'Gula kort Hemma', 'Gula Kort Borta')]
            for label, h_col, a_col in comp_cols:
                stat_comparison_row(label, round(h_stats[h_col].mean(), 2), round(a_stats[a_col].mean(), 2), "Bollinnehav" in label)

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matcher", "🛡️ Lagstatistik", "⚖️ Domaranalys", "🏆 Tabell"])
        with tab1:
            st.header("Matchcenter")
            mode = st.radio("Visa:", ["Nästa 50 matcher", "Senaste resultaten"], horizontal=True)
            d_df = df[df['response.fixture.status.short'] == ('NS' if mode == "Nästa 50 matcher" else 'FT')]
            for idx, r in d_df.sort_values('datetime', ascending=(mode=="Nästa 50 matcher")).head(50).iterrows():
                c_i, c_b = st.columns([5, 1.2])
                with c_i:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:5px; display:flex; align-items:center;"><div style="width:80px; font-size:0.8em;">{r["datetime"].strftime("%d %b")}</div><div style="flex:1; text-align:right; font-weight:bold;">{r["response.teams.home.name"]}</div><div style="margin:0 10px; background:#eee; border-radius:4px;">VS</div><div style="flex:1; text-align:left; font-weight:bold;">{r["response.teams.away.name"]}</div><div style="margin-left:15px; font-size:0.7em; color:blue;">{r.get("response.league.name", "")}</div></div>', unsafe_allow_html=True)
                with c_b:
                    if st.button("Analys", key=f"btn{idx}"):
                        if mode == "Nästa 50 matcher": st.session_state.view_h2h = r
                        else: st.session_state.view_match = r
                        st.rerun()

        with tab2:
            st.header("🛡️ Laganalys")
            all_teams = sorted(pd.concat([df['response.teams.home.name'], df['response.teams.away.name']]).unique())
            sel_team = st.selectbox("Välj lag:", all_teams)
            if sel_team:
                t_df = df[(df['response.teams.home.name'] == sel_team) | (df['response.teams.away.name'] == sel_team)]
                st.dataframe(t_df.head(10))

        with tab3:
            st.header("⚖️ Domaranalys")
            refs = sorted([r for r in df['ref_clean'].unique() if r not in ["0", "Okänd"]])
            sel_ref = st.selectbox("Välj domare:", refs)
            if sel_ref:
                r_df = df[df['ref_clean'] == sel_ref]
                st.metric("Gula/Match", round((r_df['Gula kort Hemma'] + r_df['Gula Kort Borta']).mean(), 2))

        with tab4:
            st.header("🏆 Tabell")
            if standings_df is not None: st.dataframe(standings_df)

else:
    st.error("Kunde inte ladda data.")
