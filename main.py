import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JM ASOCIADOS - GESTIÓN", layout="wide")

# Estilos para la interfaz interna (Fondo Blanco, detalles Bordó y Dorado)
st.markdown("""
<style>
    .main { background-color: #FFFFFF; }
    .car-container {
        border: 2px solid #EEEEEE;
        border-radius: 15px;
        padding: 20px;
        background-color: white;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .header-band {
        background-color: #4A0404;
        color: #D4AF37;
        padding: 20px;
        text-align: center;
        font-family: 'Times New Roman', serif;
        font-size: 30px;
        font-weight: bold;
        border-bottom: 4px solid #D4AF37;
        margin-bottom: 30px;
    }
    .spec-box {
        font-size: 14px;
        color: #333;
        background: #F9F9F9;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        border-left: 3px solid #4A0404;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA DE NEGOCIO ---
if 'reservas' not in st.session_state:
    st.session_state.reservas = []

FLOTA = {
    "Hyundai Tucson 2012": {
        "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/",
        "pasajeros": 5, "combustible": "Diesel", "transmision": "Automática",
        "precio": 260, "abs": "Sí", "seguro": "Carta Verde Internacional"
    },
    "Toyota Vitz 2012 (Blanco)": {
        "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png",
        "pasajeros": 5, "combustible": "Nafta", "transmision": "Automática",
        "precio": 195, "abs": "Sí", "seguro": "Carta Verde Internacional"
    },
    "Toyota Voxy 2011": {
        "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png",
        "pasajeros": 7, "combustible": "Nafta", "transmision": "Secuencial",
        "precio": 240, "abs": "Sí", "seguro": "Carta Verde Internacional"
    }
}

# --- 3. FUNCIONES DE CONTRATO ---
def generar_contrato(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Times", size=12)
    pdf.ln(10)
    contenido = f"""
    FECHA: {datetime.date.today()}
    CLIENTE: {datos['nombre']}
    VEHICULO: {datos['auto']}
    DIAS DE USO: {datos['dias']}
    TOTAL A PAGAR: {datos['total']}
    
    CLAUSULAS:
    1. El vehículo cuenta con Seguro Carta Verde vigente.
    2. Kilometraje libre para Paraguay, Brasil y Argentina.
    3. El arrendatario se compromete a devolver el vehículo en las mismas condiciones.
    
    FIRMA CLIENTE: _____________________          FIRMA JM ASOCIADOS: [Digital]
    """
    pdf.multi_cell(0, 10, contenido)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ DE USUARIO ---
def pantalla_principal():
    st.markdown('<div class="header-band">JM ASOCIADOS - ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    
    pestanas = st.tabs(["🚗 CATÁLOGO DE EXHIBICIÓN", "📜 MI HISTORIAL", "📍 UBICACIÓN Y CONTACTO", "📊 PANEL ADMIN"])

    # PESTAÑA 1: CATÁLOGO
    with pestanas[0]:
        st.markdown('<div style="height:10px; background:#4A0404; width:100%;"></div>', unsafe_allow_html=True) # Divisoria rectangular
        
        cols = st.columns(2)
        for i, (nombre, info) in enumerate(FLOTA.items()):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="car-container">
                    <img src="{info['img']}" style="width:100%; max-width:300px; height:auto;">
                    <h2 style="color:#4A0404; font-family:serif;">{nombre}</h2>
                    <div class="spec-box">
                        <b>Pasajeros:</b> {info['pasajeros']} | <b>Motor:</b> {info['combustible']}<br>
                        <b>Transmisión:</b> {info['transmision']} | <b>ABS:</b> {info['abs']}<br>
                        <b>Seguro:</b> {info['seguro']}<br>
                        <b>Destinos:</b> Libre Brasil, Argentina y Paraguay
                    </div>
                    <p style="font-size:24px; color:#D4AF37; font-weight:bold;">R$ {info['precio']} / día</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"ALQUILAR {nombre}", key=f"btn_{nombre}"):
                    st.session_state.seleccionado = nombre

        if 'seleccionado' in st.session_state:
            st.divider()
            st.subheader(f"Confirmar Reserva: {st.session_state.seleccionado}")
            dias = st.number_input("Días de alquiler", min_value=1, value=1)
            total = dias * FLOTA[st.session_state.seleccionado]['precio']
            
            st.markdown(f"### TOTAL A PAGAR: R$ {total}")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PIX-24510861818")
            st.write("🏦 **Datos PIX:** Marina Baez | Banco Santander | Llave: 24510861818")
            
            # Botón WhatsApp
            wa_link = f"https://wa.me/595991681191?text=Hola%20JM%20Asociados,%20envío%20comprobante%20por%20{st.session_state.seleccionado}"
            st.markdown(f'[@Enviar Comprobante WhatsApp]({wa_link})')
            
            if st.button("CONFIRMAR PAGO Y GENERAR CONTRATO"):
                datos_reserva = {"nombre": "Cliente J&M", "auto": st.session_state.seleccionado, "dias": dias, "total": total}
                st.session_state.reservas.append(datos_reserva)
                pdf_bytes = generar_contrato(datos_reserva)
                st.download_button("📥 DESCARGAR CONTRATO PDF", pdf_bytes, "Contrato_JM.pdf")

    # PESTAÑA 2: HISTORIAL
    with pestanas[1]:
        st.header("Mis Transacciones")
        if st.session_state.reservas:
            df = pd.DataFrame(st.session_state.reservas)
            st.table(df)
        else:
            st.info("No tienes alquileres registrados aún.")

    # PESTAÑA 3: UBICACIÓN
    with pestanas[2]:
        st.subheader("📍 Central de Operaciones - JM Asociados")
        st.markdown("""
        **Dirección:** Ciudad del Este, Alto Paraná, Paraguay.  
        **WhatsApp Business:** 0991 681 191  
        **Instagram:** @jm_asociados_consultoria  
        **Correo:** jymasociados@gmail.com
        """)
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57613.43469176317!2d-54.654876!3d-25.512613!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68537c35f29db%3A0x6b69b597148a071d!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

    # PESTAÑA 4: PANEL ADMIN
    with pestanas[3]:
        st.header("🛡️ Auditoría y Finanzas")
        if st.session_state.reservas:
            df_admin = pd.DataFrame(st.session_state.reservas)
            st.metric("Ingresos Totales", f"R$ {df_admin['total'].sum()}")
            fig = px.pie(df_admin, names='auto', values='total', title="Rentabilidad por Vehículo")
            st.plotly_chart(fig)
            
            csv = df_admin.to_csv(index=False).encode('utf-8')
            st.download_button("📊 EXPORTAR EXCEL DE SERVICIOS", csv, "Finanzas_JM.csv")
        else:
            st.warning("Sin datos financieros para mostrar.")

# --- 5. EJECUCIÓN ---
pantalla_principal()
