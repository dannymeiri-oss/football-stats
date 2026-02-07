import streamlit as st
import pandas as pd

# --- PERFECT LAYOUT - RÖR EJ ---
# Version: 2026-02-07
# Syfte: Exakt tabell-design för Senaste 10 matcher + Domarinformation.

def format_last_10_table(df, team_name):
    """
    Skapar en snygg tabell baserat på användarens bild.
    Kolumner: Speltid, Hemmalag, H, B, Bortalag.
    """
    if df.empty:
        return "<p style='color: gray; padding: 10px;'>Ingen statistik tillgänglig.</p>"

    # CSS för rundade hörn och ren design
    table_style = """
    <style>
        .custom-table-container {
            border: 1px solid #e6e9ef;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
            font-family: 'Source Sans Pro', sans-serif;
        }
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        .custom-table thead {
            background-color: #f8f9fb;
            border-bottom: 1px solid #e6e9ef;
        }
        .custom-table th {
            padding: 12px 10px;
            color: #666;
            font-weight: 500;
            font-size: 14px;
            text-align: left;
        }
        .custom-table td {
            padding: 10px;
            border-bottom: 1px solid #f0f2f6;
            font-size: 14px;
            color: #31333F;
        }
        .text-center { text-align: center !important; }
        .score-col { font-weight: 600; width: 30px; }
    </style>
    """

    html = table_style + f'<div class="custom-table-container">'
    html += f'<div style="padding: 10px 15px; border-bottom: 1px solid #e6e9ef; font-weight: bold;">📅 Senaste 10 matcher för {team_name}</div>'
    html += '<table class="custom-table"><thead><tr>'
    html += '<th>Speltid</th><th>Hemmalag</th><th class="text-center">H</th><th class="text-center">B</th><th>Bortalag</th>'
    html += '</tr></thead><tbody>'

    for _, row in df.iterrows():
        html += f"""
        <tr>
            <td style="width: 20%;">{row.get('date', '')}</td>
            <td style="width: 35%;">{row.get('home_team', '')}</td>
            <td class="text-center score-col">{row.get('home_score', 0)}</td>
            <td class="text-center score-col">{row.get('away_score', 0)}</td>
            <td style="width: 35%;">{row.get('away_team', '')}</td>
        </tr>
        """
    
    html += "</tbody></table></div>"
    return html

def render_h2h_view(match_data):
    """
    Renderar vyn enligt instruktioner.
    """
    # 1. Domarinformation (Ska ligga ovanför Season Averages)
    ref_name = match_data.get('referee', 'Okänd')
    ref_yellow = match_data.get('ref_avg_yellow', '-')
    
    if ref_name == "Okänd" or not ref_name:
        st.markdown("### Domare: Okänd")
    else:
        # Visar namn och snitt gula kort
        st.markdown(f"### 👤 Domare: {ref_name} | Gula kort (snitt): {ref_yellow}")

    st.markdown("---")
    st.header("SEASON AVERAGES COMPARISON")
    
    # 2. Tabeller för Senaste 10 matcher
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = match_data.get('home_team_name', 'Hemmalag')
        home_df = match_data.get('home_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(home_df, home_team), unsafe_allow_html=True)
        
    with col2:
        away_team = match_data.get('away_team_name', 'Bortalag')
        away_df = match_data.get('away_last_10', pd.DataFrame())
        st.markdown(format_last_10_table(away_df, away_team), unsafe_allow_html=True)

# --- SLUT PÅ PERFECT LAYOUT ---
