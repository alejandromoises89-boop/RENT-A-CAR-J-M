import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | SISTEMA", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 20px; border: 2px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .status-badge { padding: 5px 15px; border-radius: 10px; font-weight: bold; }
        .disponible { background-color: #2ecc71; color: white; }
        .ocupado { background-color: #e74c3c; color: white; }
        .price-tag { font-size: 1.5rem; color: #4e0b0b; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, tipo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_total REAL, fecha_inicio TEXT, fecha_fin TEXT)''')
    try:
        c.execute("INSERT INTO usuarios (nombre, correo, password, tipo) VALUES (?,?,?,?)", ("ADMIN MASTER", "admin@jymasociados.com", "JM2026_MASTER", "admin"))
    except: pass
    conn.commit()
    conn.close()

def verificar_rango_libre(auto, inicio, fin):
    conn = sqlite3.connect('jm_asociados_final.db')
    c = conn.cursor()
    # Verifica si hay solapamiento de fechas
    c.execute('''SELECT * FROM reservas WHERE auto=? AND NOT (fecha_fin < ? OR fecha_inicio > ?)''', (auto, inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")))
    conflicto = c.fetchone()
    conn.close()
    return conflicto is None

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
        if st.button("ACCEDER"):
            conn = sqlite3.connect('jm_asociados_final.db')
            c = conn.cursor()
            c.execute("SELECT nombre, tipo FROM usuarios WHERE correo=? AND password=?", (u, p))
            data = c.fetchone()
            if data:
                st.session_state.logged_in, st.session_state.user_name, st.session_state.role = True, data[0], data[1]
                st.rerun()
            else: st.error("Usuario o clave incorrecta")
    else:
        with st.form("reg"):
            n = st.text_input("Nombre Completo")
            e = st.text_input("Correo")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("REGISTRAR"):
                conn = sqlite3.connect('jm_asociados_final.db')
                conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, tipo) VALUES (?,?,?,?)", (n, e, pw, "user"))
                conn.commit()
                st.success("¡Cuenta creada!")

# --- 5. PORTAL ---
else:
    st.sidebar.write(f"👤 **{st.session_state.user_name}**")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    tabs = st.tabs(["🚗 Alquiler", "📅 Mi Calendario", "📍 Ubicación", "⚙️ Panel Master"])

    # TAB ALQUILER
    with tabs[0]:
        st.subheader("Configura tu Reserva")
        col_f1, col_f2 = st.columns(2)
        d_inicio = col_f1.date_input("Fecha de Retiro", min_value=datetime.now())
        d_fin = col_f2.date_input("Fecha de Devolución", min_value=d_inicio + timedelta(days=1))
        
        dias = (d_fin - d_inicio).days
        st.info(f"Duración total: **{dias} días**")

        flota = [
            {"n": "Toyota Vitz", "p": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson", "p": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Toyota Voxy", "p": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
        ]

        for a in flota:
            libre = verificar_rango_libre(a['n'], d_inicio, d_fin)
            total_pagar = a['p'] * dias
            
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                c1.image(a['img'])
                with c2:
                    st.subheader(a['n'])
                    if libre:
                        st.markdown('<span class="status-badge disponible">🟢 DISPONIBLE</span>', unsafe_allow_html=True)
                        st.write(f"Precio por día: {a['p']} BRL")
                        st.markdown(f'<p class="price-tag">Total a pagar: {total_pagar} BRL</p>', unsafe_allow_html=True)
                        if st.button(f"Reservar {a['n']}", key=f"res_{a['n']}"):
                            conn = sqlite3.connect('jm_asociados_final.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_total, fecha_inicio, fecha_fin) VALUES (?,?,?,?,?)",
                                                 (st.session_state.user_name, a['n'], total_pagar, d_inicio.strftime("%Y-%m-%d"), d_fin.strftime("%Y-%m-%d")))
                            conn.commit()
                            st.success("✅ ¡Reserva realizada!")
                            st.write("Escanee el PIX para confirmar su pago:")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=JM_PAGO_{total_pagar}_BRL")
                    else:
                        st.markdown('<span class="status-badge ocupado">🔴 NO DISPONIBLE EN ESTAS FECHAS</span>', unsafe_allow_html=True)
                        st.warning("Este vehículo ya tiene una reserva que se cruza con tus fechas.")
                st.markdown('</div>', unsafe_allow_html=True)

    # TAB CALENDARIO (Vista de ocupación)
    with tabs[1]:
        st.subheader("Historial de Reservas")
        conn = sqlite3.connect('jm_asociados_final.db')
        df_cal = pd.read_sql_query("SELECT auto, fecha_inicio, fecha_fin, cliente FROM reservas", conn)
        st.dataframe(df_cal, use_container_width=True)
        conn.close()

    # TAB UBICACIÓN
    with tabs[2]:
        st.markdown("### 📍 J&M ASOCIADOS Consultoría")
        st.write("C/Farid Rahal Canan, Ciudad del Este | Tel: 0983 787810")
        st.markdown('<iframe src="https://maps.google.com/?cid=3703490403065393590&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ2" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen=""></iframe>', unsafe_allow_html=True)

    # TAB PANEL MASTER (CON PIN DE SEGURIDAD)
    with tabs[3]:
        st.title("⚙️ Control Administrativo")
        pin = st.text_input("Ingrese PIN de Seguridad para acceder", type="password")
        if pin == "2026" or st.session_state.role == "admin":
            st.success("Acceso Autorizado")
            conn = sqlite3.connect('jm_asociados_final.db')
            df_admin = pd.read_sql_query("SELECT * FROM reservas", conn)
            if not df_admin.empty:
                c_m1, c_m2 = st.columns(2)
                c_m1.metric("Ingresos Proyectados", f"{df_admin['monto_total'].sum()} BRL")
                c_m2.metric("Total de Alquileres", len(df_admin))
                st.write("### Gráfico de Demanda")
                st.bar_chart(df_admin['auto'].value_counts())
                if st.button("🗑️ Resetear todas las reservas"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.rerun()
            else: st.info("No hay datos todavía.")
            conn.close()
        elif pin != "":
            st.error("PIN Incorrecto")
