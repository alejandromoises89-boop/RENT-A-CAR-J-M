import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
from fpdf import FPDF
import styles 
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
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
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
            delta = (f_fin - f_ini).days
            for i in range(delta + 1):
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

# CSS PARA EL CALENDARIO COMPACTO (TIPO AIRBNB)
st.markdown("""
    <style>
    .month-container { max-width: 280px; margin: 0 auto; }
    .month-title { font-size: 14px; font-weight: bold; text-align: center; margin: 10px 0; color: #333; text-transform: capitalize; }
    .day-header { font-size: 11px; color: #888; text-align: center; font-weight: normal; }
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
    .cal-day-box { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: 13px; position: relative; color: #333; }
    .ocupado { color: #ccc !important; }
    .raya-roja { position: absolute; width: 80%; height: 1.5px; background-color: #ff385c; transform: rotate(-45deg); z-index: 1; }
    .card-auto img { filter: drop-shadow(0px 10px 10px rgba(0,0,0,0.3)); }
    </style>
""", unsafe_allow_html=True)

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
                    <img src="{v["img"]}" width="100%">
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37; margin-bottom: 2px;">R$ {v['precio']} / día</p>
                    <p style="font-weight: bold; color: #28a745; margin-top: 0px;">Gs. {precio_en_guaranies:,.0f} / día</p>
                </div>
            ''', unsafe_allow_html=True)
            
            with st.expander(f"Alquilar {v['nombre']}"):
                # --- CALENDARIO COMPACTO ---
                st.write("### 🗓️ Disponibilidad")
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                
                # Mostramos mes actual y el siguiente
                hoy = date.today()
                meses = [(hoy.month, hoy.year), (hoy.month + 1 if hoy.month < 12 else 1, hoy.year if hoy.month < 12 else hoy.year + 1)]
                
                for m, a in meses:
                    nombre_mes = calendar.month_name[m]
                    st.markdown(f'<div class="month-title">{nombre_mes} {a}</div>', unsafe_allow_html=True)
                    
                    c_cal = st.columns(7)
                    for idx, sem_día in enumerate(["L", "M", "M", "J", "V", "S", "D"]):
                        c_cal[idx].markdown(f'<div class="day-header">{sem_día}</div>', unsafe_allow_html=True)
                    
                    cal_data = calendar.monthcalendar(a, m)
                    for semana in cal_data:
                        c_dias = st.columns(7)
                        for idx, dia in enumerate(semana):
                            if dia == 0:
                                c_dias[idx].write("")
                            else:
                                fecha_act = date(a, m, dia)
                                es_ocupado = fecha_act in ocupadas
                                if es_ocupado:
                                    c_dias[idx].markdown(f'<div class="cal-day-box ocupado">{dia}<div class="raya-roja"></div></div>', unsafe_allow_html=True)
                                else:
                                    c_dias[idx].markdown(f'<div class="cal-day-box">{dia}</div>', unsafe_allow_html=True)
                
                st.divider()

                # --- FORMULARIO ORIGINAL (SIN CAMBIOS) ---
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

                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                st.success("¡Reserva Guardada!")
                                msj_wa = f"Hola JM, soy {c_n}. Reservé {v['nombre']} del {dt_i.strftime('%d/%m')} al {dt_f.strftime('%d/%m')}. Adjunto mi comprobante."
                                link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msj_wa)}"
                                st.markdown(f'<a href="{link_wa}" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 ENVIAR AL WHATSAPP</div></a>', unsafe_allow_html=True)
                else:
                    st.error("Fechas no disponibles.")

# --- SECCIONES UBICACIÓN Y ADM ---
with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy" frameborder="0"></iframe>', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave de Acceso", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        st.write("### PANEL DE CONTROL")
        st.dataframe(res_df.drop(columns=['comprobante']))
        for _, r in res_df.iterrows():
            if st.button(f"🗑️ BORRAR RESERVA #{r['id']}", key=f"del_{r['id']}"):
                conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                conn.commit(); st.rerun()
        conn.close()