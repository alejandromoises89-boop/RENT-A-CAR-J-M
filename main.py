import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 3rem; font-weight: bold; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 20px; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 20px; }
        .btn-logout { background-color: #ff4b4b; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; float: right; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE BASE DE DATOS Y COTIZACIÓN ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_brl REAL, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER)')
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
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# --- 4. INTERFAZ DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">ACCESO AL SISTEMA</div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", u
            st.session_state.logged_in = True
            st.rerun()
else:
    # --- BOTÓN CERRAR SESIÓN (TOP RIGHT) ---
    col_h1, col_h2 = st.columns([0.9, 0.1])
    with col_h2:
        if st.button("🚪 Salir"):
            logout()

    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">Alquiler de Vehículos</div>', unsafe_allow_html=True)
    
    tabs_labels = ["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación", "⭐ Reseñas"]
    if st.session_state.role == "admin": tabs_labels.append("⚙️ Panel Master")
    tabs = st.tabs(tabs_labels)

    # (Contenido de Catálogo, Historial, Ubicación y Reseñas se mantiene igual que la versión anterior)
    # ... [Omitido por brevedad, manteniendo tu lógica actual] ...

    # --- PANEL MASTER POTENCIADO PARA EXPOSICIÓN ---
    if st.session_state.role == "admin":
        with tabs[-1]:
            st.title("📊 Dashboard Ejecutivo J&M 2026")
            conn = sqlite3.connect('jm_asociados.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            if not df.empty:
                # Métricas Financieras
                total_brl = df['monto_brl'].sum()
                egresos = total_brl * 0.25 # Simulación de costos
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Ingresos Brutos", f"{total_brl:,.0f} BRL")
                c2.metric("Costos Op. (25%)", f"{egresos:,.0f} BRL", delta_color="inverse")
                c3.metric("Utilidad Neta", f"{(total_brl - egresos):,.0f} BRL")

                st.divider()
                st.subheader("📈 Estadísticas de Metas")
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    st.write("**Demanda por Vehículo**")
                    st.bar_chart(df['auto'].value_counts())
                
                with col_g2:
                    st.write("**Distribución de Ingresos**")
                    # Gráfico de pastel para ver qué auto genera más dinero
                    ingresos_auto = df.groupby('auto')['monto_brl'].sum()
                    st.write(ingresos_auto) # Esto muestra una tabla rápida
                
                st.divider()
                st.subheader("📋 Gestión de Datos")
                st.dataframe(df, use_container_width=True)
                
                if st.button("🗑️ Borrar Historial para Nueva Exposición"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.warning("Historial limpiado.")
                    st.rerun()
            else:
                st.info("Sin datos para mostrar estadísticas.")
            conn.close()
