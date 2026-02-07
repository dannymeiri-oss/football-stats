import streamlit as st
import pandas as pd

# --- PERFECT LAYOUT - RÖR EJ ---
# Version: 2026-02-07
# Beskrivning: Fullständig layout med uppdaterad tabell-design för "Senaste 10 matcher"

def format_last_10_table(df, team_name):
    """
    Skapar en snygg HTML-tabell för 'Senaste 10 matcher' baserat på bilden.
    """
    if df.empty:
        return "<p>Ingen statistik tillgänglig.</p>"

    # HTML och CSS för att matcha bilden
    html = f"""
    <div style="border: 1px solid #e6e9ef; border-radius: 10px; overflow: hidden; margin-top: 10px; font-family: sans-serif;">
        <div style="padding: 15px; background-color: white; border-bottom: 1px solid #e6e9ef;">
            <h3 style="margin: 0; color: #31333F; font-size: 1.2rem;">📅 Senaste 10 matcher för {team_name}</h3>
        </div>
        <table style="width: 100%; border-collapse: collapse; background-color: white;">
            <thead>
                <tr style="border-bottom: 1px solid #e6e9ef; color: #666; font-size: 0.85rem; text-align: left;">
                    <th style="padding: 12px 15px;">Speltid</th>
                    <th style="padding: 12px 15px;">Hemmalag</th>
                    <th style="padding: 12px 15px; text-align: center;">H</th>
                    <th style="padding: 12px 15px; text-align: center;">B</th>
                    <th style="padding: 12px 15px;">Bortalag</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df.iterrows():
        html += f"""
                <tr style="border-bottom: 1px solid #f0f2f6; font-size: 0.9rem; color: #31333F;">
                    <td style="padding: 10px 15px;">{row.get('date', '')}</td>
                    <td style="padding: 10px 15px;">{row.get('home_team', '')}</td>
                    <td style="padding: 10px 15px; text-align: center; font-weight: bold;">{row.get('home_score', 0)}</td>
                    <td style="padding: 10px 15px; text-align: center; font-weight: bold;">{row.get('away_score', 0)}</td>
                    <td style="padding: 10px 15px;">{row.get('away_team', '')}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    return html

def render_h2h_view(match_data):
    """
    Renderar H2H-vyn med Domarinformation och laganalys.
    """
    st.title("Matchcenter")
    
    # --- DOMARRAD (Enligt instruktion) ---
    st.subheader("Matchinformation")
    ref_name = match_data.get('referee', 'Domare: Okänd')
    ref_yellow = match_data.get('ref_avg_yellow', '-')
    
    if ref_name != "Domare: Okänd":
        st.info(f"👤 **Domare:** {ref_name} | **Snitt gula kort (senaste 10):** {ref_yellow}")
    else:
        st.warning(f"👤 {ref_name}")

    st.markdown("---")
    
    # --- SEASON AVERAGES COMPARISON ---
    st.header("SEASON AVERAGES COMPARISON")
    # (Här ligger din befintliga tabell/logik för jämförelse)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Senaste 10 för Hemmalag
        home_team = match_data.get('home_team_name', 'Hemmalag')
        home_matches = match_data.get('home_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(home_matches, home_team), unsafe_print_html=True)
        
    with col2:
        # Senaste 10 för Bortalag
        away_team = match_data.get('away_team_name', 'Bortalag')
        away_matches = match_data.get('away_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(away_matches, away_team), unsafe_print_html=True)

def main():
    # Placeholder för data-laddning
    # I din riktiga app ersätts detta med anropet till din API/Databas
    sample_data = {
        'referee': 'Felix Zwayer',
        'ref_avg_yellow': '4.2',
        'home_team_name': '1. FC Heidenheim',
        'away_team_name': 'Hamburger SV',
        'home_last_10': pd.DataFrame([
            {'date': '01 Feb 2026', 'home_team': 'Borussia Dortmund', 'home_score': 3, 'away_score': 2, 'away_team': '1. FC Heidenheim'},
            {'date': '24 Jan 2026', 'home_team': '1. FC Heidenheim', 'home_score': 0, 'away_score': 3, 'away_team': 'RB Leipzig'}
        ]) # Fyll på med mer data här
    }
    
    render_h2h_view(sample_data)

if __name__ == "__main__":
    main()
