import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILOS AVANZADOS ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

# CSS personalizado para Fondos Negros y Bordes Dorados
st.markdown("""
<style>
    .stApp { background-color: #4A0404; color: #D4AF37; }
    h1, h2, h3, p, label { color: #D4AF37 !important; font-weight: bold; }
    
    /* Cuadros de texto en Negro con borde Dorado */
    input, textarea, [data-baseweb="select"] {
        background-color: black !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
    }
    
    .stButton>button {
        background-color: #D4AF37 !important;
        color: black !important;
        font-weight: bold;
        width: 100%;
        border-radius: 10px;
    }
    
    .card-auto {
        background-color: black;
        padding: 20px;
        border: 3px solid #D4AF37;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    
    .btn-wa { background-color: #25D366 !important; color: white !important; padding: 10px; border-radius: 8px; text-align: center; display: block; text-decoration: none; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCIA DE SESIÓN ---
if 'logueado' not in st.session_state:
    st.session_state.logueado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = "user"

# --- 3. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_final.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, chapa TEXT, chasis TEXT, precio REAL, img TEXT)')
    
    autos = [
        ("Hyundai Tucson", "AA-123", "TUC-7721", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"),
        ("Toyota Vitz Blanco", "BCC-445", "VTZ-001", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png"),
        ("Toyota Vitz Negro", "XAM-990", "VTZ-998", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"),
        ("Toyota Voxy", "HHP-112", "VOX-556", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 4. GENERADOR DE CONTRATO ---
def generar_contrato_pdf(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO JM ASOCIADOS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    texto = f"""CONTRATO DE ALQUILER PROFESIONAL
    Cliente: {d['cliente']}
    Vehículo: {d['auto']} | Chapa: {d['chapa']} | Chasis: {d['chasis']}
    Periodo: {d['inicio']} al {d['fin']}
    Total: R$ {d['total']}
    
    CLAUSULAS:
    1. Responsabilidad civil total del arrendatario.
    2. Prohibido el uso fuera del territorio nacional sin permiso.
    3. Multas y sanciones a cargo del cliente.
    ... (Cláusulas legales de JM Asociados) ...
    
    FIRMA DIGITAL REGISTRADA: {d['firma']}
    """
    pdf.multi_cell(0, 10, texto)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. LOGICA DE ACCESO ---
if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>Acceso JM</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size:80px;'>🔒</h1>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    user = col_l.text_input("Usuario")
    pw = col_r.text_input("Contraseña", type="password")
    
    if st.button("INGRESAR"):
        if user == "admin" and pw == "8899":
            st.session_state.perfil = "admin"
        st.session_state.logueado = True
        st.session_state.u_name = user
        st.rerun()
    
    st.button("Crear cuenta y Guardar")
    st.button("Olvidé mi contraseña")
    st.button("Acceso con Biometría (Huella/Rostro)")

# --- 6. APP PRINCIPAL ---
else:
    st.markdown("<h2 style='text-align:center;'>JM ALQUILER DE VEHICULOS</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("Cerrar Sesión 🚪"):
        st.session_state.logueado = False
        st.rerun()

    menu = st.tabs(["🚗 Vehículos", "📍 Ubicación", "🛡️ Panel Máster"])

    # --- TAB VEHICULOS ---
    with menu[0]:
        conn = sqlite3.connect('jm_final_final.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:300px; border-radius:10px;">
                    <h3>{a['nombre']}</h3>
                    <p>Chapa: {a['chapa']} | Precio: R$ {a['precio']}</p>
                </div>''', unsafe_allow_html=True)
                
                with st.expander("📝 Reservar ahora"):
                    st.write("✒️ **FIRMA DIGITAL**")
                    firma_input = st.text_input("Escriba su nombre completo como firma", key=f"f_{a['nombre']}")
                    
                    c1, c2 = st.columns(2)
                    d_i = c1.date_input("Recogida", date.today(), key=f"di_{a['nombre']}")
                    d_f = c2.date_input("Devolución", d_i + timedelta(days=1), key=f"df_{a['nombre']}")
                    
                    total_p = (d_f - d_i).days * a['precio']
                    st.markdown(f"### Total: R$ {total_p}")
                    st.info("🏦 **PAGO PIX:** Chave: JMASOCIADOS2026")
                    
                    if st.button("Confirmar y Pagar", key=f"btn_{a['nombre']}"):
                        if not firma_input:
                            st.error("Debe firmar para continuar")
                        else:
                            # Guardar Reserva
                            conn = sqlite3.connect('jm_final_final.db')
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)",
                                         (st.session_state.u_name, a['nombre'], d_i, d_f, total_p))
                            conn.commit(); conn.close()
                            
                            st.success("✅ ¡Reserva Exitosa!")
                            
                            # Generar Contrato
                            datos_pdf = {'cliente': st.session_state.u_name, 'auto': a['nombre'], 'chapa': a['chapa'], 
                                         'chasis': a['chasis'], 'inicio': d_i, 'fin': d_f, 'total': total_p, 'firma': firma_input}
                            pdf_file = generar_contrato_pdf(datos_pdf)
                            
                            # Botones Finales
                            st.download_button("📥 DESCARGAR CONTRATO FIRMADO", pdf_file, f"Contrato_JM_{a['nombre']}.pdf")
                            
                            wa_msg = f"Hola JM! Soy {st.session_state.u_name}, envío comprobante del {a['nombre']} por R$ {total_p}."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(wa_msg)}" class="btn-wa">📤 ENVIAR COMPROBANTE WHATSAPP</a>', unsafe_allow_html=True)

    # --- TAB UBICACIÓN ---
    with menu[1]:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.234567!2d-54.612345!3d-25.512345!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ0LjQiUyA1NMKwMzYnNDQuNCJX!5e0!3m2!1ses!2spy!4v1620000000000" width="100%" height="400" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown('<br><a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" style="color:#D4AF37; font-size:20px; text-decoration:none;">📸 Visita nuestro Instagram</a>', unsafe_allow_html=True)

    # --- TAB PANEL MÁSTER ---
    with menu[2]:
        if st.session_state.perfil == "admin":
            st.subheader("📊 Finanzas e Ingresos")
            conn = sqlite3.connect('jm_final_final.db')
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            st.metric("TOTAL INGRESOS", f"R$ {res['total'].sum():,.2f}")
            fig = px.bar(res, x="auto", y="total", color="auto", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.subheader("🗑️ Limpiar Historial")
            pin_check = st.text_input("Ingrese PIN Maestro para borrar todo", type="password")
            if st.button("BORRAR REGISTROS"):
                if pin_check == "0000":
                    conn.execute("DELETE FROM reservas")
                    conn.commit()
                    st.success("Historial borrado.")
                    st.rerun()
                else:
                    st.error("PIN Incorrecto.")
            conn.close()
        else:
            st.warning("Área exclusiva para Administradores.")
