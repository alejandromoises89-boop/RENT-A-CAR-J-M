import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO DEGRADADO PREMIUM ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        .stApp { 
            background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); 
            color: white; 
        }
        .header-jm { text-align: center; color: #D4AF37; font-size: 4.5rem; font-weight: bold; margin-bottom: 0px; text-shadow: 2px 2px 4px #000; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 40px; letter-spacing: 4px; font-weight: 300; }
        .card-auto { 
            background-color: white; 
            color: #1a1a1a; 
            padding: 25px; 
            border-radius: 15px; 
            border: 2px solid #D4AF37; 
            margin-bottom: 20px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); 
        }
        .review-card {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #D4AF37;
            margin-bottom: 10px;
        }
        .btn-wa-confirm { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px; }
        .price-tag { color: #b02121; font-size: 1.4rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, monto_egreso REAL, inicio TEXT, fin TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)''')
    conn.commit()
    conn.close()

def verificar_bloqueo(auto, inicio, fin):
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM reservas WHERE auto=? AND (inicio <= ? AND fin >= ?)''', (auto, fin.strftime("%Y-%m-%d"), inicio.strftime("%Y-%m-%d")))
    resultado = c.fetchone()
    conn.close()
    return resultado is None

init_db()

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. ACCESO (LOGIN/REGISTRO) ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        op = st.radio("Acceso al Portal", ["Ingresar", "Registrarse"], horizontal=True)
        if op == "Ingresar":
            u = st.text_input("Usuario (Email)")
            p = st.text_input("Clave", type="password")
            if st.button("ENTRAR"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (u, p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in, st.session_state.user_name = True, user[0]
                    st.rerun()
                else: st.error("❌ Credenciales inválidas")
        else:
            with st.form("reg"):
                n = st.text_input("Nombre Completo")
                e = st.text_input("Correo")
                t = st.text_input("WhatsApp")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("REGISTRARSE"):
                    try:
                        conn = sqlite3.connect('jm_final_safe.db')
                        conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, tel) VALUES (?,?,?,?)", (n, e, p, t))
                        conn.commit()
                        st.success("¡Registro exitoso! Ya puede ingresar.")
                    except: st.error("El correo ya existe.")

# --- 5. PORTAL JM ---
else:
    st.markdown(f'<h3 style="text-align:center; color:#D4AF37;">Bienvenido, {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Alquiler de Flota", "📅 Mi Historial", "📍 Ubicación", "⭐ Reseñas", "⚙️ Panel Master"])

    # --- PESTAÑA 1: ALQUILER (FLOTA ORDENADA) ---
    with tabs[0]:
        st.subheader("Seleccione sus fechas de reserva")
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde", min_value=datetime.now().date())
        f_fin = c_f2.date_input("Hasta", min_value=
