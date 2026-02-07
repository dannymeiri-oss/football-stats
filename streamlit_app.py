import streamlit as st
import pandas as pd

# --- PERFECT LAYOUT - RÖR EJ ---
# Version: 2026-02-07 (Korrigerad)

def format_last_10_table(df, team_name):
    """
    Skapar en exakt kopia av tabell-designen i din bild.
    """
    if df.empty:
        return "<p style='color: gray; padding: 20px;'>Ingen statistik tillgänglig för tillfället.</p>"

    # HTML och CSS för att matcha bilden (image_0fdc1e.png)
    html = f"""
    <div style="margin-bottom: 25px; font-family: 'Source Sans Pro', sans-serif;">
        <h3 style="margin-bottom: 15px; font-size: 1.4rem; color: #31333F; display: flex; align-items: center;">
            <span style="margin-right: 10px;">📅</span> Senaste 10 matcher för {team_name}
        </h3>
        <div style="border: 1px solid #e6e9ef; border-radius: 8px; overflow: hidden; background-color: white;">
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="background-color: #f8f9fb; border-bottom: 1px solid #e6e9ef;">
                        <th style="padding: 12px 15px; color: #666; font-weight: 400; font-size: 0.9rem; width: 20%;">Speltid</th>
                        <th style="padding: 12px 15px; color: #666; font-weight: 400; font-size: 0.9rem; width: 35%;">Hemmalag</th>
                        <th style="padding: 12px 15px; color: #666; font-weight: 400; font-size: 0.9rem; text-align: center; width: 5%;">H</th>
                        <th style="padding: 12px 15px; color: #666; font-weight: 400; font-size: 0.9rem; text-align: center; width: 5%;">B</th>
                        <th style="padding: 12px 15px; color: #666; font-weight: 400; font-size: 0.9rem; width: 35%;">Bortalag</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for _, row in df.iterrows():
        html += f"""
                    <tr style="border-bottom: 1px solid #f0f2f6;">
                        <td style="padding: 10px 15px; font-size: 0.9rem;">{row.get('date', '')}</td>
                        <td style="padding: 10px 15px; font-size: 0.9rem;">{row.get('home_team', '')}</td>
                        <td style="padding: 10px 15px; font-size: 0.9rem; text-align: center; font-weight: 500;">{row.get('home_score', 0)}</td>
                        <td style="padding: 10px 15px; font-size: 0.9rem; text-align: center; font-weight: 500;">{row.get('away_score', 0)}</td>
                        <td style="padding: 10px 15px; font-size: 0.9rem;">{row.get('away_team', '')}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    return html

def render_h2h_view(match_data):
    """
    Huvudvy för H2H med domarinformation och tabeller.
    """
    # --- DOMARRAD (Enligt sparade instruktioner) ---
    # Visas ovanför "SEASON AVERAGES COMPARISON"
    ref_name = match_data.get('referee', 'Okänd')
    ref_yellow = match_data.get('ref_avg_yellow', '-')
    
    st.markdown("---")
    if ref_name == "Okänd":
        st.markdown(f"**Domare:** Okänd")
    else:
        st.markdown(f"👤 **Domare:** {ref_name} | **Gula kort (snitt senaste 10):** {ref_yellow}")
    
    st.header("SEASON AVERAGES COMPARISON")
    
    # Här renderas de två tabellerna sida vid sida
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = match_data.get('home_team_name', 'Hemmalag')
        home_matches = match_data.get('home_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(home_matches, home_team), unsafe_allow_html=True)
        
    with col2:
        away_team = match_data.get('away_team_name', 'Bortalag')
        away_matches = match_data.get('away_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(away_matches, away_team), unsafe_allow_html=True)

# Exempel på hur man kör (Main-del)
def main():
    # Demo-data för att testa layouten
    demo_data = {
        'referee': 'Felix Zwayer',
        'ref_avg_yellow': '4.2',
        'home_team_name': '1. FC Heidenheim',
        'away_team_name': 'Hamburger SV',
        'home_last_10': pd.DataFrame([
            {'date': '01 Feb 2026', 'home_team': 'Borussia Dortmund', 'home_score': 3, 'away_score': 2, 'away_team': '1. FC Heidenheim'},
            {'date': '24 Jan 2026', 'home_team': '1. FC Heidenheim', 'home_score': 0, 'away_score': 3, 'away_team': 'RB Leipzig'},
            {'date': '17 Jan 2026', 'home_team': 'VfL Wolfsburg', 'home_score': 1, 'away_score': 1, 'away_team': '1. FC Heidenheim'}
        ])
    }
    render_h2h_view(demo_data)

if __name__ == "__main__":
    main()
