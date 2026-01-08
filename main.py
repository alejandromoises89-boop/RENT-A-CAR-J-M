import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
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

# --- FUNCIONES DE APOYO ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT inicio, fin FROM reservas WHERE auto = ?"
    df = pd.read_sql_query(query, conn, params=(auto,))
    conn.close()
    fechas = set()
    for _, row in df.iterrows():
        try:
            f_ini = pd.to_datetime(row['inicio']).date()
            f_fin = pd.to_datetime(row['fin']).date()
            for i in range((f_fin - f_ini).days + 1):
                fechas.add(f_ini + timedelta(days=i))
        except: continue
    return fechas

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

# CSS PARA EL CALENDARIO TIPO AIRBNB
st.markdown("""
    <style>
    .cal-container { max-width: 300px; margin: 0 auto; font-family: sans-serif; }
    .cal-title { font-size: 15px; font-weight: bold; text-align: center; margin: 10px 0; color: #333; text-transform: lowercase; }
    .cal-days-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; font-size: 11px; color: #717171; margin-bottom: 5px; }
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
    .cal-box { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: 13px; position: relative; color: #222; border: 0.5px solid #f7f7f7; }
    .ocupado { color: #b0b0b0 !important; }
    .raya-roja { position: absolute; width: 100%; height: 1px; background-color: #ff385c; transform: rotate(-45deg); z-index: 1; }
    </style>
""", unsafe_allow_html=True)

t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37;">R$ {v["precio"]} / día</p><p style="color:#28a745;">Gs. {precio_gs:,.0f} / día</p></div>', unsafe_allow_html=True)
            
            with st.expander(f"Alquilar {v['nombre']}"):
                # --- CALENDARIO ESTILO AIRBNB ---
                st.write("### 🗓️ Disponibilidad")
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                hoy = date.today()
                
                # Renderizar Mes Actual y Siguiente
                for m_offset in [0, 1]:
                    m = (hoy.month + m_offset - 1) % 12 + 1
                    a = hoy.year + (hoy.month + m_offset - 1) // 12
                    st.markdown(f'<div class="cal-title">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
                    
                    c_head = st.columns(7)
                    for d_n in ["L", "M", "M", "J", "V", "S", "D"]:
                        c_head[cal_data := ["L", "M", "M", "J", "V", "S", "D"].index(d_n)].markdown(f'<center><small>{d_n}</small></center>', unsafe_allow_html=True)
                    
                    cal_data = calendar.monthcalendar(a, m)
                    for semana in cal_data:
                        c_dias = st.columns(7)
                        for idx, dia in enumerate(semana):
                            if dia != 0:
                                fecha_act = date(a, m, dia)
                                es_ocu = fecha_act in ocupadas
                                style = "ocupado" if es_ocu else ""
                                raya = '<div class="raya-roja"></div>' if es_ocu else ""
                                c_dias[idx].markdown(f'<div class="cal-box {style}">{dia}{raya}</div>', unsafe_allow_html=True)

                st.divider()
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
                        # CONTRATO ORIGINAL
                        st.markdown(f'<div style="background-color:#2b0606; color:#f1f1f1; padding:20px; border:1px solid #D4AF37; border-radius:10px; height:300px; overflow-y:scroll; font-size:13px;"><b>CONTRATO:</b><br>Arrendatario: {c_n}...</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read())); conn.commit(); conn.close()
                            st.success("¡Reserva lista!")

with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy" frameborder="0"></iframe>', unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    col_s1.markdown('<a href="https://instagram.com" target="_blank"><div style="background:linear-gradient(45deg, #f09433, #bc1888); color:white; padding:15px; border-radius:15px; text-align:center;">📸 INSTAGRAM</div></a>', unsafe_allow_html=True)
    col_s2.markdown('<a href="https://wa.me/595991681191" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center;">💬 WHATSAPP</div></a>', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        st.title("📊 PANEL DE CONTROL")
        c_f1, c_f2 = st.columns(2)
        c_f1.metric("INGRESOS", f"R$ {res_df['total'].sum():,.2f}")
        c_f2.metric("GASTOS", f"R$ {egr_df['monto'].sum():,.2f}")
        
        fig_pie = px.pie(res_df, values='total', names='auto', hole=0.4, color_discrete_sequence=['#D4AF37', '#800020'])
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva {r['id']} - {r['cliente']}"):
                st.write(f"Auto: {r['auto']} | Total: R$ {r['total']}")
                if st.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()