import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
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
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Blanco"),
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
def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "No Disponible":
        conn.close(); return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio, t_fin))
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
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    
                    # Cálculo de valores
                    dias = max(1, (dt_f - dt_i).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    precio_dia_gs = total_gs / dias

                    if c_n and c_d and c_w:
                        st.warning("⚠️ **ATENCIÓN:** Es obligatorio leer el contrato antes de pagar.")
                        
                        st.markdown("### 📄 PREVISUALIZACIÓN DEL CONTRATO")
                        # AQUÍ INTEGRAMOS TUS VARIABLES DENTRO DEL TEXTO DEL CONTRATO
                        contrato_texto = f"""
                        <div style="background-color: #2b0606; color: #f1f1f1; padding: 20px; border: 1px solid #D4AF37; border-radius: 10px; height: 300px; overflow-y: scroll; font-size: 12px; font-family: sans-serif; line-height: 1.5;">
                            <center><b>CONTRATO DE ALQUILER DE VEHÍCULO</b></center><br>
                            <b>ARRENDADOR:</b> JM ASOCIADOS | R.U.C. 1.702.076-0<br>
                            <b>ARRENDATARIO:</b> {c_n.upper()} | Doc: {c_d}<br><br>
                            <b>OBJETO:</b> Alquiler de {v['nombre']} (Placa: {v['placa']}) Color: {v['color']}.<br>
                            <b>DURACIÓN:</b> {dias} días. Desde {dt_i.strftime('%d/%m/%Y %H:%M')} hasta {dt_f.strftime('%d/%m/%Y %H:%M')}.<br>
                            <b>PRECIO:</b> Gs. {precio_dia_gs:,.0f} por día. TOTAL: Gs. {total_gs:,.0f}.<br><br>
                            <b>CLÁUSULAS PRINCIPALES:</b><br>
                            1. Uso exclusivo en Paraguay y MERCOSUR.<br>
                            2. Depósito de Gs. 5.000.000 en caso de siniestro.<br>
                            3. Límite de 200km/día. Excedente: 100.000 Gs.<br>
                            4. Responsabilidad Civil y Penal a cargo del arrendatario.<br>
                            5. El vehículo se entrega con soporte técnico en video.<br><br>
                            <i>Al confirmar la reserva, usted acepta los términos del contrato.</i>
                        </div>
                        """
                        st.markdown(contrato_texto, unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez - Santander</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y ACEPTAR CONTRATO", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                st.success("¡Reserva Guardada!")
                                
                                msj_wa = f"Hola JM, soy *{c_n}*. He aceptado el contrato y adjunto pago por el {v['nombre']}."
                                link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msj_wa)}"
                                st.markdown(f'<a href="{link_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 ENVIAR COMPROBANTE AL WHATSAPP</div></a>', unsafe_allow_html=True)
                            else:
                                st.error("Debe adjuntar el comprobante.")
                else:
                    st.error("Vehículo no disponible para estas fechas.")

# --- SECCIONES RESTANTES IGUAL ---
with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 20px; overflow: hidden;"><iframe src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d3600.613528221598!2d-54.6025215!3d-25.5179536!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2zMjXCsDMxJzA0LjYiUyA1NMKwMzYnMDkuMSJX!5e0!3m2!1ses!2spy!4v1715801234567" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe></div>', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave Admin", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        st.title("📊 BALANCE")
        ing = res_df['total'].sum() if not res_df.empty else 0
        st.metric("INGRESOS TOTALES", f"R$ {ing:,.2f}")
        
        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"{r['cliente']} - {r['auto']}"):
                if r['comprobante']: st.image(r['comprobante'], width=300)
                if st.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
