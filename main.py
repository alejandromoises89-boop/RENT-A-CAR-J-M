import streamlit as st
import urllib.parse
from database import init_db, obtener_flota, guardar_reserva
from styles import aplicar_estilos
from auth import login_screen
from admin import panel_control
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")
init_db()
aplicar_estilos()

# Función para crear el contrato PDF
def generar_pdf(nombre, auto, f1, f2):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "CONTRATO DE ALQUILER - J&M ASOCIADOS")
    p.drawString(100, 750, f"Arrendatario: {nombre}")
    p.drawString(100, 730, f"Vehículo: {auto}")
    p.drawString(100, 710, f"Periodo: {f1} al {f2}")
    p.drawString(100, 680, "Términos: El cliente se compromete a devolver el vehículo en las mismas condiciones.")
    p.showPage()
    p.save()
    return buffer.getvalue()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    
    # Definición de pestañas según rol
    titulos = ["🚗 Catálogo", "📅 Mi Historial", "💬 Comentarios"]
    if st.session_state.role == "admin":
        titulos.append("⚙️ Panel de Control")
    
    tabs = st.tabs(titulos)

    with tabs[0]: # CATALOGO
        st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
        for auto in obtener_flota():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(auto['img'], caption=auto['nombre'], use_container_width=True)
            with col2:
                st.subheader(f"{auto['nombre']} - {auto['color']}")
                st.write(f"💰 Precio: {auto['precio']:,} Gs")
                d1 = st.date_input("Recogida", key=f"d1_{auto['id']}")
                d2 = st.date_input("Devolución", key=f"d2_{auto['id']}")
                
                if st.button(f"Confirmar Reserva {auto['nombre']}", key=f"btn_{auto['id']}"):
                    guardar_reserva(st.session_state.user_name, auto['nombre'], d1, d2, auto['precio'])
                    
                    # Mostrar QR de PIX
                    st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=00020126360014BR.GOV.BCB.PIX0114245108618185204000053039865802BR5911MarinaBaez6008SANTANDER", caption="Escanea para pagar vía PIX")
                    st.info("Datos: 24510861818 | Marina Baez | Banco Santander")
                    
                    # Generar PDF
                    pdf = generar_pdf(st.session_state.user_name, auto['nombre'], d1, d2)
                    st.download_button("📩 Descargar mi Contrato PDF", data=pdf, file_name=f"Contrato_JM_{auto['id']}.pdf")
                    
                    # WhatsApp
                    msg = f"¡Hola! Reservé el {auto['nombre']}. Aquí mis datos para el contrato. Ya descargué mi PDF. Enviando comprobante PIX..."
                    st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank">📲 Avisar por WhatsApp</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[3]:
            panel_control()
