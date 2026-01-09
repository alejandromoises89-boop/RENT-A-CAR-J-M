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
    label, .stDateInput label, .stTimeInput label, .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: #D4AF37 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    .streamlit-expanderHeader, button[data-baseweb="tab"] p {
        color: #D4AF37 !important;
        font-weight: bold !important;
    }
    .contrato-dorado {
        background-color: #1a1c23; 
        color: #D4AF37; 
        padding: 25px; 
        border-radius: 10px; 
        height: 380px; 
        overflow-y: scroll; 
        font-family: 'Courier New', monospace; 
        font-size: 13px; 
        border: 2px solid #D4AF37; 
        text-align: justify; 
        line-height: 1.5;
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
    except: return 1450.0

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
    for a in autos: c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit(); conn.close()

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
                # Calendario Airbnb
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                meses_display = [(date.today().month, date.today().year), ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]
                html_cal = """<style>.airbnb-container { display: flex; flex-direction: row; gap: 25px; overflow-x: auto; padding: 10px 0; }.airbnb-month { min-width: 200px; flex: 1; }.airbnb-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }.airbnb-cell { position: relative; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 500; color: white; }.airbnb-raya { position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%; left: 0; z-index: 1; }</style><div class="airbnb-container">"""
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div class="airbnb-month"><div style="color:#D4AF37; font-weight:600; margin-bottom:10px; text-transform:capitalize;">{nombre_mes} {a}</div><div class="airbnb-grid">'
                    for d_nom in ["L","M","M","J","V","S","D"]: html_cal += f'<div style="font-size:11px; color:#888;">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia); es_ocu = f_act in ocupadas; raya = '<div class="airbnb-raya"></div>' if es_ocu else ""
                                html_cal += f'<div class="airbnb-cell {"airbnb-ocupado" if es_ocu else ""}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                st.markdown(html_cal + "</div>", unsafe_allow_html=True)

                st.divider()
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"d2{v['nombre']}")
                
                # Horarios dinámicos
                es_finde_i = f_ini.weekday() >= 5
                es_finde_f = f_fin.weekday() >= 5
                h_max_i = time(12, 0) if es_finde_i else time(17, 0)
                h_max_f = time(12, 0) if es_finde_f else time(17, 0)
                h_ini = c1.time_input(f"Hora Entrega (8:00 - {h_max_i.strftime('%H:%M')})", time(8,0), key=f"h1{v['nombre']}")
                h_fin = c2.time_input(f"Hora Retorno (8:00 - {h_max_f.strftime('%H:%M')})", h_max_f, key=f"h2{v['nombre']}")

                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("Número de WhatsApp", key=f"w{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="contrato-dorado"><b>CONTRATO J&M ASOCIADOS</b><br>Arrendatario: {c_n.upper()}<br>Vehículo: {v["nombre"]}<br>Periodo: {dt_i.strftime("%d/%m/%Y %H:%M")} al {dt_f.strftime("%d/%m/%Y %H:%M")}<br>Total: R$ {total_r}</div>', unsafe_allow_html=True)
                        acepto = st.checkbox("Acepto términos", key=f"chk{v['nombre']}")
                        foto = st.file_uploader("Comprobante PIX", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                
                                # --- MENSAJE PERSONALIZADO RESTAURADO ---
                                msg = f"Hola JM, soy {c_n}. He aceptado el contrato.\n🚗 Vehículo: {v['nombre']}\n🗓️ Retiro: {dt_i.strftime('%d/%m/%Y %H:%M')}\n🗓️ Retorno: {dt_f.strftime('%d/%m/%Y %H:%M')}\n💰 Pago Realizado: R$ {total_r}"
                                link = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                                st.markdown(f'<a href="{link}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva Guardada!")
                            else: st.error("Falta comprobante.")

# --- UBICACIÓN Y ADMINISTRACIÓN ---
with t_ubi: st.write("Sección Ubicación")
with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        st.write("Panel Admin Activo")