import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# Nombre de DB nuevo para evitar el error de columnas
DB_NAME = 'jm_final_2025.db' 

# --- ESTILOS CSS PREMIUM (FONDO OSCURO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3 { color: #D4AF37 !important; }
    .card-auto { background-color: #1a1c23; border: 1px solid #D4AF37; padding: 20px; border-radius: 15px; text-align: center; }
    .contrato-scroll { background-color: #f9f9f9; color: #1a1a1a; padding: 25px; border-radius: 10px; height: 400px; overflow-y: scroll; font-family: 'Courier New'; font-size: 13px; border: 2px solid #D4AF37; text-align: justify; }
    .cal-box { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 0.1px solid #3d4452; background: #2d323e; color: white; }
    .ocupado { background-color: #1a1c23 !important; color: #555 !important; position: relative; }
    .raya-roja { position: absolute; width: 80%; height: 2px; background-color: #ff4b4b; top: 50%; }
    .btn-wa { background-color: #25D366; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, 
        auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total_gs REAL, comprobante BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS egresos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto_r REAL, monto_gs REAL, fecha DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
        nombre TEXT PRIMARY KEY, precio_gs REAL, img TEXT, estado TEXT, 
        placa TEXT, color TEXT, marca TEXT, modelo TEXT, año TEXT, chasis TEXT)''')
    
    autos = [
        ("Hyundai Tucson Blanco", 280000, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "BLANCO", "HYUNDAI", "TUCSON", "2012", "KMHJU81VBCU36106"),
        ("Toyota Vitz Blanco", 180000, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "BLANCO", "TOYOTA", "VITZ", "2015", "NCP13-123456"),
        ("Toyota Voxy Gris", 240000, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "GRIS", "TOYOTA", "VOXY", "2014", "ZRR80-009876")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- INTERFAZ ---
st.markdown("<h1 style='text-align: center;'>J&M ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="70%"><p style="font-size:20px; color:#D4AF37;">Gs. {v["precio_gs"]:,.0f} / día</p></div>', unsafe_allow_html=True)
            with st.expander("Reservar y Ver Contrato"):
                c1, c2 = st.columns(2)
                f_i = c1.date_input("Inicio", key=f"f1{v['nombre']}")
                h_i = c1.time_input("Hora", time(10,0), key=f"h1{v['nombre']}")
                f_f = c2.date_input("Fin", key=f"f2{v['nombre']}")
                h_f = c2.time_input("Hora ", time(12,0), key=f"h2{v['nombre']}")
                
                nom = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                doc = st.text_input("Documento / CPF", key=f"d{v['nombre']}")
                tel = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                
                dias = max(1, (f_f - f_i).days)
                total = dias * v['precio_gs']
                
                if nom and doc:
                    st.markdown(f"""
                    <div class="contrato-scroll">
                        <center><b>CONTRATO DE ALQUILER DE VEHÍCULO</b></center><br>
                        <b>ARRENDADOR:</b> J&M ASOCIADOS. CI: 1.702.076-0.<br>
                        <b>ARRENDATARIO:</b> {nom.upper()}. Doc: {doc}.<br><br>
                        <b>VEHÍCULO:</b> {v['marca']} {v['modelo']} {v['año']} - Chapa: {v['placa']}<br>
                        <b>CHASIS:</b> {v['chasis']}<br>
                        <b>PERIODO:</b> {dias} días ({f_i} al {f_f}).<br>
                        <b>TOTAL:</b> Gs. {total:,.0f}.<br><br>
                        El arrendatario es responsable penal y civil de todo lo ocurrido...
                    </div>""", unsafe_allow_html=True)
                    
                    foto = st.file_uploader("Subir Comprobante", key=f"foto{v['nombre']}")
                    if st.button("CONFIRMAR", key=f"btn{v['nombre']}") and foto:
                        conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total_gs, comprobante) VALUES (?,?,?,?,?,?,?,?)", (nom, doc, tel, v['nombre'], datetime.combine(f_i, h_i), datetime.combine(f_f, h_f), total, foto.read())); conn.commit(); conn.close()
                        st.success("¡Reserva cargada!")

with t_ubi:
    st.markdown("### 📍 Ubicación: Curupayty casi Farid Rahal")
    st.markdown('<iframe src="http://googleusercontent.com/maps.google.com/6" width="100%" height="400"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.sidebar.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        # Gastos
        with st.expander("💸 CARGAR GASTO"):
            with st.form("g"):
                con = st.text_input("Concepto"); r_m = st.number_input("R$"); gs_m = st.number_input("Gs.")
                if st.form_submit_button("Guardar"):
                    conn.execute("INSERT INTO egresos (concepto, monto_r, monto_gs, fecha) VALUES (?,?,?,?)", (con, r_m, gs_m, date.today())); conn.commit(); st.rerun()
        
        # Gráficos
        if not res_df.empty:
            st.plotly_chart(px.line(res_df, x='inicio', y='total_gs', title="Ingresos", color_discrete_sequence=['#D4AF37']))
            st.plotly_chart(px.pie(res_df, values='total_gs', names='auto', hole=0.4))
        
        # Registro
        for _, r in res_df.iterrows():
            with st.expander(f"{r['cliente']} - {r['auto']}"):
                st.write(f"CI: {r['ci']} | Total: Gs. {r['total_gs']:,.0f}")
                if r['comprobante']: st.image(r['comprobante'], width=300)
        conn.close()