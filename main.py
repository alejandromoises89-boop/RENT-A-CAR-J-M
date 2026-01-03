import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
import requests
from datetime import datetime
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

# Cargar Iconos de Google y Font Awesome
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

def obtener_cotizacion_brl():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/BRL"
        response = requests.get(url)
        return round(response.json()['rates']['PYG'])
    except:
        return 1450 

cotizacion_hoy = obtener_cotizacion_brl()

st.markdown(f"""
<style>
    .stApp {{ background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }}
    .header-jm {{ text-align: center; color: #D4AF37; margin-bottom: 20px; }}
    .card-auto {{ background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; }}
    
    /* Botones Estilo App */
    .btn-notif {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 15px;
        border-radius: 12px;
        text-decoration: none !important;
        font-weight: bold;
        font-size: 16px;
        margin-top: 10px;
        width: 100%;
        transition: 0.3s ease;
        border: none;
    }}
    .btn-whatsapp {{ background-color: #25D366; color: white !important; box-shadow: 0 4px #128C7E; }}
    .btn-email {{ background-color: #D4AF37; color: black !important; box-shadow: 0 4px #b08d2c; }}
    .btn-notif:active {{ transform: translateY(4px); box-shadow: none; }}
    .btn-icon {{ margin-right: 12px; font-size: 24px; vertical-align: middle; }}
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL)''')
    conn.commit()
    conn.close()

# --- 3. FLOTA VERIFICADA (Nombres, Colores y Links) ---
flota = [
    {
        "nombre": "Hyundai Tucson", 
        "color": "Blanco", 
        "precio_brl": 260, 
        "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"
    },
    {
        "nombre": "Toyota Vitz", 
        "color": "Blanco", 
        "precio_brl": 195, 
        "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"
    },
    {
        "nombre": "Toyota Vitz", 
        "color": "Negro", 
        "precio_brl": 195, 
        "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"
    },
    {
        "nombre": "Toyota Voxy", 
        "color": "Gris", 
        "precio_brl": 240, 
        "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"
    }
]

# --- 4. INTERFAZ ---
init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M ASOCIADOS</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Correo o Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", u
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    st.success(f"📈 Cotización Real hoy: {cotizacion_hoy:,} PYG")
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "⚙️ Panel Master"])

    with tabs[0]:
        for auto in flota:
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            st.markdown(f'<div class="card-auto">', unsafe_allow_html=True)
            c1, c2
