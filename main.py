import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from fpdf import FPDF
import urllib.parse
import requests
import io

# --- 1. CONFIGURACIÓN E INTERFAZ DUAL ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA PROFESIONAL", layout="wide")

# Persistencia de sesión
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'role' not in st.session_state: st.session_state.role = "user"
if 'vista' not in st.session_state: st.session_state.vista = "login"

# CSS para Adaptación Móvil/PC y Estética Corporativa
st.markdown("""
<style>
    .stApp { background-color: #4A0404; color: white; }
    .card-auto {
        background-color: white; color: black; padding: 20px;
        border-radius: 15px; border: 4px solid #D4AF37; margin-bottom: 20px;
        display: flex; align-items: center; gap: 20px;
    }
    .btn-wa { 
        background-color: #25D366; color: white !important; padding: 12px; 
        border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px;
    }
    .btn-insta {
        background: linear-gradient(45deg, #f09433, #dc2743, #bc1888);
        color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold;
    }
    @media (max-width: 800px) {
        .card-auto { flex-direction: column !important; text-align: center; }
        .card-auto img { width: 100% !important; }
        .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 10px 5px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA ---
def init_db():
    conn = sqlite3.connect('jm_master.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, 
                  chasis TEXT, chapa TEXT, color TEXT, año TEXT)''')
    
    autos_data = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?)", autos_data)
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, total REAL, tipo TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (cliente TEXT, estrellas INTEGER, comentario TEXT, fecha DATE)')
    conn.commit()
    conn.close()

def get_fechas_bloqueadas(auto):
    conn = sqlite3.connect('jm_master.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = []
    for _, row in df.iterrows():
        d_ini = datetime.strptime(row['inicio'], '%Y-%m-%d').date()
        d_fin = datetime.strptime(row['fin'], '%Y-%m-%d').date()
        while d_ini <= d_fin:
            bloqueadas.append(d_ini)
            d_ini += timedelta(days=1)
    return bloqueadas

def get_cotizacion():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/BRL").json()
        return res['rates']['PYG']
    except: return 1450.0

init_db()
cot_pyg = get_cotizacion()

# --- 3. CONTRATO PDF (12 CLÁUSULAS) ---
def crear_pdf(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE LOCACIÓN - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    
    clausulas = [
        f"1. OBJETO: Arrendamiento del vehículo {d['auto']} con Chapa {d['chapa']} y Chasis {d['chasis']}.",
        f"2. PLAZO: Desde {d['inicio']} hasta {d['fin']}.",
        f"3. PRECIO: R$ {d['total']} (Equivalente a Gs. {d['total']*cot_pyg:,.0f} aprox).",
        "4. GARANTÍA: El cliente deposita una fianza por daños eventuales.",
        "5. SEGURO: Cobertura de responsabilidad civil incluida.",
        "6. COMBUSTIBLE: Retorno con el mismo nivel de entrega.",
        "7. MULTAS: Responsabilidad absoluta del locatario.",
        "8. MANTENIMIENTO: Prohibido reparaciones ajenas sin permiso.",
        "9. TERRITORIO: Uso exclusivo en Paraguay (salvo Carta Verde).",
        "10. DAÑOS: Responsabilidad por daños mecánicos por mal uso.",
        "11. LIMPIEZA: Cargo adicional si el vehículo vuelve sucio.",
        "12. JURISDICCIÓN: Tribunales de Ciudad del Este."
    ]
    for c in clausulas:
        pdf.multi_cell(0, 7, c)
        pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. FLUJO DE PANTALLAS ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.session_state.vista == "login":
            u = st.text_input("Usuario / Teléfono")
            p = st.text_input("Contraseña", type="password")
            if st.button("INGRESAR"):
                if u == "admin" and p == "8899": st.session_state.role = "admin"
                st.session_state.autenticado = True; st.session_state.user_name = u; st.rerun()
            if st.button("Crear Cuenta"): st.session_state.vista = "registro"; st.rerun()
            st.button("Olvidé mi contraseña"
