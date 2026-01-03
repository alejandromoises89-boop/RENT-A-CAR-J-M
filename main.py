import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 3rem; font-weight: bold; margin-bottom: 0px; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 20px; letter-spacing: 2px; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .btn-notif { display: flex; align-items: center; justify-content: center; padding: 10px; border-radius: 10px; text-decoration: none !important; font-weight: bold; margin-top: 10px; color: white !important; }
        .btn-whatsapp { background-color: #25D366; }
        .btn-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y COTIZACIÓN ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_brl REAL, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    conn.commit()
    conn.close()

def obtener_cotizacion():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        return round(r.json()['rates']['PYG'])
    except: return 1450

init_db()
cotizacion_hoy = obtener_cotizacion()

# --- 3. FLOTA DE VEHÍCULOS ---
flota = [
    {"nombre": "Toyota Vitz", "color": "Negro", "precio_brl": 195, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio_brl": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio_brl": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio_brl": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

# --- 4. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def logout():
    st.toast("✨ Gracias por confiar en J&M Asesoría Contable. ¡Vuelva pronto!")
    time.sleep(2)
    st.session_state.logged_in = False
    st.rerun()

# --- 5. INTERFAZ ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">SISTEMA DE ALQUILER</div>', unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
            st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
        else:
            st.session_state.role, st.session_state.user_name = "user", u
        st.session_state.logged_in = True
        st.rerun()
else:
    # Barra Superior
    c_h1, c_h2 = st.columns([0.8, 0.2])
    with c_h1: st.write(f"👤 Usuario: **{st.session_state.user_name}**")
    with c_h2: 
        if st.button("🚪 Cerrar Sesión"): logout()

    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">Alquiler de Vehículos</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center; color:#D4AF37; font-weight:bold;">1 Real = {cotizacion_hoy:,} PYG</p>', unsafe_allow_html=True)

    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación & Redes", "⭐ Reseñas", "⚙️ Panel Master"] if st.session_state.role == "admin" else ["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación & Redes", "⭐ Reseñas"])

    # --- TAB 1: CATÁLOGO ---
    with tabs[0]:
        for idx, auto in enumerate(flota):
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                col_img, col_txt = st.columns([1, 2])
                with col_img: st.image(auto['img'], use_container_width=True)
                with col_txt:
                    st.subheader(f"{auto['nombre']} - {auto['color']}")
                    st.write(f"Tarifa Diaria: **{auto['precio_brl']} BRL** (Gs. {monto_pyg:,})")
                    if st.button("Confirmar Reserva", key=f"btn_{idx}"):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_brl, fecha) VALUES (?,?,?,?)",
                                             (st.session_state.user_name, auto['nombre'], auto['precio_brl'], datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success("✅ ¡Reserva registrada!")
                        st.write("Escanee el PIX para confirmar:")
                        st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=24510861818")
                st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: MI HISTORIAL ---
    with tabs[1]:
        st.subheader("Mi Historial de Alquiler")
        conn = sqlite3.connect('jm_asociados.db')
        df_h = pd.read_sql_query(f"SELECT auto, monto_brl, fecha FROM reservas WHERE cliente = '{st.session_state.user_name}'", conn)
        st.dataframe(df_h, use_container_width=True)
        conn.close()

    # --- TAB 3: UBICACIÓN ---
    with tabs[2]:
        c_m, c_i = st.columns([2, 1])
        with c_m:
            st.markdown("### 📍 Ubicación Exacta")
            st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d450.0!2d-54.6105!3d-25.5125!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ1LjAiUyA1NMKwMzYnMzcuOCJX!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        with c_i:
            st.write("**Edificio Aramí** (Frente Edif. España)")
            st.write("Farid Rahal y Curupayty, CDE")
            st.divider()
            st.markdown(f'''
                <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank" class="btn-notif btn-instagram"><i class="fab fa-instagram">
