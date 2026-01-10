import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTILO INVERTIDO: FONDO BLANCO / TARJETAS BORDÓ ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1 { color: #800000 !important; text-align: center; }
    
    /* Etiquetas en negro para que se vean sobre fondo blanco */
    label, .stDateInput label, .stTimeInput label, .stTextInput label, .stSelectbox label {
        color: #1a1c23 !important;
        font-weight: bold !important;
    }

    /* Tarjetas de autos en Bordó */
    .card-auto {
        background-color: #800000;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #D4AF37;
        margin-bottom: 10px;
        color: white;
        text-align: center;
    }
    .card-auto h3 { color: #D4AF37 !important; margin-bottom: 5px; }
    
    /* Pestañas */
    button[data-baseweb="tab"] p { color: #800000 !important; font-weight: bold !important; }
    
    /* Contrato en fondo oscuro para resaltar */
    .contrato-scroll {
        background-color: #f9f9f9; 
        color: #333; 
        padding: 20px; 
        border-radius: 10px; 
        height: 300px; 
        overflow-y: scroll; 
        border: 1px solid #D4AF37;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()
DB_NAME = 'jm_corporativo_permanente.db'

# --- BASE DE DATOS (CON LIMPIEZA DE DUPLICADOS) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    # Lista maestra de autos
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
    ]
    
    # Insertar solo si no existe el nombre (PRIMARY KEY)
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES AUXILIARES ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row['inicio']).date()
            end = pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close()
    return disponible

# --- INTERFAZ ---
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    # Leemos la flota y eliminamos duplicados por nombre por si acaso
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn).drop_duplicates(subset=['nombre'])
    conn.close()
    
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%">
                    <p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p>
                    <p style="color:#ffffff; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p>
                </div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                # Calendario Airbnb ... (Mismo código de calendario que ya tienes)
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                # ... [Aquí va tu bloque de html_cal del calendario] ...
                
                # --- DATOS DE RESERVA ---
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"d2{v['nombre']}")
                
                # Lógica de horarios que ya manejas
                h_ini = c1.time_input("Hora Entrega", time(8,0), key=f"h1{v['nombre']}")
                h_fin = c2.time_input("Hora Retorno", time(12,0), key=f"h2{v['nombre']}")
                
                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)

                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    
                    if c_n and c_d and c_w:
                        dias = max(1, (f_fin - f_ini).days)
                        total_r = dias * v['precio']
                        
                        st.markdown(f'<div class="contrato-scroll"><b>CONTRATO JM</b><br>Cliente: {c_n}<br>Auto: {v["nombre"]}<br>Total: R$ {total_r}</div>', unsafe_allow_html=True)
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            # Guardar y enviar WhatsApp...
                            st.success("¡Reserva Lista!")

# --- SECCIONES RESTANTES ---
with t_ubi: st.write("Ubicación JM")
with t_adm: 
    if st.text_input("Clave", type="password") == "8899":
        st.write("Panel Admin")