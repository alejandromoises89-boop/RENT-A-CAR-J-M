import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN VISUAL ESTILO "DASHBOARD PREMIUM" ---
st.set_page_config(page_title="J&M ASOCIADOS | Premium", layout="wide")

def aplicar_estilo_imagen():
    st.markdown("""
    <style>
        /* Importar Fuente Elegante */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        * { font-family: 'Montserrat', sans-serif; }

        /* Fondo de la App: Degradado Radial */
        .stApp {
            background: radial-gradient(circle at top, #3d0a0a 0%, #121212 100%);
            color: #ffffff;
        }

        /* Encabezado Superior Dorado */
        .header-jm {
            text-align: center;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-bottom: 2px solid #D4AF37;
            margin-bottom: 30px;
        }
        .header-jm h1 { color: #D4AF37; font-weight: 700; letter-spacing: 2px; margin:0; }

        /* Tarjetas de Vehículos (Glassmorphism) */
        .car-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        .car-card:hover {
            border-color: #D4AF37;
            transform: translateY(-10px);
            background: rgba(212, 175, 55, 0.05);
        }

        /* Botones Estilo Premium */
        div.stButton > button {
            background: linear-gradient(90deg, #D4AF37 0%, #B8860B 100%) !important;
            color: black !important;
            font-weight: bold !important;
            border-radius: 12px !important;
            border: none !important;
            height: 45px;
            width: 100%;
            transition: 0.4s;
        }
        div.stButton > button:hover {
            box-shadow: 0px 0px 15px rgba(212, 175, 55, 0.6);
            transform: scale(1.02);
        }

        /* Métricas del Admin */
        [data-testid="stMetricValue"] { color: #D4AF37 !important; }
        
        /* Estilo de los Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255,255,255,0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 10px;
            color: white;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #D4AF37 !important;
            color: black !important;
        }
    </style>
    
    <div class="header-jm">
        <h1>J&M ASOCIADOS</h1>
        <p style="color: #D4AF37; margin:0;">CONCESIONARIA & RENT-A-CAR CORPORATIVO</p>
    </div>
    """, unsafe_allow_html=True)

aplicar_estilo_imagen()

# --- 2. BASE DE DATOS Y LÓGICA ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. UI: PESTAÑAS ---
t_alquilar, t_ubi, t_admin = st.tabs(["🚗 ALQUILAR VEHÍCULO", "📍 UBICACIÓN", "🛡️ DASHBOARD ADMIN"])

with t_alquilar:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    
    cols = st.columns(2) # Dos columnas de tarjetas
    for i, v in enumerate(flota.iterrows()):
        v = v[1]
        with cols[i % 2]:
            st.markdown(f"""
            <div class="car-card">
                <img src="{v['img']}" style="width: 100%; max-width: 250px; margin-bottom: 15px;">
                <h3 style="color: #D4AF37;">{v['nombre']}</h3>
                <p style="font-size: 1.2rem; font-weight: bold;">R$ {v['precio']} <small>/ día</small></p>
                <p style="color: {'#00FF00' if v['estado']=='Disponible' else '#FF0000'};">● {v['estado']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("RESERVAR AHORA"):
                d_i = st.date_input("Inicio", key=f"d1{v['nombre']}")
                d_f = st.date_input("Fin", key=f"d2{v['nombre']}")
                nom = st.text_input("Nombre Completo", key=f"nom{v['nombre']}")
                ci = st.text_input("Documento (CI)", key=f"ci{v['nombre']}")
                
                if st.button("CONFIRMAR PAGO", key=f"btn{v['nombre']}"):
                    if nom and ci:
                        st.info("⚠️ Envíe el comprobante PIX: 24510861818")
                        st.success("Reserva procesada. Bloqueando fechas...")
                    else: st.error("Complete los datos.")

with t_ubi:
    st.markdown("""
        <div style="border: 2px solid #D4AF37; border-radius: 20px; overflow: hidden;">
            <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.12345678!2d-54.6166!3d-25.5166!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzU5LjgiUyA1NMKwMzcnMDAuMCJX!5e0!3m2!1ses!2spy!4v1625000000000" 
            width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
        </div>
    """, unsafe_allow_html=True)

with t_admin:
    if st.text_input("Código de Acceso", type="password") == "8899":
        st.subheader("📊 Resumen Financiero")
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("INGRESOS TOTALES", f"R$ {res_df['total'].sum():,.2f}")
        c2.metric("AUTOS ACTIVOS", "4")
        c3.metric("RESERVAS MES", len(res_df))

        if not res_df.empty:
            fig = px.bar(res_df, x='auto', y='total', color_discrete_sequence=['#D4AF37'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#D4AF37")
            st.plotly_chart(fig, use_container_width=True)
            
        st.subheader("📋 Gestión de Reservas")
        st.dataframe(res_df.drop(columns=['comprobante']))
        conn.close()