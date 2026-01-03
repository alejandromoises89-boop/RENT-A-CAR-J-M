import streamlit as st
import urllib.parse
import io
from database import init_db, obtener_flota, guardar_reserva
from styles import aplicar_estilos
from auth import login_screen
from admin import panel_control
from reportlab.pdfgen import canvas

# Configuración Inicial
st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")
init_db()
aplicar_estilos()

def generar_contrato_pdf(nombre, auto, f1, f2):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(150, 800, "CONTRATO DE ALQUILER - J&M ASOCIADOS")
    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"ARRENDATARIO: {nombre}")
    p.drawString(50, 730, f"VEHÍCULO: {auto}")
    p.drawString(50, 710, f"FECHAS: Desde {f1} hasta {f2}")
    p.drawString(50, 680, "TÉRMINOS: El cliente declara recibir el vehículo en óptimas condiciones.")
    p.drawString(50, 660, "Firma del Cliente: _________________________")
    p.showPage()
    p.save()
    return buffer.getvalue()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    # Menú de Pestañas
    titulos = ["🚗 Catálogo", "📅 Mi Historial", "💬 Comentarios"]
    if st.session_state.role == "admin":
        titulos.append("⚙️ Panel de Control")
    
    tabs = st.tabs(titulos)

    with tabs[0]:
        st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
        for auto in obtener_flota():
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} - {auto['color']}")
                st.write(f"**Tarifa:** {auto['precio']:,} Gs")
                f_ini = st.date_input("Recogida", key=f"i_{auto['id']}")
                f_fin = st.date_input("Devolución", key=f"f_{auto['id']}")
                
                if st.button(f"Confirmar Reserva {auto['nombre']}", key=f"btn_{auto['id']}"):
                    guardar_reserva(st.session_state.user_name, auto['nombre'], f_ini, f_fin, auto['precio'])
                    
                    st.success("✅ Reserva Exitosa. Procede al pago.")
                    
                    # 1. Contrato PDF
                    pdf = generar_contrato_pdf(st.session_state.user_name, auto['nombre'], f_ini, f_fin)
                    st.download_button("📥 Descargar mi Contrato PDF", data=pdf, file_name=f"Contrato_JM_{st.session_state.user_name}.pdf")
                    
                    # 2. QR PIX Dinámico
                    # QR Generado con API pública para visualización inmediata
                    pix_data = "24510861818-Marina-Baez-Santander"
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={pix_data}", caption="Escanea para pagar vía PIX")
                    st.code("Llave PIX: 24510861818\nTitular: Marina Baez\nBanco: Santander", language="text")

                    # 3. WhatsApp
                    mensaje = f"¡Hola J&M! Agendé el {auto['nombre']} del {f_ini} al {f_fin}. Ya tengo mi contrato. Envío comprobante de pago."
                    st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(mensaje)}" target="_blank">📲 Enviar Comprobante WhatsApp</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[-1]:
            panel_control()
