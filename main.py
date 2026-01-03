import streamlit as st
import urllib.parse
from database import init_db, obtener_flota, guardar_reserva
from styles import aplicar_estilos
from auth import login_screen
from admin import panel_control
from reportlab.pdfgen import canvas

st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")
init_db()
aplicar_estilos()

def generar_contrato_pdf(nombre, auto, f1, f2):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(150, 800, "CONTRATO DE ALQUILER - J&M ASOCIADOS")
    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"Arrendatario: {nombre}")
    p.drawString(50, 730, f"Vehículo Alquilado: {auto}")
    p.drawString(50, 710, f"Desde: {f1}  Hasta: {f2}")
    p.drawString(50, 680, "El cliente declara recibir el vehículo en perfectas condiciones.")
    p.drawString(50, 660, "Firma J&M Asociados: ____________________")
    p.showPage()
    p.save()
    return buffer.getvalue()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    # Menú dinámico
    menu = ["🚗 Catálogo", "📅 Mi Historial", "💬 Comentarios"]
    if st.session_state.role == "admin":
        menu.append("⚙️ Panel de Control")
    
    tabs = st.tabs(menu)

    with tabs[0]:
        st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
        for auto in obtener_flota():
            col1, col2 = st.columns([1, 2])
            col1.image(auto['img'], use_container_width=True)
            with col2:
                st.subheader(f"{auto['nombre']} - {auto['color']}")
                st.write(f"**Tarifa:** {auto['precio']:,} Gs")
                f1 = st.date_input("Inicio", key=f"f1_{auto['id']}")
                f2 = st.date_input("Fin", key=f"f2_{auto['id']}")
                
                if st.button(f"Confirmar Reserva {auto['nombre']}", key=f"btn_{auto['id']}"):
                    guardar_reserva(st.session_state.user_name, auto['nombre'], f1, f2, auto['precio'])
                    
                    st.success("✅ Reserva Agendada")
                    
                    # Generar y descargar PDF
                    pdf_data = generar_contrato_pdf(st.session_state.user_name, auto['nombre'], f1, f2)
                    st.download_button("📥 Descargar Contrato PDF", data=pdf_data, file_name="Contrato_JM.pdf")
                    
                    # Mostrar QR y Datos PIX
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PIX_LLAVE_24510861818_MARINA_BAEZ", caption="Escanea para pagar con PIX")
                    st.code("Llave PIX: 24510861818\nTitular: Marina Baez\nBanco: Santander", language="text")

                    # WhatsApp Link
                    mensaje = f"Hola J&M! Reservé el {auto['nombre']} del {f1} al {f2}. Adjunto mi comprobante PIX."
                    st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(mensaje)}" target="_blank">📲 Enviar Comprobante vía WhatsApp</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[-1]:
            panel_control()

