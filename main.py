import streamlit as st
import urllib.parse
# Importaciones de tus archivos locales
from database import init_db, obtener_flota
from styles import aplicar_estilos
from auth import login_screen
from admin import panel_control

# Configuración inicial
st.set_page_config(page_title="J&M Asociados", layout="wide")
init_db()
aplicar_estilos()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos</p></div>', unsafe_allow_html=True)
    
    tabs_labels = ["Catálogo", "Mi Historial", "Comentarios"]
    if st.session_state.role == "admin": 
        tabs_labels.append("Panel de Control")
    
    tabs = st.tabs(tabs_labels)

    with tabs[0]:
        st.subheader("Nuestra Flota")
        usd, brl = 7550, 1450 # Cotización manual aproximada
        for auto in obtener_flota():
            with st.expander(f"{auto['nombre']} - {auto['color']}"):
                col1, col2 = st.columns([1, 2])
                col1.image(auto['img'])
                col2.write(f"**Precio:** {auto['precio']:,} Gs")
                col2.write(f"USD: {auto['precio']/usd:.2f} | BRL: {auto['precio']/brl:.2f}")
                if col2.button(f"Alquilar {auto['nombre']}", key=auto['id']):
                    msg = f"Es un placer saludarte. Alquiler agendado de J&M ASOCIADOS."
                    st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank">📲 WhatsApp</a>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[-1]:
            panel_control()
