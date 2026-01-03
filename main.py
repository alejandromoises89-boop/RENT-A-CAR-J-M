import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="J&M ASOCIADOS | SISTEMA", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 20px; border: 2px solid #D4AF37; margin-bottom: 20px; }
        .status-badge { padding: 5px 15px; border-radius: 10px; font-weight: bold; }
        .disponible { background-color: #2ecc71; color: white; }
        .ocupado { background-color: #e74c3c; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS (PROTECCIÓN DE CRUCE) ---
def init_db():
    conn = sqlite3.connect('jm_asociados_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT, documento TEXT, doc_tipo TEXT, 
        correo TEXT UNIQUE, telefono TEXT, direccion TEXT, password TEXT, tipo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_brl REAL, 
        fecha TEXT, estado_pago TEXT)''')
    try:
        c.execute("INSERT INTO usuarios (nombre, correo, password, tipo) VALUES (?,?,?,?)", 
                  ("ADMIN MASTER", "admin@jymasociados.com", "JM2026_MASTER", "admin"))
    except: pass
    conn.commit()
    conn.close()

def verificar_disponibilidad(auto_nombre, fecha_consulta):
    conn = sqlite3.connect('jm_asociados_v4.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservas WHERE auto=? AND fecha=?", (auto_nombre, fecha_consulta))
    existe = c.fetchone()
    conn.close()
    return existe is None # True si está libre

init_db()

# --- 3. LOGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. ACCESO ---
if not st.session_state.logged_in:
    st.title("J&M ASOCIADOS")
    op = st.radio("Acceso:", ["Ingresar", "Registrarse"], horizontal=True)
    if op == "Ingresar":
        u = st.text_input("Correo")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            conn = sqlite3.connect('jm_asociados_v4.db')
            c = conn.cursor()
            c.execute("SELECT nombre, tipo FROM usuarios WHERE correo=? AND password=?", (u, p))
            data = c.fetchone()
            if data:
                st.session_state.logged_in, st.session_state.user_name, st.session_state.role = True, data[0], data[1]
                st.rerun()
            else: st.error("Datos incorrectos")
    else:
        with st.form("reg"):
            n = st.text_input("Nombre Completo")
            e = st.text_input("Email")
            dt = st.selectbox("Documento", ["CI", "CPF", "RG", "Pasaporte"])
            dn = st.text_input("Nro Documento")
            tl = st.text_input("Teléfono")
            dr = st.text_input("Dirección")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("REGISTRAR"):
                conn = sqlite3.connect('jm_asociados_v4.db')
                conn.cursor().execute("INSERT INTO usuarios (nombre, documento, doc_tipo, correo, telefono, direccion, password, tipo) VALUES (?,?,?,?,?,?,?,?)", (n, dn, dt, e, tl, dr, pw, "user"))
                conn.commit()
                st.success("Registrado.")

# --- 5. PORTAL CON BLOQUEO DE FECHAS ---
else:
    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    tabs = st.tabs(["🚗 Flota", "📊 Panel Control"] if st.session_state.role == "admin" else ["🚗 Alquiler", "📅 Mis Reservas"])

    with tabs[0]:
        st.subheader("Disponibilidad para hoy: " + datetime.now().strftime("%d/%m/%Y"))
        flota = [
            {"n": "Toyota Vitz Negro", "p": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson Blanco", "p": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Toyota Voxy Gris", "p": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
        ]
        
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        
        for a in flota:
            libre = verificar_disponibilidad(a['n'], fecha_hoy)
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                c1.image(a['img'])
                with c2:
                    st.subheader(a['n'])
                    if libre:
                        st.markdown('<span class="status-badge disponible">🟢 DISPONIBLE</span>', unsafe_allow_html=True)
                        st.write(f"Tarifa: {a['p']} BRL")
                        if st.button(f"Reservar Ahora", key=f"res_{a['n']}"):
                            conn = sqlite3.connect('jm_asociados_v4.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_brl, fecha, estado_pago) VALUES (?,?,?,?,?)",
                                                 (st.session_state.user_name, a['n'], a['p'], fecha_hoy, "Pendiente"))
                            conn.commit()
                            st.success("¡Reservado!")
                            st.rerun()
                    else:
                        st.
