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
        .header-jm { text-align: center; color: #D4AF37; font-size: 3rem; font-weight: bold; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 20px; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y COTIZACIÓN ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_brl REAL, fecha_registro TEXT)')
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

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def logout():
    # Mensaje de despedida antes de limpiar la sesión
    placeholder = st.empty()
    placeholder.success("✨ Gracias por confiar en J&M Asesoría Contable. ¡Vuelva pronto!")
    time.sleep(2) # Pausa para que el cliente lea el mensaje
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_name = None
    st.rerun()

# --- 4. INTERFAZ ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">ACCESO AL SISTEMA</div>', unsafe_allow_html=True)
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
    # --- BARRA SUPERIOR (BIENVENIDA Y SALIDA) ---
    c_top1, c_top2 = st.columns([0.8, 0.2])
    with c_top1:
        st.write(f"👤 Bienvenido/a: **{st.session_state.user_name}**")
    with c_top2:
        if st.button("🚪 Cerrar Sesión"):
            logout()

    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">Alquiler de Vehículos</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center; color:#D4AF37;">Cotización: 1 Real = {cotizacion_hoy:,} PYG</p>', unsafe_allow_html=True)

    tab_list = ["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación", "⭐ Reseñas"]
    if st.session_state.role == "admin": tab_list.append("⚙️ Panel Master")
    tabs = st.tabs(tab_list)

    # (Lógica de Catálogo e Historial simplificada para el ejemplo)
    with tabs[0]:
        st.info("Seleccione su vehículo y confirme su reserva para ver las opciones de pago.")
        # Aquí iría tu lista de autos 'flota' con los botones de reserva...

    # --- PANEL MASTER: FINANZAS Y ESTADÍSTICAS ---
    if st.session_state.role == "admin":
        with tabs[4]:
            st.title("📊 Panel Master - Balance Anual")
            conn = sqlite3.connect('jm_asociados.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            if not df.empty:
                # Métricas financieras para la exposición
                ingresos = df['monto_brl'].sum()
                gastos = ingresos * 0.30 # Ejemplo: 30% gastos
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Ingresos Totales", f"{ingresos:,.2f} BRL")
                col2.metric("Egresos (Mant.)", f"{gastos:,.2f} BRL", delta_color="inverse")
                col3.metric("Utilidad Neta", f"{(ingresos - gastos):,.2f} BRL")
                
                st.divider()
                st.subheader("📈 Rendimiento de Metas")
                st.bar_chart(df['auto'].value_counts())
                
                st.write("### Detalle de Transacciones")
                st.dataframe(df, use_container_width=True)
                
                if st.button("🗑️ Borrar Reservas (Limpieza de Auditoría)"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.success("Base de datos de reservas limpia.")
                    st.rerun()
            else:
                st.warning("No hay datos financieros para mostrar en el balance.")
            conn.close()
