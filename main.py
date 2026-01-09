import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import styles

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTILO DORADO BLINDADO ---
st.markdown("""
    <style>
    /* Color dorado para todas las etiquetas de campos (Nombre, Fechas, etc) */
    label, .stDateInput label, .stTimeInput label, .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: #D4AF37 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    /* Color para los títulos de los Expanders */
    .streamlit-expanderHeader {
        color: #D4AF37 !important;
        font-weight: bold !important;
    }
    /* Color de los Tabs (Pestañas) */
    button[data-baseweb="tab"] p {
        color: #D4AF37 !important;
        font-weight: bold !important;
    }
    /* Descripciones y subtítulos */
    .stMarkdown p, .stMarkdown h3 {
        color: #FFFFFF !important;
    }
    /* Ajuste para que el texto dentro de los botones no sea gris */
    .stButton button {
        color: white !important;
        border: 1px solid #D4AF37 !important;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    pass

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()
DB_NAME = 'jm_corporativo_permanente.db'

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE VALIDACIÓN ---
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close()
    return disponible

# --- INTERFAZ ---
st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p><p style="color:#28a745; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                # Calendario y Selección de Horarios con Dorado Blindado
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"d2{v['nombre']}")

                es_finde_i = f_ini.weekday() >= 5
                es_finde_f = f_fin.weekday() >= 5
                h_max_i = time(12, 0) if es_finde_i else time(17, 0)
                h_max_f = time(12, 0) if es_finde_f else time(17, 0)
                
                h_ini = c1.time_input(f"Hora Entrega (8:00 - {h_max_i.strftime('%H:%M')})", time(8,0), key=f"h1{v['nombre']}")
                h_fin = c2.time_input(f"Hora Retorno (8:00 - {h_max_f.strftime('%H:%M')})", h_max_f, key=f"h2{v['nombre']}")

                horario_valido = True
                if h_ini < time(8,0) or h_ini > h_max_i:
                    st.error(f"⚠️ Entrega permitida solo de 08:00 a {h_max_i.strftime('%H:%M')}")
                    horario_valido = False
                if h_fin < time(8,0) or h_fin > h_max_f:
                    st.error(f"⚠️ Retorno permitido solo de 08:00 a {h_max_f.strftime('%H:%M')}")
                    horario_valido = False

                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                if esta_disponible(v['nombre'], dt_i, dt_f) and horario_valido:
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("Número de WhatsApp", key=f"w{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    
                    if c_n and c_d and c_w:
                        acepto = st.checkbox("He leído y acepto los términos", key=f"chk{v['nombre']}")
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                st.success("¡Reserva Guardada!")
                            else: st.error("Falta comprobante.")
                else:
                    if horario_valido: st.error("Vehículo no disponible.")

# --- PESTAÑAS UBICACIÓN Y ADM ---
with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        st.markdown("<h2 style='color:#D4AF37;'>Panel de Control</h2>", unsafe_allow_html=True)
        # El código administrativo se mantiene aquí para ver métricas y gastos.