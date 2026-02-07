import streamlit as st
import pandas as pd

# ==========================================
# --- PERFECT LAYOUT - RÖR EJ ---
# Version: 2026-02-07
# ==========================================

def format_last_10_table(df, team_name):
    """
    Skapar en snygg HTML-tabell för 'Senaste 10 matcher' baserat på din bild.
    Innehåller kolumnerna: Speltid, Hemmalag, H, B, Bortalag.
    """
    if df.empty:
        return f"<div style='border: 1px solid #e6e9ef; border-radius: 10px; padding: 20px; color: gray;'>Ingen statistik tillgänglig för {team_name}.</div>"

    # CSS för att matcha din bifogade bild exakt
    table_style = """
    <style>
        .match-container {
            border: 1px solid #e6e9ef;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 25px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: white;
        }
        .match-header {
            padding: 12px 15px;
            background-color: white;
            border-bottom: 1px solid #e6e9ef;
            font-weight: 600;
            font-size: 1.1rem;
            color: #31333F;
        }
        .match-table {
            width: 100%;
            border-collapse: collapse;
        }
        .match-table thead {
            background-color: #f8f9fb;
            border-bottom: 1px solid #e6e9ef;
        }
        .match-table th {
            padding: 10px 15px;
            color: #666;
            font-weight: 500;
            font-size: 0.85rem;
            text-align: left;
            text-transform: uppercase;
        }
        .match-table td {
            padding: 10px 15px;
            border-bottom: 1px solid #f0f2f6;
            font-size: 0.9rem;
            color: #31333F;
        }
        .center-text { text-align: center !important; }
        .score-box { font-weight: bold; width: 40px; }
    </style>
    """

    html = table_style + '<div class="match-container">'
    html += f'<div class="match-header">📅 Senaste 10 matcher för {team_name}</div>'
    html += '<table class="match-table"><thead><tr>'
    html += '<th>Speltid</th><th>Hemmalag</th><th class="center-text">H</th><th class="center-text">B</th><th>Bortalag</th>'
    html += '</tr></thead><tbody>'

    for _, row in df.iterrows():
        # Säkerställ att vi har värden även om data saknas
        date = row.get('date', '-')
        home = row.get('home_team', '-')
        h_score = row.get('home_score', 0)
        a_score = row.get('away_score', 0)
        away = row.get('away_team', '-')

        html += f"""
        <tr>
            <td style="width: 20%;">{date}</td>
            <td style="width: 35%;">{home}</td>
            <td class="center-text score-box">{h_score}</td>
            <td class="center-text score-box">{a_score}</td>
            <td style="width: 35%;">{away}</td>
        </tr>
        """
    
    html += "</tbody></table></div>"
    return html

def render_h2h_view(match_data):
    """
    Renderar H2H-vyn med korrekt placerad domarrad och snygga tabeller.
    """
    # 1. DOMARRAD (Enligt din instruktion: Ovanför Season Averages)
    ref_name = match_data.get('referee', '')
    ref_avg = match_data.get('ref_avg_yellow', '-')

    if not ref_name or ref_name == "Okänd":
        st.info("👤 **Domare:** Okänd")
    else:
        st.info(f"👤 **Domare:** {ref_name} | **Gula kort (snitt senaste 10):** {ref_avg}")

    # 2. SEASON AVERAGES COMPARISON (Titel)
    st.header("SEASON AVERAGES COMPARISON")
    
    # --- Här ligger din befintliga jämförelsestatistik ---
    # (Behåll din existerande kod för Team Analysis här)
    
    st.markdown("---")

    # 3. SENASTE MATCHER (Två kolumner)
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = match_data.get('home_team_name', 'Hemmalag')
        home_df = match_data.get('home_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(home_df, home_team), unsafe_allow_html=True)
        
    with col2:
        away_team = match_data.get('away_team_name', 'Bortalag')
        away_df = match_data.get('away_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(away_df, away_team), unsafe_allow_html=True)

# --- Exempel på main för att köra koden ---
def main():
    # Demo-data (ersätts av din riktiga data-import)
    demo_data = {
        'referee': 'Felix Zwayer',
        'ref_avg_yellow': '4.2',
        'home_team_name': '1. FC Heidenheim',
        'away_team_name': 'Hamburger SV',
        'home_last_10': pd.DataFrame([
            {'date': '01 Feb 2026', 'home_team': 'Dortmund', 'home_score': 3, 'away_score': 2, 'away_team': 'Heidenheim'},
            {'date': '24 Jan 2026', 'home_team': 'Heidenheim', 'home_score': 0, 'away_score': 3, 'away_team': 'RB Leipzig'}
        ]),
        'away_last_10': pd.DataFrame([
            {'date': '31 Jan 2026', 'home_team': 'Hamburger SV', 'home_score': 2, 'away_score': 1, 'away_team': 'Köln'},
            {'date': '25 Jan 2026', 'home_team': 'Hertha', 'home_score': 1, 'away_score': 1, 'away_team': 'Hamburger SV'}
        ])
    }
    render_h2h_view(demo_data)

if __name__ == "__main__":
    main()
