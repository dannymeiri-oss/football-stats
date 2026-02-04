# --- MATCHSTATISTIK GRUPPERAD ---
        
        st.markdown('<div class="section-header">ANFALL & CHANSER</div>', unsafe_allow_html=True)
        draw_stat_item("Expected Goals (xG)", m.get('xG Hemma', 0), m.get('xG Borta', 0))
        draw_stat_item("Skott på mål", m.get('Skott på mål Hemma', 0), m.get('Skott på mål Borta', 0))
        draw_stat_item("Totala Skott", m.get('Total Skott Hemma', 0), m.get('Total Skott Borta', 0))
        draw_stat_item("Skott Utanför", m.get('Skott Utanför Hemma', 0), m.get('Skott Utanför Borta', 0))
        draw_stat_item("Blockerade Skott", m.get('Blockerade Skott Hemma', 0), m.get('Blockerade Skott Borta', 0))
        draw_stat_item("Skott i Box", m.get('Skott i Box Hemma', 0), m.get('Skott i Box Borta', 0))
        draw_stat_item("Skott utanför Box", m.get('Skott utanför Box Hemma', 0), m.get('Skott utanför Box Borta', 0))
        
        st.markdown('<div class="section-header">SPELUPPBYGGNAD</div>', unsafe_allow_html=True)
        draw_stat_item("Bollinnehav", m.get('Bollinnehav Hemma', 0), m.get('Bollinnehav Borta', 0), is_percent=True)
        draw_stat_item("Passningar", m.get('Passningar Hemma', 0), m.get('Passningar Borta', 0))
        draw_stat_item("Passningssäkerhet", m.get('Passningssäkerhet Hemma', 0), m.get('Passningssäkerhet Borta', 0), is_percent=True)
        draw_stat_item("Hörnor", m.get('Hörnor Hemma', 0), m.get('Hörnor Borta', 0))
        draw_stat_item("Offside", m.get('Offside Hemma', 0), m.get('Offside Borta', 0))

        st.markdown('<div class="section-header">FÖRSVAR & DISCIPLIN</div>', unsafe_allow_html=True)
        draw_stat_item("Räddningar", m.get('Räddningar Hemma', 0), m.get('Räddningar Borta', 0))
        draw_stat_item("Fouls", m.get('Fouls Hemma', 0), m.get('Fouls Borta', 0))
        draw_stat_item("Gula Kort", m.get('Gula kort Hemma', 0), m.get('Gula Kort Borta', 0))
        draw_stat_item("Röda Kort", m.get('Röda Kort Hemma', 0), m.get('Röda Kort Borta', 0))
