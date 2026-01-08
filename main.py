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
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png"
)

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("<style>body{background-color:#0e1117; color:white;}</style>", unsafe_allow_html=True)

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
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/cK92Y5Hf/tucson-Photoroom.png", "Disponible", "AAVI502", "Blanco"),
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
            for i in range((end - start).days + 1): 
                bloqueadas.add(start + timedelta(days=i))
        except: 
            continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": 
        return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close()
    return disponible

# --- INTERFAZ ---
st.markdown("<h1 style='text-align:center;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto" style="border:1px solid #333; padding:15px; border-radius:15px; margin-bottom:10px; text-align:center;">
                <h3>{v["nombre"]}</h3>
                <img src="{v["img"]}" width="100%">
                <p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p>
                <p style="color:#28a745; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p>
            </div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad y Alquilar"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                meses_display = [(date.today().month, date.today().year), 
                                 ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]

                html_cal = '<div style="display: flex; flex-direction: row; gap: 20px; overflow-x: auto; padding: 10px 0;">'
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div style="min-width: 200px;"><div style="font-weight: 600; color: white; text-transform: capitalize; margin-bottom:10px;">{nombre_mes} {a}</div><div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center;">'
                    for d_nom in ["L","M","M","J","V","S","D"]: html_cal += f'<div style="font-size: 11px; color: #888;">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia)
                                es_ocu = f_act in ocupadas
                                color = "color: #555;" if es_ocu else "color: white;"
                                raya = '<div style="position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%;"></div>' if es_ocu else ""
                                html_cal += f'<div style="position: relative; height: 30px; display: flex; align-items: center; justify-content: center; font-size: 12px; {color}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                html_cal += '</div>'
                st.markdown(html_cal, unsafe_allow_html=True)
                st.divider()

                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(10,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(12,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    c_pais = st.text_input("País / Domicilio", key=f"p{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        st.markdown(f"""<div style="background-color: #f9f9f9; color: #333; padding: 20px; border-radius: 10px; height: 250px; overflow-y: scroll; font-family: monospace; border: 2px solid #D4AF37;">
                            <center><b>CONTRATO DE ALQUILER - JM ASOCIADOS</b></center><br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}<br><b>DOC:</b> {c_d.upper()}<br><b>VEHÍCULO:</b> {v['nombre'].upper()}<br>
                            <b>TOTAL:</b> Gs. {total_gs:,.0f} (R$ {total_r})<br><br>
                            <b>CLÁUSULAS:</b> El arrendatario es responsable penal y civilmente por el uso del vehículo. Límite de 200km/día. Cobertura Mercosur incluida.
                        </div>""", unsafe_allow_html=True)
                        acepto = st.checkbox("Acepto los términos", key=f"chk{v['nombre']}")
                        st.info(f"PAGO PIX: R$ {total_r} | Llave: 24510861818")
                        foto = st.file_uploader("Comprobante", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                texto_wa = f"Hola JM, soy {c_n}. Reservé {v['nombre']} del {dt_i.date()} al {dt_f.date()}. Total: R$ {total_r}"
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(texto_wa)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva Guardada!")
                else:
                    st.error("Vehículo no disponible en las fechas o en taller.")

with t_ubi:
    st.markdown("<h3 style='text-align: center;'>UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d3601.23!2d-54.6!3d-25.5!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e0!3m2!1ses!2spy!4v123456789"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL")
        ing_r = res_df['total'].sum() if not res_df.empty else 0
        egr_r = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_m1, c_m2, c
