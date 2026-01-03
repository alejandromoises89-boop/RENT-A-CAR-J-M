import streamlit as st
import urllib.parse
from database import init_db, obtener_flota, verificar_disponibilidad, guardar_reserva
from styles import aplicar_estilos
from auth import login_screen
from admin import panel_control

# Inicialización
st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")
init_db()
aplicar_estilos()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos</p></div>', unsafe_allow_html=True)
    
    tabs_nombres = ["Catálogo", "Mi Historial", "Comentarios"]
    if st.session_state.role == "admin": tabs_nombres.append("Panel de Control")
    
    tabs = st.tabs(tabs_nombres)

    with tabs[0]: # CATALOGO
        # Cotización Simulada Cambios Chaco
        usd, brl = 7550, 1450
        st.subheader("Catálogo de Revista - Flota J&M")
        
        for auto in obtener_flota():
            with st.container():
                col1, col2 = st.columns([1, 2])
                col1.image(auto['img'], use_container_width=True)
                col2.write(f"### {auto['nombre']} - {auto['color']}")
                col2.write(f"**Gs. {auto['precio']:,}** | **USD {(auto['precio']/usd):.2f}** | **R$ {(auto['precio']/brl):.2f}**")
                
                ini = col2.date_input("Fecha Inicio", key=f"i_{auto['id']}")
                fin = col2.date_input("Fecha Fin", key=f"f_{auto['id']}")
                
                if col2.button(f"Alquilar {auto['nombre']}", key=f"b_{auto['id']}"):
                    if verificar_disponibilidad(auto['id'], ini, fin):
                        guardar_reserva(st.session_state.user_name, auto['id'], ini, fin, auto['precio'])
                        st.success(f"¡Reserva confirmada de {ini} a {fin}!")
                        
                        # Datos PIX y WhatsApp
                        msg = f"Es un placer saludarte, {st.session_state.user_name}. Alquiler agendado de {ini} a {fin}. PIX: 24510861818 Marina Baez Santander."
                        st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank">📲 Notificar Pago (WhatsApp)</a>', unsafe_allow_html=True)
                    else:
                        st.error("No disponible en estas fechas.")

    if st.session_state.role == "admin" and len(tabs) > 3:
        with tabs[3]: panel_control()
