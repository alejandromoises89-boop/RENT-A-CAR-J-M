import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, date, timedelta, time
import uuid
import json
import requests
import os
import calendar
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM Alquiler | Premium Car Rental",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES Y DISEÑO (DESIGN SYSTEM) ---
COLORS = {
    "bordo": "#600010",
    "gold": "#D4AF37",
    "ivory": "#FDFCFB",
    "glass": "rgba(255, 255, 255, 0.9)",
    "dark": "#1A1A1A"
}

DB_NAME = 'jm_corporativo_v3.db'
ADMIN_KEY = "8899"
CORPORATE_WA = "595991681191"

# --- ESTILOS CSS PREMIUM ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['ivory']}; font-family: 'Inter', sans-serif; }}
    h1, h2, h3 {{ font-family: 'Playfair Display', serif; color: {COLORS['bordo']}; }}
    
    .vehicle-container {{
        background: white; border-radius: 30px; padding: 25px; margin-bottom: 30px;
        border-left: 8px solid {COLORS['bordo']}; box-shadow: 0 15px 35px rgba(0,0,0,0.05);
    }}
    .stButton>button {{
        background: linear-gradient(135deg, {COLORS['bordo']} 0%, #3a000a 100%);
        color: white; border-radius: 12px; border: none; padding: 12px; font-weight: 600;
    }}
    .stButton>button:hover {{ background: {COLORS['gold']}; color: white; }}
    
    /* Airbnb Calendar Style */
    .airbnb-container {{ display: flex; gap: 20px; overflow-x: auto; padding: 10px; }}
    .airbnb-month {{ background: #1a1c23; padding: 15px; border-radius: 15px; min-width: 250px; }}
    .airbnb-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; text-align: center; }}
    .airbnb-cell {{ position: relative; color: white; font-size: 12px; padding: 5px; }}
    .airbnb-ocupado {{ color: #ff385c; text-decoration: line-through; opacity: 0.5; }}
    .airbnb-raya {{ position: absolute; width: 100%; height: 2px; background: #ff385c; top: 50%; left: 0; }}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id TEXT PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, 
                  inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, status TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id TEXT PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, specs TEXT)')
    
    # Datos iniciales de flota
    autos = [
        ("Hyundai Tucson 2012", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", '{"trans": "Auto", "fuel": "Diesel", "pax": 5}'),
        ("Toyota Vitz 2012", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", '{"trans": "Auto", "fuel": "Nafta", "pax": 5}'),
        ("Toyota Vitz RS 2012", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", '{"trans": "Secuencial", "fuel": "Nafta", "pax": 5}'),
        ("Toyota Voxy 2011", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", '{"trans": "Auto", "fuel": "Nafta", "pax": 7}')
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

# --- FUNCIONES AUXILIARES ---
def get_cotizacion():
    try:
        return requests.get("https://open.er-api.com/v6/latest/BRL").json()['rates']['PYG']
    except: return 1460.0

def get_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    ocupadas = set()
    for _, r in df.iterrows():
        start, end = pd.to_datetime(r['inicio']).date(), pd.to_datetime(r['fin']).date()
        for i in range((end - start).days + 1): ocupadas.add(start + timedelta(days=i))
    return ocupadas

# --- INICIALIZACIÓN ---
init_db()
if 'view' not in st.session_state: st.session_state.view = 'HOME'
if 'cotizacion' not in st.session_state: st.session_state.cotizacion = get_cotizacion()

# --- HEADER Y NAVEGACIÓN ---
col_l, col_r = st.columns([4, 1])
with col_l:
    st.markdown(f"<h1>JM <span style='color:{COLORS['gold']}'>ALQUILER</span></h1>", unsafe_allow_html=True)
with col_r:
    st.markdown(f"**1 BRL = {st.session_state.cotizacion:,.0f} PYG**")

nav = st.columns(4)
if nav[0].button("🚗 FLOTA"): st.session_state.view = 'HOME'; st.rerun()
if nav[1].button("📍 SEDE"): st.session_state.view = 'MAP'; st.rerun()
if nav[2].button("🔐 ADMIN"): st.session_state.view = 'ADMIN'; st.rerun()
if nav[3].button("🔄"): st.session_state.cotizacion = get_cotizacion(); st.rerun()
st.divider()

# --- VISTA: HOME (FLOTA) ---
if st.session_state.view == 'HOME':
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()

    for _, car in flota.iterrows():
        specs = json.loads(car['specs'])
        col_img, col_info = st.columns([1.5, 2])
        with col_img:
            st.image(car['img'], use_container_width=True)
        with col_info:
            st.markdown(f"""
                <div class="vehicle-container">
                    <h2 style="margin:0;">{car['nombre']}</h2>
                    <p style="color:{COLORS['gold']}; font-weight:bold;">{car['placa']}</p>
                    <div style="display:flex; justify-content:space-between; margin:15px 0;">
                        <span>👤 {specs['pax']} Pax</span> <span>⚙️ {specs['trans']}</span> <span>⛽ {specs['fuel']}</span>
                    </div>
                    <h3 style="margin:0;">R$ {car['precio']} <small style="font-size:12px; color:gray;">/ día</small></h3>
                    <p style="color:green;">Gs. {car['precio'] * st.session_state.cotizacion:,.0f} aprox.</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Ver Disponibilidad y Reservar"):
                ocupadas = get_fechas_ocupadas(car['nombre'])
                # Calendario Airbnb
                cal_html = '<div class="airbnb-container">'
                for m_add in [0, 1]:
                    target_date = date.today() + timedelta(days=30*m_add)
                    m, y = target_date.month, target_date.year
                    cal_html += f'<div class="airbnb-month"><div style="color:white; text-align:center; margin-bottom:10px;">{calendar.month_name[m]} {y}</div><div class="airbnb-grid">'
                    for d in ["L","M","M","J","V","S","D"]: cal_html += f'<div style="color:gray; font-size:10px;">{d}</div>'
                    for week in calendar.monthcalendar(y, m):
                        for day in week:
                            if day == 0: cal_html += '<div></div>'
                            else:
                                curr = date(y, m, day)
                                cl = "airbnb-ocupado" if curr in ocupadas else ""
                                cal_html += f'<div class="airbnb-cell {cl}">{day}</div>'
                    cal_html += '</div></div>'
                st.markdown(cal_html + '</div>', unsafe_allow_html=True)
                
                # Formulario
                f1, f2 = st.columns(2)
                ini_d = f1.date_input("Inicio", key=f"id_{car['nombre']}")
                fin_d = f2.date_input("Fin", key=f"fd_{car['nombre']}")
                
                # Lógica de Horarios
                h_max = time(12, 0) if ini_d.weekday() >= 5 else time(17, 0)
                ini_t = f1.time_input("Entrega (8:00 a "+h_max.strftime("%H:%M")+")", time(9,0), key=f"it_{car['nombre']}")
                fin_t = f2.time_input("Retorno", time(9,0), key=f"ft_{car['nombre']}")
                
                if st.button("PROCEDER A RESERVA", key=f"btn_{car['nombre']}"):
                    if any(ini_d + timedelta(days=i) in ocupadas for i in range((fin_d - ini_d).days + 1)):
                        st.error("Fechas ocupadas")
                    else:
                        st.session_state.booking_data = {
                            "car": car['nombre'], "precio": car['precio'],
                            "inicio": datetime.combine(ini_d, ini_t),
                            "fin": datetime.combine(fin_d, fin_t)
                        }
                        st.session_state.view = 'BOOKING'; st.rerun()

# --- VISTA: RESERVA (BOOKING WIZARD) ---
elif st.session_state.view == 'BOOKING':
    data = st.session_state.booking_data
    st.markdown(f"### Confirmando: {data['car']}")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        nombre = st.text_input("Nombre Completo")
        doc = st.text_input("Documento (CI/RG/Pasaporte)")
        wa = st.text_input("WhatsApp")
        st.write("Firma el contrato digitalmente:")
        canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, key="signature")
        
    with col_b:
        dias = max(1, (data['fin'] - data['inicio']).days)
        total = dias * data['precio']
        st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:15px; border:1px solid {COLORS['gold']};">
                <h4>Resumen</h4>
                <p>Periodo: {dias} días</p>
                <p>Total R$: {total:,.2f}</p>
                <p>Total Gs: {total * st.session_state.cotizacion:,.0f}</p>
                <small>Pago vía PIX: 24510861818</small>
            </div>
        """, unsafe_allow_html=True)
        comprobante = st.file_uploader("Adjuntar Comprobante")
        
        if st.button("CONFIRMAR TODO"):
            if not (nombre and doc and wa and comprobante): st.error("Faltan datos")
            else:
                conn = sqlite3.connect(DB_NAME)
                res_id = str(uuid.uuid4())[:8]
                conn.execute("INSERT INTO reservas VALUES (?,?,?,?,?,?,?,?,?,?)", 
                             (res_id, nombre, doc, wa, data['car'], data['inicio'], data['fin'], total, comprobante.read(), "Pendiente"))
                conn.commit(); conn.close()
                st.balloons(); st.success("Reserva Enviada")
                wa_msg = urllib.parse.quote(f"Hola JM, reserva de {nombre} para {data['car']}. ID: {res_id}")
                st.markdown(f'<a href="https://wa.me/{CORPORATE_WA}?text={wa_msg}" target="_blank">ENVIAR WHATSAPP</a>', unsafe_allow_html=True)

# --- VISTA: ADMIN ---
elif st.session_state.view == 'ADMIN':
    if st.text_input("Password", type="password") == ADMIN_KEY:
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        exp_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresos R$", f"{res_df['total'].sum():,.2f}")
        m2.metric("Egresos R$", f"{exp_df['monto'].sum():,.2f}")
        
        # IA Gemini
        if st.button("✨ Generar Análisis IA"):
            try:
                genai.configure(api_key=st.secrets["GEMINI_KEY"])
                model = genai.GenerativeModel('gemini-1.5-flash')
                report = model.generate_content(f"Analiza estas ventas: {res_df[['auto', 'total']].to_json()}")
                st.info(report.text)
            except: st.error("Configura GEMINI_KEY en Secrets")

        st.subheader("Gestión de Flota")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            c1, c2, c3 = st.columns([2,1,1])
            c1.write(f"{f['nombre']} - {f['estado']}")
            if c3.button("🔧 Cambiar Estado", key=f"st_{f['nombre']}"):
                nuevo = "En Taller" if f['estado']=="Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()
        
        st.subheader("Reservas Recientes")
        st.dataframe(res_df)
        conn.close()

elif st.session_state.view == 'MAP':
    st.markdown("### Nuestra Sede - Ciudad del Este")
    st.map(pd.DataFrame({'lat': [-25.509], 'lon': [-54.611]}))