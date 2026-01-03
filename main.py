import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="JM | Alquiler", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 5rem; font-weight: bold; margin-bottom: 0px; line-height: 1; }
        .sub-header { text-align: center; color: white; font-size: 1.5rem; margin-bottom: 30px; letter-spacing: 3px; }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 20px; border: 2px solid #D4AF37; margin-bottom: 20px; }
        .price-tag { font-size: 1.5rem; color: #4e0b0b; font-weight: bold; }
        div.stButton > button:first-child { width: 100%; border-radius: 10px; }
        .logout-container { display: flex; justify-content: center; margin-top: 50px; padding-bottom: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, tipo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_total REAL, fecha_inicio TEXT, fecha_fin TEXT)''')
    try:
        c.execute("INSERT INTO usuarios (nombre, correo, password, tipo) VALUES (?,?,?,?)", ("ADMIN MASTER", "admin@jymasociados.com", "JM2026_MASTER", "admin"))
    except: pass
    conn.commit()
    conn.close()

def verificar_rango_libre(auto, inicio, fin):
    conn = sqlite3.connect('jm_final_v2.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM reservas WHERE auto=? AND NOT (fecha_fin < ? OR fecha_inicio > ?)''', (auto, inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")))
    conflicto = c.fetchone()
    conn.close()
    return conflicto is None

init_db()

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LOGIN (JM - ALQUILER DE VEHICULOS) ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    
    col_acc1, col_acc2, col_acc3 = st.columns([1, 2, 1])
    with col_acc2:
        op = st.radio("Seleccione Acción:", ["Ingresar", "Registrarse"], horizontal=True)
        if op == "Ingresar":
            u = st.text_input("Correo")
            p = st.text_input("Contraseña", type="password")
            if st.button("ACCEDER"):
                conn = sqlite3.connect('jm_final_v2.db')
                c = conn.cursor()
                c.execute("SELECT nombre, tipo FROM usuarios WHERE correo=? AND password=?", (u, p))
                data = c.fetchone()
                if data:
                    st.session_state.logged_in, st.session_state.user_name, st.session_state.role = True, data[0], data[1]
                    st.rerun()
                else: st.error("Credenciales incorrectas")
        else:
            n = st.text_input("Nombre Completo")
            e = st.text_input("Correo")
            pw = st.text_input("Contraseña", type="password")
            if st.button("CREAR CUENTA"):
                conn = sqlite3.connect('jm_final_v2.db')
                conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, tipo) VALUES (?,?,?,?)", (n, e, pw, "user"))
                conn.commit()
                st.success("Cuenta creada. Ya puede ingresar.")

# --- 5. PORTAL DEL CLIENTE ---
else:
    st.markdown('<div class="header-jm" style="font-size:3rem;">JM</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;">Bienvenido, {st.session_state.user_name}</p>', unsafe_allow_html=True)

    tabs = st.tabs(["🚗 Vehículos", "📅 Mi Calendario", "📍 Ubicación", "⚙️ Panel Master"])

    with tabs[0]:
        st.subheader("Configura tu Reserva")
        col_f1, col_f2 = st.columns(2)
        d_inicio = col_f1.date_input("Retiro", min_value=datetime.now())
        d_fin = col_f2.date_input("Devolución", min_value=d_inicio + timedelta(days=1))
        dias = (d_fin - d_inicio).days
        
        flota = [
            {"n": "Toyota Vitz", "p": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson", "p": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Toyota Voxy", "p": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
        ]

        for a in flota:
            libre = verificar_rango_libre(a['n'], d_inicio, d_fin)
            total = a['p'] * dias
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                c1.image(a['img'])
                with c2:
                    st.subheader(a['n'])
                    if libre:
                        st.markdown(f'<p class="price-tag">Total por {dias} días: {total} BRL</p>', unsafe_allow_html=True)
                        if st.button(f"Confirmar Reserva {a['n']}", key=f"res_{a['n']}"):
                            conn = sqlite3.connect('jm_final_v2.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_total, fecha_inicio, fecha_fin) VALUES (?,?,?,?,?)",
                                                 (st.session_state.user_name, a['n'], total, d_inicio.strftime("%Y-%m-%d"), d_fin.strftime("%Y-%m-%d")))
                            conn.commit()
                            st.success(f"¡Reserva confirmada! Total: {total} BRL")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_JM_{total}")
                    else:
                        st.error("🔴 NO DISPONIBLE en el rango seleccionado.")
                st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        conn = sqlite3.connect('jm_final_v2.db')
        df = pd.read_sql_query("SELECT auto, fecha_inicio, fecha_fin FROM reservas", conn)
        st.dataframe(df, use_container_width=True)

    with tabs[2]:
        st.write("📍 C/Farid Rahal Canan, Curupayty, Cd. del Este")
        st.markdown('<iframe src="https://maps.google.com/?cid=3703490403065393590&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ5" width="100%" height="350" style="border-radius:15px;"></iframe>', unsafe_allow_html=True)

    with tabs[3]:
        pin = st.text_input("PIN de Seguridad Admin", type="password")
        if pin == "2026" or st.session_state.role == "admin":
            conn
