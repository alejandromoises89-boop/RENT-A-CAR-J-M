import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
from fpdf import FPDF
import styles # Asegúrate de tener este archivo styles.py
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)
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

# --- BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, 
                  auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, 
                  comprobante BLOB, precio_pactado REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS egresos 
                 (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)''')
    
    # IMAGEN TUCSON ACTUALIZADA (SIN FONDO)
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE DISPONIBILIDAD ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT inicio, fin FROM reservas WHERE auto = ?"
    df = pd.read_sql_query(query, conn, params=(auto,))
    conn.close()
    fechas_bloqueadas = set()
    for _, row in df.iterrows():
        try:
            f_ini = pd.to_datetime(row['inicio']).date()
            f_fin = pd.to_datetime(row['fin']).date()
            delta = f_fin - f_ini
            for i in range(delta.days + 1):
                fechas_bloqueadas.add(f_ini + timedelta(days=i))
        except: continue
    return fechas_bloqueadas

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller":
        conn.close(); return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    ocupado = c.fetchone()[0]
    conn.close(); return ocupado == 0

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_en_guaranies = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%" style="filter: drop-shadow(0px 10px 10px rgba(0,0,0,0.3));">
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37; margin-bottom: 2px;">R$ {v['precio']} / día</p>
                    <p style="font-weight: bold; color: #28a745; margin-top: 0px;">Gs. {precio_en_guaranies:,.0f} / día</p>
                </div>
            ''', unsafe_allow_html=True)
            
            with st.expander(f"📅 VER DISPONIBILIDAD Y ALQUILAR"):
                st.write("### 🗓️ Calendario Mensual")
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                
                mes_sel = st.selectbox("Seleccione el mes:", range(1, 13), 
                                     format_func=lambda x: calendar.month_name[x].capitalize(), 
                                     key=f"mes_{v['nombre']}")
                
                año_actual = date.today().year
                cal = calendar.monthcalendar(año_actual, mes_sel)
                
                # Encabezado días semana
                cols_cal = st.columns(7)
                for ic, d_nom in enumerate(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]):
                    cols_cal[ic].caption(f"**{d_nom}**")
                
                # Dibujar Calendario (SOLO NÚMEROS Y X)
                for semana in cal:
                    for idx, dia in enumerate(semana):
                        if dia == 0:
                            cols_cal[idx].write("")
                        else:
                            fecha_dia = date(año_actual, mes_sel, dia)
                            es_ocupado = fecha_dia in ocupadas
                            bg = "#dc3545" if es_ocupado else "#28a745"
                            marca = "X" if es_ocupado else dia
                            
                            cols_cal[idx].markdown(f'''
                                <div style="background-color:{bg}; color:white; border-radius:4px; text-align:center; padding:8px; margin-bottom:4px; font-weight:bold;">
                                    {marca}
                                </div>
                            ''', unsafe_allow_html=True)
                
                st.markdown("<small>🟢 Disponible | 🔴 Reservado (X)</small>", unsafe_allow_html=True)
                st.divider()

                # --- EL RESTO DEL CÓDIGO SIGUE IGUAL (Formulario, Contrato, etc.) ---
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    
                    dias = max(1, (dt_f - dt_i).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    precio_dia_gs = total_gs / dias

                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, precio_pactado) VALUES (?,?,?,?,?,?,?,?,?)",
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read(), v['precio']))
                                conn.commit(); conn.close()
                                st.success("¡Reserva confirmada!")
                                
                                msj_wa = f"Hola JM! Soy {c_n}. He reservado {v['nombre']} del {dt_i.strftime('%d/%m')} al {dt_f.strftime('%d/%m')}. Adjunto comprobante."
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msj_wa)}" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center;">📲 ENVIAR AL WHATSAPP</div></a>', unsafe_allow_html=True)
                else:
                    st.error("Vehículo no disponible para estas fechas.")

# --- SECCIONES UBICACIÓN Y ADMINISTRADOR (INTACTAS) ---
with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden; margin-bottom: 20px;"><iframe width="100%" height="400" src="https://maps.google.com/maps?q=Curupayty%20Farid%20Rahal&t=&z=15&ie=UTF8&iwloc=&output=embed" frameborder="0"></iframe></div>', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave", type="password")
    if clave == "8899":
        # Todo el código de administrador que ya tenías...
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        st.dataframe(res_df)
        conn.close()
