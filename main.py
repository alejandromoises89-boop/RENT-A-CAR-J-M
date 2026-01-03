import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | SISTEMA", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 3.2rem; font-weight: bold; margin-bottom: 0px; }
        .sub-header { text-align: center; color: white; font-size: 1.1rem; margin-bottom: 25px; letter-spacing: 1px; }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 20px; border: 2px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.4); }
        .btn-pago { display: flex; align-items: center; justify-content: center; padding: 12px; border-radius: 10px; text-decoration: none !important; font-weight: bold; margin-top: 10px; color: white !important; }
        .btn-wa { background-color: #25D366; }
        .btn-ins { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #bc1888); }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados_v3.db')
    c = conn.cursor()
    # Tabla de Usuarios con KYC completo
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT, documento TEXT, doc_tipo TEXT, 
        correo TEXT UNIQUE, telefono TEXT, direccion TEXT, password TEXT, tipo TEXT)''')
    # Tabla de Reservas
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_brl REAL, 
        fecha TEXT, estado_pago TEXT)''')
    # Admin por defecto
    try:
        c.execute("INSERT INTO usuarios (nombre, correo, password, tipo) VALUES (?,?,?,?)", 
                  ("ADMIN MASTER", "admin@jymasociados.com", "JM2026_MASTER", "admin"))
    except: pass
    conn.commit()
    conn.close()

init_db()

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

def logout():
    st.toast("✅ Gracias por confiar en J&M ASOCIADOS. ¡Vuelva pronto!")
    time.sleep(2)
    st.session_state.logged_in = False
    st.rerun()

# --- 4. ACCESO Y REGISTRO ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M ASOCIADOS</div><div class="sub-header">CONSULTORÍA & ALQUILER</div>', unsafe_allow_html=True)
    tab_acc = st.tabs(["🔑 Ingresar", "📝 Registro Cliente Nuevo"])
    
    with tab_acc[0]:
        u = st.text_input("Correo")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            conn = sqlite3.connect('jm_asociados_v3.db')
            c = conn.cursor()
            c.execute("SELECT nombre, tipo FROM usuarios WHERE correo=? AND password=?", (u, p))
            data = c.fetchone()
            if data:
                st.session_state.logged_in, st.session_state.user_name, st.session_state.role = True, data[0], data[1]
                st.rerun()
            else: st.error("Error de acceso")
            conn.close()

    with tab_acc[1]:
        with st.form("reg"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nombre y Apellido")
            e = c2.text_input("Email")
            dt = c1.selectbox("Documento", ["CI", "CPF", "RG", "Pasaporte", "DNI"])
            dn = c2.text_input("Nro Documento")
            tl = c1.text_input("Teléfono / Celular")
            dr = c2.text_input("Dirección Completa")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("REGISTRARME"):
                try:
                    conn = sqlite3.connect('jm_asociados_v3.db')
                    conn.cursor().execute("INSERT INTO usuarios (nombre, documento, doc_tipo, correo, telefono, direccion, password, tipo) VALUES (?,?,?,?,?,?,?,?)",
                                         (n, dn, dt, e, tl, dr, pw, "user"))
                    conn.commit()
                    st.success("¡Registro Exitoso!")
                except: st.error("Email ya registrado")

# --- 5. INTERFAZ LOGUEADA ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
    if st.sidebar.button("🚪 CERRAR SESIÓN"): logout()

    # PESTAÑAS (CORRECCIÓN DE LA LÍNEA 101)
    if st.session_state.role == "admin":
        tabs = st.tabs(["🚗 Catálogo", "📍 Ubicación", "⭐ Reseñas", "📈 Panel Master"])
    else:
        tabs = st.tabs(["🚗 Catálogo", "💰 Mis Pagos", "📍 Ubicación", "⭐ Reseñas"])

    with tabs[0]:
        st.subheader("Nuestra Flota")
        autos = [
            {"n": "Toyota Vitz", "p": 195, "img": "
