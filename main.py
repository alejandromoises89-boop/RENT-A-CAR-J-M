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
        .header-jm { text-align: center; color: #D4AF37; font-size: 3.5rem; font-weight: bold; margin-bottom: 0px; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 30px; letter-spacing: 2px; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .btn-notif { display: flex; align-items: center; justify-content: center; padding: 10px; border-radius: 10px; text-decoration: none !important; font-weight: bold; margin-top: 10px; color: white !important; }
        .btn-whatsapp { background-color: #25D366; }
        .btn-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_brl REAL, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, usuario TEXT UNIQUE, password TEXT, tipo TEXT)')
    try:
        c.execute("INSERT INTO usuarios (nombre, usuario, password, tipo) VALUES (?,?,?,?)", 
                  ("ADMIN MASTER", "admin@jymasociados.com", "JM2026_MASTER", "admin"))
    except: pass
    conn.commit()
    conn.close()

def obtener_cotizacion():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        return round(r.json()['rates']['PYG'])
    except: return 1450

init_db()
cotizacion_hoy = obtener_cotizacion()

# --- 3. FLOTA ---
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
    st.toast("✨ Gracias por confiar en J&M. ¡Vuelva pronto!")
    time.sleep(1.5)
    st.session_state.logged_in = False
    st.session_state.user_name = None
    st.session_state.role = None
    st.rerun()

# --- 5. ACCESO (LOGIN / REGISTRO) ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">ASOCIADOS & CONSULTORES</div>', unsafe_allow_html=True)
    
    opcion = st.radio("Acceso al Portal:", ["Ingresar", "Registrarse"], horizontal=True)
    
    if opcion == "Ingresar":
        u = st.text_input("Usuario (Email)")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            conn = sqlite3.connect('jm_asociados.db')
            c = conn.cursor()
            c.execute("SELECT nombre, tipo FROM usuarios WHERE usuario=? AND password=?", (u, p))
            user_data = c.fetchone()
            conn.close()
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_name = user_data[0]
                st.session_state.role = user_data[1]
                st.rerun()
            else:
                st.error("❌ Datos incorrectos")
    else:
        new_name = st.text_input("Nombre Completo")
        new_user = st.text_input("Nuevo Usuario (Email)")
        new_pass = st.text_input("Contraseña", type="password")
        if st.button("CREAR CUENTA"):
            if new_name and new_user and new_pass:
                try:
                    conn = sqlite3.connect('jm_asociados.db')
                    conn.cursor().execute("INSERT INTO usuarios (nombre, usuario, password, tipo) VALUES (?,?,?,?)", 
                                         (new_name, new_user, new_pass, "user"))
                    conn.commit()
                    conn.close()
                    st.success("✅ Cuenta creada. Ya puede Ingresar.")
                except: st.error("❌ El usuario ya existe.")
            else: st.warning("⚠️ Complete todos los campos.")

# --- 6. PORTAL ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        logout()

    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">Alquiler de Vehículos</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Ubicación", "⭐ Reseñas", "⚙️ Panel Master"] if st.session_state.role == "admin" else ["🚗 Catálogo", "📅 Mis Alquileres", "📍 Ubicación", "⭐ Reseñas"])

    with tabs[0]:
        st.write(f"Cotización actual: **1 BRL = {cotizacion_hoy:,} PYG**")
        for idx, auto in enumerate(flota):
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1: st.image(auto['img'], use_container_width=True)
                with c2:
                    st.subheader(f"{auto['nombre']} {auto['color']}")
                    st.write(f"Tarifa: **{auto['precio_brl']} BRL** (Gs. {monto_pyg:,})")
                    if st.button("Reservar Ahora", key=f"res_{idx}"):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_brl, fecha) VALUES (?,?,?,?)",
                                             (st.session_state.user_name, auto['nombre'], auto['precio_brl'], datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success("✅ Reserva registrada. Pague vía PIX para confirmar.")
                        st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=24510861818")
                st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Mis Alquileres Registrados")
        conn = sqlite3.connect('jm_asociados.db')
        df_h = pd.read_sql_query(f"SELECT auto, monto_brl, fecha FROM reservas WHERE cliente = '{st.session_state.user_name}'", conn)
        st.dataframe(df_h, use_container_width=True)
        conn.close()

    with tabs[2]:
        st.markdown("### 📍 Edificio Aramí")
        st.write("Farid Rahal y Curupayty, Ciudad del Este")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.627727142!2d-54.611111!3d-25.511111!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQwLjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1620000000000!5m2!1ses!2spy" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        st.markdown(f'''
            <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank" class="btn-notif btn-instagram">Ver Instagram</a>
            <a href="https://wa.me/595991681191" target="_blank" class="btn-notif btn-whatsapp">WhatsApp Oficial</a>
        ''', unsafe_allow_html=True)

    with tabs[3]:
        with st.form("res_f"):
            com = st
