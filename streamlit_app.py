# --- 3. LAYOUT (DETALJVY FÖR ANALYS/H2H) ---
    if st.session_state.view_mode in ["match_detail", "h2h_detail"]:
        if st.button("← Tillbaka"): 
            st.session_state.view_mode = "main"
            st.rerun()
        
        m = st.session_state.selected_match
        h_team, a_team = m['response.teams.home.name'], m['response.teams.away.name']
        
        # Header med loggor och resultat
        st.markdown(f"""
            <div style="background-color: #0e1117; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <div style="color: #ffcc00; font-weight: bold; letter-spacing: 2px;">FULL TIME</div>
                <div style="display: flex; justify-content: center; align-items: center; gap: 40px; margin-top: 10px;">
                    <div style="text-align: center;">
                        <img src="{m['response.teams.home.logo']}" width="80"><br>
                        <span style="font-size: 1.2rem; font-weight: bold;">{h_team}</span>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <div style="background: #e63946; color: white; font-size: 3rem; padding: 10px 25px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.home'])}</div>
                        <div style="font-size: 2rem;">-</div>
                        <div style="background: #e63946; color: white; font-size: 3rem; padding: 10px 25px; border-radius: 5px; font-weight: bold;">{int(m['response.goals.away'])}</div>
                    </div>
                    <div style="text-align: center;">
                        <img src="{m['response.teams.away.logo']}" width="80"><br>
                        <span style="font-size: 1.2rem; font-weight: bold;">{a_team}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # OM LÄGET ÄR "ANALYS" (Resultat-sidan), VISA MATCHSTATISTIK
        if st.session_state.view_mode == "match_detail":
            st.markdown("<div class='section-header'>MATCH STATISTICS</div>", unsafe_allow_html=True)
            
            # Hjälpfunktion för att rita snygga rader (likt bilden)
            def draw_stat_row(label, home_val, away_val, is_pct=False):
                suffix = "%" if is_pct else ""
                st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 8px;">
                        <div style="flex: 1; text-align: right; font-size: 1.5rem; font-weight: bold; padding-right: 20px;">{home_val}{suffix}</div>
                        <div style="width: 200px; background: #e63946; color: white; text-align: center; padding: 5px; font-weight: bold; font-size: 0.8rem; border-radius: 3px;">{label.upper()}</div>
                        <div style="flex: 1; text-align: left; font-size: 1.5rem; font-weight: bold; padding-left: 20px;">{away_val}{suffix}</div>
                    </div>
                """, unsafe_allow_html=True)

            # Här hämtar vi datan från den valda matchen (m)
            draw_stat_row("Ball Possession", int(m['Bollinnehav Hemma']), int(m['Bollinnehav Borta']), True)
            draw_stat_row("Expected Goals (xG)", m['xG Hemma'], m['xG Borta'])
            draw_stat_row("Shots on Target", int(m['Skott på mål Hemma']), int(m['Skott på mål Borta']))
            draw_stat_row("Total Shots", int(m['Skott totalt Hemma']), int(m['Skott totalt Borta']))
            draw_stat_row("Corner Kicks", int(m['Hörnor Hemma']), int(m['Hörnor Borta']))
            draw_stat_row("Fouls", int(m['Fouls Hemma']), int(m['Fouls Borta']))
            draw_stat_row("Yellow Cards", int(m['Gula kort Hemma']), int(m['Gula Kort Borta']))
            draw_stat_row("Offsides", int(m['Offside Hemma']), int(m['Offside Borta']))
            draw_stat_row("Pass Accuracy", int(m['Passningssäkerhet Hemma']), int(m['Passningssäkerhet Borta']), True)

        # OM LÄGET ÄR "H2H" (Nästa matcher), VISA DIN GAMLA H2H-LAYOUT
        else:
            # (Här behåller du din befintliga kod för H2H-snitt och inbördes möten)
            st.markdown("### ⚔️ Historisk H2H Analys")
            # ... din befintliga H2H-kod ...
