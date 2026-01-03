import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime, timedelta
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

# --- 2. BASE DE DATOS (SOPORTE CALENDARIO) ---
def init_db():
    conn = sqlite3.connect('jm_asociados_v5.db')
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

def verificar_disponibilidad(auto_nombre, fecha_str):
    conn = sqlite3.connect('jm_asociados_v5.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservas WHERE auto=? AND fecha=?", (auto_nombre, fecha_str))
    existe = c.fetchone()
    conn.close()
    return existe is None

init_db()

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. ACCESO ---
if not st.session_state.logged_in:
    st.markdown('<h1 style="text-align:center; color:#D4AF37;">J&M ASOCIADOS</h1>', unsafe_allow_html=True)
    op = st.radio("Seleccione:", ["Ingresar", "Registrarse"], horizontal=True)
    if op == "Ingresar":
        u = st.text_input("Correo")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR AL PORTAL"):
            conn = sqlite3.connect('jm_asociados_v5.db')
            c = conn.cursor()
            c.execute("SELECT nombre, tipo FROM usuarios WHERE correo=? AND password=?", (u, p))
            data = c.fetchone()
            if data:
                st.session_state.logged_in, st.session_state.user_name, st.session_state.role = True, data[0], data[1]
                st.rerun()
            else: st.error("Acceso denegado")
    else:
        with st.form("reg"):
            n = st.text_input("Nombre y Apellido")
            e = st.text_input("Email")
            dt = st.selectbox("Documento", ["CI", "CPF", "RG", "Pasaporte"])
            dn = st.text_input("Nro Documento")
            tl = st.text_input("WhatsApp")
            dr = st.text_input("Dirección")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("REGISTRAR CLIENTE"):
                conn = sqlite3.connect('jm_asociados_v5.db')
                conn.cursor().execute("INSERT INTO usuarios (nombre, documento, doc_tipo, correo, telefono, direccion, password, tipo) VALUES (?,?,?,?,?,?,?,?)", (n, dn, dt, e, tl, dr, pw, "user"))
                conn.commit()
                st.success("¡Registro exitoso! Ya puede ingresar.")

# --- 5. INTERFAZ PRINCIPAL ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()
    
    # PESTAÑAS
    tabs_labels = ["🚗 Reservar", "📅 Calendario", "📍 Ubicación", "⭐ Reseñas"]
    if st.session_state.role == "admin": tabs_labels.append("📈 Panel Master")
    
    tabs = st.tabs(tabs_labels)

    # TAB RESERVAR (CATÁLOGO)
    with tabs[0]:
        st.subheader("Catálogo de Flota")
        fecha_reserva = st.date_input("¿Para qué fecha desea el vehículo?", min_value=datetime.now())
        f_str = fecha_reserva.strftime("%d/%m/%Y")
        
        flota = [
            {"n": "Toyota Vitz Negro", "p": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson Blanco", "p": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Toyota Voxy Gris", "p": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
        ]
        
        for a in flota:
            libre = verificar_disponibilidad(a['n'], f_str)
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                c1.image(a['img'])
                with c2:
                    st.subheader(a['n'])
                    if libre:
                        st.markdown(f'<span class="status-badge disponible">🟢 LIBRE PARA EL {f_str}</span>', unsafe_allow_html=True)
                        if st.button(f"Confirmar Reserva: {a['n']}", key=f"btn_{a['n']}"):
                            conn = sqlite3.connect('jm_asociados_v5.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_brl, fecha, estado_pago) VALUES (?,?,?,?,?)",
                                                 (st.session_state.user_name, a['n'], a['p'], f_str, "Pendiente"))
                            conn.commit()
                            st.success(f"¡Reserva confirmada para el {f_str}!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.markdown(f'<span class="status-badge ocupado">🔴 OCUPADO EL {f_str}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # TAB CALENDARIO (NUEVA)
    with tabs[1]:
        st.subheader("📅 Cronograma Mensual de Ocupación")
        conn = sqlite3.connect('jm_asociados_v5.db')
        df_cal = pd.read_sql_query("SELECT auto, fecha, cliente FROM reservas", conn)
        conn.close()
        
        if not df_cal.empty:
            # Crear una tabla visual de disponibilidad
            st.write("A continuación se muestran los vehículos y sus fechas ya comprometidas:")
            st.table(df_cal)
        else:
            st.info("No hay reservas marcadas en el calendario todavía.")

    # TAB UBICACIÓN
