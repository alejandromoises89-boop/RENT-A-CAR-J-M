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

    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Reserva", "📍
