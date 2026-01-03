import streamlit as st
import urllib.parse
from database import init_db, obtener_flota, verificar_disponibilidad, guardar_reserva
from styles import aplicar_estilos
from auth import login_screen
from admin import panel_control

st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")
init_db()
aplicar_estilos()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
    if 'temp_nombre' in st.session_state:
        link_app = "https://rent-a-car-j-m-nigbrrf2rzdecmahq2kbuq.streamlit.app/"
        mensaje = f"Es un placer saludarte, {st.session_state.temp_nombre}. Hemos habilitado nuestro nuevo Portal Ejecutivo de Rent-a-Car...\n\n🌐 Accede aquí: {link_app}\n\nJ&M ASOCIADOS | Alquiler de Vehículos & Alta Gama"
        st.link_button("📲 Enviar Bienvenida por WhatsApp", f"https://wa.me/{st.session_state.temp_tel}?text={urllib.parse.quote(mensaje)}")
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    menu = ["Catálogo", "Mi Historial", "Comentarios"]
    if st.session_state.role == "admin": menu.append("Panel de Control")
    tabs = st.tabs(menu)

    with tabs[0]:
        st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
        for auto in obtener_flota():
            col1, col2 = st.columns([1, 2])
            col1.image(auto['img'], use_container_width=True)
            col2.write(f"### {auto['nombre']} ({auto['color']})")
            col2.write(f"**Gs. {auto['precio']:,}**")
            ini = col2.date_input("Inicio", key=f"i_{auto['id']}")
            fin = col2.date_input("Fin", key=f"f_{auto['id']}")
            if col2.button(f"Reservar {auto['id']}", key=f"b_{auto['id']}"):
                if verificar_disponibilidad(auto['id'], ini, fin):
                    guardar_reserva(st.session_state.user_name, auto['id'], ini, fin, auto['precio'])
                    st.success("Reserva lista. Procede al pago PIX.")
                    msg_pago = f"Gracias por elegir J&M. Reservaste el {auto['nombre']} del {ini} al {fin}. Por favor adjunta aquí tu comprobante PIX."
                    st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg_pago)}" target="_blank">📲 Enviar Comprobante</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[-1]: panel_control()
