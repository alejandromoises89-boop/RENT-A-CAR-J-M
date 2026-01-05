import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA TOTAL", layout="wide")

# CSS OPTIMIZADO PARA MÓVILES (Responsivo)
st.markdown("""
<style>
    .stApp { background-color: #4A0404; color: white; }
    .card-auto {
        background-color: white; color: black; padding: 15px;
        border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 20px;
    }
    /* Arreglo para que el panel administrativo sea visible en móviles */
    [data-testid="stVerticalBlock"] > div:has(div.stTabs) { width: 100%; }
    .btn-wa { background-color: #25D366; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    iframe { border-radius: 15px; border: 2px solid #D4AF37; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE SESIÓN (MANTENER LOGUEADO) ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = "user"

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_rent_pro_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, año TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, h_entrega TEXT, h_devolucion TEXT, total REAL, tipo TEXT)''')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ASOCIADOS | LOGIN</h1>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuario")
        p = st.text_input("Password", type="password")
        if st.button("ENTRAR"):
            if u == "admin" and p == "8899":
                st.session_state.role = "admin"
                st.session_state.autenticado = True
                st.session_state.user = "Administrador"
            else:
                st.session_state.autenticado = True
                st.session_state.user = u
            st.rerun()
else:
    # --- APP PRINCIPAL ---
    st.sidebar.write(f"Sesión: {st.session_state.user}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False; st.rerun()

    menu = ["🚗 Flota y Alquiler", "📍 Ubicación", "🛡️ Panel Máster"]
    tab = st.tabs(menu)

    # --- TAB 1: FLOTA ---
    with tab[0]:
        conn = sqlite3.connect('jm_rent_pro_v2.db')
        df_f = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, a in df_f.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:300px; border-radius:10px;">
                    <h2 style="color:#4A0404;">{a['nombre']}</h2>
                    <p style="color:gray;">{a['color']} | Chapa: {a['chapa']} | Año: {a['año']}</p>
                    <h3 style="color:#D4AF37;">R$ {a['precio']} p/ día</h3>
                    <p><b>Estado: {a['estado']}</b></p>
                </div>''', unsafe_allow_html=True)
                
                if a['estado'] == "Disponible":
                    with st.expander("📝 Alquilar este vehículo"):
                        col1, col2 = st.columns(2)
                        f_i = col1.date_input("Fecha Entrega", key=f"fi{a['nombre']}")
                        h_i = col1.time_input("Hora Entrega", time(9, 0), key=f"hi{a['nombre']}")
                        f_f = col2.date_input("Fecha Devolución", f_i + timedelta(days=1), key=f"ff{a['nombre']}")
                        h_f = col2.time_input("Hora Devolución", time(9, 0), key=f"hf{a['nombre']}")
                        
                        st.write("---")
                        st.write("✒️ **Firma Digital (Escribe tu nombre completo como firma)**")
                        firma = st.text_input("Firma del cliente", key=f"sig{a['nombre']}")
                        
                        dias = (f_f - f_i).days
                        total = dias * a['precio']
                        st.subheader(f"Total: R
