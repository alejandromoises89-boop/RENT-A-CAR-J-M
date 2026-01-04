import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from fpdf import FPDF
import io
from streamlit_js_eval import streamlit_js_eval

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="J&M ASOCIADOS", layout="wide", page_icon="🚗")

# Inicialización de Base de Datos de Usuarios y Reservas
if 'db_usuarios' not in st.session_state:
    st.session_state.db_usuarios = pd.DataFrame(columns=["Nombre", "Email", "Teléfono", "Password", "Documento", "País"])
if 'db_reservas' not in st.session_state:
    st.session_state.db_reservas = pd.DataFrame(columns=["ID", "Fecha", "Cliente", "Auto", "Total", "Estado"])
if 'logueado' not in st.session_state:
    st.session_state.logueado = False

# --- 2. ESTILO CSS PREMIUM (Logo Serigrafía y Layout) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,700&display=swap');
    
    /* Fondo Degradado Bordo Login */
    .login-bg {
        background: linear-gradient(180deg, #800000 0%, #300000 100%);
        padding: 50px; border-radius: 20px; text-align: center;
    }
    
    /* Logo Tipo Serigrafía Cursiva */
    .logo-serigrafia {
        font-family: 'Playfair Display', serif;
        color: #D4AF37; font-size: 60px; font-style: italic;
        text-shadow: 2px 2px 4px #000; margin-bottom: 0;
    }
    
    .sub-logo { color: #D4AF37; letter-spacing: 3px; font-size: 14px; margin-top: -10px; }

    /* Inputs Dorados */
    .stTextInput>div>div>input {
        border: 1px solid #D4AF37 !important; border-radius: 8px !important;
        background: rgba(255,255,255,0.05) !important; color: white !important;
    }
    
    /* Botones Bordó Destacados */
    .stButton>button {
        background-color: #900000 !important; color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important; font-weight: bold !important;
        border-radius: 10px !important; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.05); background-color: #B00000 !important; }

    /* Exhibidor de Autos (Cuadrado Blanco) */
    .car-display {
        background: white; border: 1px solid #DDD; padding: 20px;
        border-radius: 15px; text-align: center; color: black;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES DE LÓGICA (Contrato y Registro) ---
def generar_contrato_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO - J&M ASOCIADOS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    # Relleno automático del contrato
    texto = f"""Por la presente, J&M ASOCIADOS entrega en alquiler el vehículo {datos['Auto']} 
al cliente {datos['Cliente']}, identificado con documento {datos['Doc']}, 
por un periodo de {datos['Dias']} días. 
Monto Total: {datos['Monto']}.
El vehículo cuenta con Seguro Carta Verde y Kilometraje Libre para PY, BR y AR."""
    pdf.multi_cell(0, 10, texto)
    pdf.ln(20)
    pdf.cell(90, 10, "Firma Digital Cliente: ____________", 0)
    pdf.cell(90, 10, "Firma J&M: [Sello Digital]", 0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ DE LOGIN / REGISTRO ---
if not st.session_state.logueado:
    st.markdown('<div class="login-bg">', unsafe_allow_html=True)
    st.markdown('<h1 class="logo-serigrafia">J&M Asociados</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-logo">ALQUILER DE VEHÍCULOS & CONSULTORÍA</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        opcion = st.radio("Acción", ["Iniciar Sesión", "Registrarse", "Recuperar Contraseña"], horizontal=True)
        
        if opcion == "Iniciar Sesión":
            u = st.text_input("Correo o Teléfono")
            p = st.text_input("Contraseña", type="password")
            # Simulación de Biometría (Solo visible en dispositivos móviles compatibles)
            if st.button("Ingresar con Biometría"):
                st.info("Solicitando huella/FaceID...")
            
            if st.button("ENTRAR AL SISTEMA"):
                if u == "admin" or u == "0991681191": # Ejemplo
                    st.session_state.logueado = True
                    st.rerun()

        elif opcion == "Registrarse":
            with st.form("reg"):
                st.text_input("Nombre y Apellido")
                st.text_input("Email")
                st.text_input("Teléfono")
                st.selectbox("Tipo de Documento", ["C.I.", "RG", "CPF", "Pasaporte"])
                st.text_input("Nro Documento")
                st.text_input("Password", type="password")
                if st.form_submit_button("CREAR CUENTA"):
                    st.success("Cuenta creada. Ya puede iniciar sesión.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. INTERFAZ INTERNA ---
else:
    # Encabezado Fijo
    st.markdown('<h1 style="color:#D4AF37; font-family:serif;">J&M ASOCIADOS</h1>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📜 Mi Historial", "📍 Ubicación", "🔐 Panel Admin"])

    with tabs[0]: # CATÁLOGO CON EXHIBIDORES
        st.markdown('<div style="background:#800000; padding:10px; color:white; border-radius:10px;">SELECCIONE SU VEHÍCULO - DISPONIBILIDAD INMEDIATA</div>', unsafe_allow_html=True)
        
        AUTOS = {
            "Toyota Vitz Blanco": {"trans": "Automático", "pas": 5, "comb": "Nafta", "abs": "Sí", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            "Hyundai Tucson": {"trans": "Automático", "pas": 5, "comb": "Diesel", "abs": "Sí", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"}
        }

        for nombre, info in AUTOS.items():
            st.markdown(f"""
            <div class="car-display">
                <img src="{info['img']}" width="300">
                <h2>{nombre}</h2>
                <p>⚙️ {info['trans']} | 👥 {info['pas']} Pasajeros | ⛽ {info['comb']}</p>
                <p>✅ ABS | ✅ Seguro Carta Verde | ✅ Kilometraje Libre (PY-BR-AR)</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Reservar {nombre}"):
                st.session_state.reservando = nombre

        if 'reservando' in st.session_state:
            st.divider()
            st.markdown("### Finalizar Pago y Contrato")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PIX-KEY-24510861818")
            st.write("Banco Santander - Marina Baez - PIX: 24510861818")
            
            # Botón WhatsApp Corporativo
            wa_link = "https://wa.me/595991681191?text=Hola%20J&M,%20envio%20mi%20comprobante%20de%20pago"
            st.markdown(f'<a href="{wa_link}"><button style="background:#25D366; color:white; padding:10px; border-radius:5px; border:none;">📲 Enviar Comprobante vía WhatsApp</button></a>', unsafe_allow_html=True)
            
            # Vista Previa Contrato
            pdf_contrato = generar_contrato_pdf({"Auto": st.session_state.reservando, "Cliente": "Usuario J&M", "Doc": "123456", "Dias": 3, "Monto": "R$ 600"})
            st.download_button("📥 Descargar Contrato Firmado", pdf_contrato, "Contrato_JM.pdf")

    with tabs[2]: # UBICACIÓN PROFESIONAL
        st.subheader("Ubícanos en Ciudad del Este")
        st.markdown("""
        **Dirección:** Centro de CDE - Paraguay  
        **WhatsApp:** [+595 991 681191](https://wa.me/595991681191)  
        **Instagram:** [@jm_asociados_consultoria](https://www.instagram.com/jm_asociados_consultoria)
        """)
        # Mapa Simulado
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.378772322307!2d-54.6111!3d-25.5111!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQwLjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1625510000000!5m2!1ses!2spy" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

    # Botón Cerrar Sesión Estilo Login
    st.sidebar.markdown("---")
    if st.sidebar.button("CERRAR SESIÓN DEL SISTEMA"):
        st.session_state.logueado = False
        st.rerun()
