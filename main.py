# --- PESTAÑA UBICACIÓN (DIRECCIÓN EXACTA Y MAPA) ---
    with tabs[2]:
        st.subheader("📍 Ubicación Exacta - JM Asociados")
        
        # Diseño en dos columnas: Información a la izquierda, Mapa a la derecha
        col_map1, col_map2 = st.columns([1, 1.8])
        
        with col_map1:
            st.markdown(f"""
                <div style="background-color: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; border-left: 5px solid #D4AF37;">
                    <h4 style="color: #D4AF37; margin-top:0;">Datos de Contacto</h4>
                    <p><b>📍 Dirección:</b> C/ Farid Rahal Canan, Ciudad del Este, Paraguay.</p>
                    <p><b>📞 Corporativo:</b> 0991 681191</p>
                    <hr style="border-color: rgba(212, 175, 55, 0.3);">
                    <p>Escanea el QR o haz clic en los botones para contactarnos o seguirnos en nuestras redes.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Botón de WhatsApp
            st.markdown('<a href="https://wa.me/595991681191" class="btn-wa-confirm" style="margin-bottom:10px;">📲 WhatsApp Corporativo</a>', unsafe_allow_html=True)
            
            # Botón de Instagram (Link solicitado)
            st.markdown("""
                <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" 
                   style="display: block; background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%); 
                          color: white !important; text-align: center; padding: 12px; border-radius: 10px; 
                          text-decoration: none; font-weight: bold; margin-top: 10px;">
                    📸 Seguir en Instagram
                </a>
            """, unsafe_allow_html=True)

        with col_map2:
            # Iframe de Google Maps configurado para la ubicación exacta de JM Asociados en Ciudad del Este
            # Este mapa permite al usuario hacer zoom y ver la calle Farid Rahal Canan directamente.
            st.markdown("""
                <iframe 
                    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.94165922379!2d-54.6125!3d-25.5085!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f685764d95d10d%3A0x6a05325785084976!2sJM%20Asociados!5e0!3m2!1ses!2spy!4v1700000000000!5m2!1ses!2spy" 
                    width="100%" 
                    height="450" 
                    style="border:0; border-radius:15px; box-shadow: 0 10px 20px rgba(0,0,0,0.5);" 
                    allowfullscreen="" 
                    loading="lazy" 
                    referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            """, unsafe_allow_html=True)
