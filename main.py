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

# --- BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    # Imagen Tucson actualizada sin fondo blanco
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

# --- FUNCIONES ---
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
    if res and res[0] == "No Disponible":
        conn.close(); return False
    # Ajuste de formato para comparación de base de datos
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    ocupado = c.fetchone()[0]
    conn.close(); return ocupado == 0

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)

# CSS para el calendario compacto tipo Airbnb (Cuadrados perfectos)
st.markdown("""
    <style>
    .cal-grid-container { max-width: 300px; margin-bottom: 20px; }
    .day-header { font-size: 11px; color: #888; text-align: center; margin-bottom: 5px; }
    .cal-day-box { 
        aspect-ratio: 1/1; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 14px; 
        position: relative; 
        color: #333; 
        background: white; 
        border: 0.5px solid #f0f0f0;
    }
    .ocupado { color: #ccc !important; }
    .raya-roja { 
        position: absolute; 
        width: 100%; 
        height: 1.5px; 
        background-color: #dc3545; 
        transform: rotate(-45deg); 
        z-index: 1; 
    }
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
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37; margin-bottom: 2px;">
                        R$ {v['precio']} / día
                    </p>
                    <p style="font-weight: bold; color: #28a745; margin-top: 0px;">
                        Gs. {precio_en_guaranies:,.0f} / día
                    </p>
                </div>
            ''', unsafe_allow_html=True)
            
            with st.expander(f"Alquilar {v['nombre']}"):
                # --- CALENDARIO DE DISPONIBILIDAD ---
                st.write("### 🗓️ Disponibilidad")
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                
                # Mostrar Mes Actual
                hoy = date.today()
                m, a = hoy.month, hoy.year
                st.markdown(f"**{calendar.month_name[m]} {a}**")
                
                c_head = st.columns(7)
                for idx, sem in enumerate(["L", "M", "M", "J", "V", "S", "D"]):
                    c_head[idx].markdown(f'<div class="day-header">{sem}</div>', unsafe_allow_html=True)
                
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

                # --- FORMULARIO DE RESERVA ---
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
                        st.warning("⚠️ **ATENCIÓN:** Antes de proceder al pago, es obligatorio leer el contrato de alquiler.")
                        
                        st.markdown("### 📄 CONTRATO DE ALQUILER (LECTURA OBLIGATORIA)")
                        contrato_html = f"""
                        <div style="background-color: #2b0606; color: #f1f1f1; padding: 20px; border: 1px solid #D4AF37; border-radius: 10px; height: 350px; overflow-y: scroll; font-size: 13px; line-height: 1.6; font-family: sans-serif;">
                            <center><h4 style="color:#D4AF37;">CONTRATO DE ALQUILER Y AUTORIZACIÓN PARA CONDUCIR</h4></center>
                            <b>ARRENDADOR:</b> JM ASOCIADOS | C.I. 1.702.076-0<br>
                            <b>ARRENDATARIO:</b> {c_n.upper()} | C.I./Documento: {c_d}<br><br>
                            <b>DURACIÓN:</b> {dias} días. Desde {dt_i.strftime('%d/%m/%Y')} hasta {dt_f.strftime('%d/%m/%Y')}.<br>
                            <b>TOTAL: Gs. {total_gs:,.0f}</b>.<br>
                            <i>Al confirmar y subir el comprobante, usted declara haber leído y aceptado todas las cláusulas.</i>
                        </div>
                        """
                        st.markdown(contrato_html, unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez - Santander</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y ACEPTAR CONTRATO", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                st.success("¡Reserva Guardada con Éxito!")
                                msj_wa = f"Hola JM, soy {c_n}. He leído el contrato y acepto los términos. 🚗 Vehículo: {v['nombre']} 🗓️ Periodo: {dt_i.strftime('%d/%m/%Y')} al {dt_f.strftime('%d/%m/%Y')} 💰 Total: R$ {total_r} Adjunto mi comprobante de pago."
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msj_wa)}" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 ENVIAR AL WHATSAPP</div></a>', unsafe_allow_html=True)
                else:
                    st.error("Vehículo no disponible para estas fechas.")

# --- SECCIONES UBICACIÓN Y ADM (INTACTAS) ---
with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden;"><iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy" frameborder="0"></iframe></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; margin-top:20px; color:#D4AF37;"><p>📍 C/ Farid Rahal Canan, Cd. del Este, Paraguay</p></div>', unsafe_allow_html=True)

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
