import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import requests

# --- 1. CONFIGURACIÓN INICIAL Y PERSISTENCIA ---
st.set_page_config(page_title="JM ALQUILER DE VEHICULOS", layout="wide")

# Inicialización de estados para que no se borren al actualizar
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"

# --- 2. BASE DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('jm_final_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (user TEXT PRIMARY KEY, password TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, año TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, h_entrega TEXT, h_devolucion TEXT, total REAL)''')
    
    # Datos de los autos
    autos_iniciales = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?)", autos_iniciales)
    conn.commit()
    conn.close()

init_db()

# --- 3. LÓGICA DE BLOQUEO DE FECHAS ---
def obtener_fechas_bloqueadas(auto_nombre):
    conn = sqlite3.connect('jm_final_v3.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto_nombre,))
    conn.close()
    bloqueadas = []
    for _, row in df.iterrows():
        inicio = datetime.strptime(row['inicio'], '%Y-%m-%d').date()
        fin = datetime.strptime(row['fin'], '%Y-%m-%d').date()
        while inicio <= fin:
            bloqueadas.append(inicio)
            inicio += timedelta(days=1)
    return bloqueadas

# --- 4. GENERADOR DE CONTRATO (12 CLÁUSULAS) ---
def crear_pdf_contrato(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Yo, {d['cliente']}, alquilo el {d['auto']} (Chapa: {d['chapa']}) desde {d['inicio']} hasta {d['fin']}.")
    
    clausulas = [
        "1. Uso exclusivo en territorio nacional.", "2. Prohibido subarrendar.", "3. Seguro contra terceros incluido.",
        "4. Depósito de garantía obligatorio.", "5. Combustible al mismo nivel.", "6. Responsabilidad civil del cliente.",
        "7. Multas a cargo del cliente.", "8. Prohibido reparaciones sin aviso.", "9. Retorno puntual o multa.",
        "10. Limpieza obligatoria.", "11. Jurisdicción en Ciudad del Este.", "12. Firma digital válida."
    ]
    for c in clausulas:
        pdf.cell(0, 7, c, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. ESTILOS CSS ---
st.markdown("""
<style>
    .stApp { background-color: #4A0404; color: white; }
    .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 20px; }
    .btn-custom { display: block; width: 100%; padding: 15px; margin: 10px 0; text-align: center; border-radius: 10px; font-weight: bold; text-decoration: none; color: white !important; }
    .btn-wa { background-color: #25D366; }
    .btn-ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); }
    .footer-jm { text-align: center; padding: 20px; color: #D4AF37; }
</style>
""", unsafe_allow_html=True)

# --- 6. INTERFAZ DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>Acceso JM</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size: 100px;'>🔒</h1>", unsafe_allow_html=True)
    
    tab_log, tab_reg = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
    
    with tab_log:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        col_log1, col_log2 = st.columns(2)
        if col_log1.button("INGRESAR"):
            if u == "admin" and p == "8899":
                st.session_state.role = "admin"
                st.session_state.autenticado = True
                st.session_state.user = "Admin JM"
                st.rerun()
            else:
                st.session_state.autenticado = True
                st.session_state.user = u
                st.rerun()
        if col_log2.button("Inicia con Biometría"):
            st.info("Sensor biométrico no detectado. Use contraseña.")
        st.button("Olvidé mi contraseña")

    with tab_reg:
        new_u = st.text_input("Nuevo Usuario")
        new_p = st.text_input("Nueva Contraseña", type="password")
        if st.button("Guardar y Crear"):
            st.success("Cuenta creada. Ahora inicie sesión.")

else:
    # --- APP PRINCIPAL ---
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
    
    if st.sidebar.button("Cerrar Sesión 🚪"):
        st.session_state.autenticado = False
        st.rerun()

    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Reserva", "📍 Ubicación y Contacto", "🛡️ Panel Máster"])

    # TAB CATALOGO
    with tabs[0]:
        conn = sqlite3.connect('jm_final_v3.db')
        flota = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, a in flota.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:300px; border-radius:10px;">
                    <h3>{a['nombre']}</h3>
                    <p>{a['color']} | {a['año']} | Chapa: {a['chapa']}</p>
                    <h3 style="color:#D4AF37;">R$ {a['precio']} / día</h3>
                    <p><b>Estado: {a['estado']}</b></p>
                </div>''', unsafe_allow_html=True)
                
                bloq = obtener_fechas_bloqueadas(a['nombre'])
                
                if a['estado'] == "Disponible":
                    with st.expander(f"Alquilar {a['nombre']}"):
                        f_ini = st.date_input("Fecha Inicio", date.today(), key=f"i{a['nombre']}")
                        f_fin = st.date_input("Fecha Devolución", f_ini + timedelta(days=1), key=f"f{a['nombre']}")
                        
                        if f_ini in bloq or f_fin in bloq:
                            st.error("⚠️ Fechas no disponibles para este vehículo.")
                        else:
                            h_e = st.time_input("Hora Entrega", time(9,0), key=f"he{a['nombre']}")
                            h_d = st.time_input("Hora Devolución", time(9,0), key=f"hd{a['nombre']}")
                            total = (f_fin - f_ini).days * a['precio']
                            
                            st.info(f"🏦 **DATOS PIX PARA PAGO:**\n\nChave PIX: **JMASOCIADOS2026**\nBanco: JM Bank")
                            st.subheader(f"Total: R$ {total}")
                            
                            if st.button(f"Confirmar Reserva {a['nombre']}"):
                                conn = sqlite3.connect('jm_final_v3.db')
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, h_entrega, h_devolucion, total) VALUES (?,?,?,?,?,?,?)",
                                             (st.session_state.user, a['nombre'], f_ini, f_fin, str(h_e), str(h_d), total))
                                conn.commit(); conn.close()
                                st.success("¡Reserva confirmada!")
                                
                                # Botón Contrato
                                pdf = crear_pdf_contrato({'cliente':st.session_state.user, 'auto':a['nombre'], 'chapa':a['chapa'], 'inicio':f_ini, 'fin':f_fin, 'total':total})
                                st.download_button("📄 Descargar Contrato PDF", pdf, f"Contrato_{a['nombre']}.pdf")
                                
                                # WhatsApp
                                msg = f"Reserva JM: {a['nombre']}. Cliente: {st.session_state.user}. Total: R$ {total}"
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-custom btn-wa">Enviar Comprobante por WhatsApp</a>', unsafe_allow_html=True)

    # TAB UBICACION Y CONTACTO
    with tabs[2]:
        st.markdown("### 📍 Nuestra Ubicación")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.234567!2d-54.612345!3d-25.512345!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ0LjQiUyA1NMKwMzYnNDQuNCJX!5e0!3m2!1ses!2spy!4v1620000000000" width="100%" height="400" frameborder="0" style="border:0;" allowfullscreen></iframe>', unsafe_allow_html=True)
        
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-custom btn-wa">💬 WhatsApp Corporativo</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-custom btn-ig">📸 Nuestro Instagram</a>', unsafe_allow_html=True)

    # TAB PANEL MASTER (ADMIN)
    with tabs[3]:
        if st.session_state.role == "admin":
            st.title("🛡️ Panel Administrativo")
            conn = sqlite3.connect('jm_final_v3.db')
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            # Finanzas
            st.metric("INGRESOS TOTALES", f"R$ {df_res['total'].sum():,}")
            fig = px.bar(df_res, x="auto", y="total", title="Ingresos por Vehículo")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_res, use_container_width=True)
            if st.button("LIMPIAR REGISTROS (PIN 0000)"):
                st.warning("Ingrese PIN para borrar")
            conn.close()
        else:
            st.warning("⚠️ Acceso denegado. Solo para administradores.")