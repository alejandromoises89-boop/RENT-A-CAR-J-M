import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

DB_NAME = 'jm_corporativo_permanente.db'

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .cal-header { font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0 5px 0; color: #333; text-transform: capitalize; }
    .cal-grid-fijo { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0px; max-width: 320px; margin: 0 auto; border: 0.2px solid #eee; }
    .cal-box-fijo { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: 12px; position: relative; background: white; color: #222; border: 0.1px solid #f7f7f7; }
    .cal-day-name-fijo { text-align: center; font-size: 10px; color: #717171; font-weight: bold; padding-bottom: 5px; }
    .ocupado { color: #ccc !important; background-color: #fafafa; }
    .raya-roja-h { position: absolute; width: 80%; height: 1.5px; background-color: #ff385c; z-index: 1; top: 50%; }
    .card-auto { border: 1px solid #ddd; padding: 15px; border-radius: 15px; background: white; text-align: center; }
    .contrato-container { background-color: #1a1a1a; color: #f1f1f1; padding: 20px; border-radius: 10px; font-size: 12px; border: 1px solid #D4AF37; height: 350px; overflow-y: scroll; text-align: justify; line-height: 1.5; }
    .btn-whatsapp { background-color: #25D366; color: white !important; padding: 12px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    conn.commit(); conn.close()

init_db()

# --- FUNCIONES ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close(); bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start, end = pd.to_datetime(row['inicio']).date(), pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37;">R$ {v["precio"]} / día</p></div>', unsafe_allow_html=True)
            with st.expander("Ver Disponibilidad y Reservar"):
                # Calendario Visual
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                c_m1, c_m2 = st.columns(2)
                for idx, (m, a) in enumerate([(date.today().month, date.today().year), ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]):
                    with [c_m1, c_m2][idx]:
                        st.markdown(f'<div class="cal-header">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
                        d_h = "".join([f'<div class="cal-day-name-fijo">{d}</div>' for d in ["L","M","M","J","V","S","D"]])
                        d_b = ""
                        for sem in calendar.monthcalendar(a, m):
                            for d in sem:
                                if d == 0: d_b += '<div class="cal-box-fijo" style="background:transparent; border:none;"></div>'
                                else:
                                    f_act = date(a, m, d)
                                    es_o = f_act in ocupadas
                                    clase = "cal-box-fijo ocupado" if es_o else "cal-box-fijo"
                                    raya = '<div class="raya-roja-h"></div>' if es_o else ""
                                    d_b += f'<div class="{clase}">{d}{raya}</div>'
                        st.markdown(f'<div class="cal-grid-fijo">{d_h}{d_b}</div>', unsafe_allow_html=True)

                st.divider()
                # Selección de Fecha y HORA
                c1, c2 = st.columns(2)
                fi = c1.date_input("Fecha Inicio", key=f"fi{v['nombre']}", value=date.today())
                hi = c1.time_input("Hora Entrega", value=time(10, 0), key=f"hi{v['nombre']}")
                ff = c2.date_input("Fecha Fin", key=f"ff{v['nombre']}")
                hf = c2.time_input("Hora Devolución", value=time(10, 0), key=f"hf{v['nombre']}")
                
                dt_inicio = datetime.combine(fi, hi)
                dt_fin = datetime.combine(ff, hf)
                
                c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                c_ci = st.text_input("CI / Documento", key=f"ci{v['nombre']}")
                c_wa = st.text_input("WhatsApp", key=f"wa{v['nombre']}")
                
                dias = max(1, (ff - fi).days)
                total_r = dias * v['precio']
                
                if c_n and c_ci:
                    st.markdown(f"""
                    <div class="contrato-container">
                        <center><b>CONTRATO DE ALQUILER DE VEHÍCULO</b></center><br>
                        <b>ARRENDADOR:</b> J&M ASOCIADOS. RUC: 1.702.076-0.<br>
                        <b>ARRENDATARIO:</b> {c_n.upper()}. CI: {c_ci}.<br><br>
                        <b>VEHÍCULO:</b> {v['nombre']}. PLACA: {v['placa']}.<br>
                        <b>PERIODO:</b> Desde {fi} ({hi}) hasta {ff} ({hf}).<br>
                        <b>PRECIO TOTAL:</b> R$ {total_r}.<br><br>
                        <b>CLÁUSULAS:</b> El arrendatario se hace responsable civil y penalmente del vehículo. 
                        Se establece un depósito de Gs. 5.000.000 en caso de siniestro. 
                        El kilometraje permitido es de 200km por día.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    foto = st.file_uploader("Subir Comprobante", key=f"f{v['nombre']}")
                    if st.button("CONFIRMAR Y GUARDAR", key=f"b{v['nombre']}"):
                        conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_ci, c_wa, v['nombre'], dt_inicio, dt_fin, total_r, foto.read() if foto else None)); conn.commit(); conn.close()
                        msg = f"Hola JM, soy {c_n}. He leído el contrato y acepto los términos.\n🚗 Vehículo: {v['nombre']}\n🗓️ Entrega: {fi} {hi}\n🗓️ Devolución: {ff} {hf}\n💰 Total: R$ {total_r}"
                        st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-whatsapp">ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)

with t_ubi:
    st.markdown("### 📍 Ubicación y Contacto")
    col1, col2 = st.columns(2)
    with col1:
        st.info("📍 Curupayty esquina Farid Rahal, CDE.")
        st.markdown("[💬 WhatsApp Soporte](https://wa.me/595983635573)")
        st.markdown("[📞 Llamar ahora](tel:+595983635573)")
    with col2:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.4475475653514!2d-54.6111!3d-25.5111!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQwLjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1620000000000!5m2!1ses!2spy" width="100%" height="300" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.subheader("⚙️ Gestión de Precios")
        for _, f in flota_adm.iterrows():
            c_a, c_b = st.columns([3,1])
            new_p = c_a.number_input(f"Precio diario {f['nombre']}", value=f['precio'], key=f"p_{f['nombre']}")
            if c_b.button("Guardar", key=f"save_{f['nombre']}"):
                conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (new_p, f['nombre'])); conn.commit(); st.rerun()

        st.divider()
        st.subheader("📊 Descargar Datos")
        c_d1, c_d2 = st.columns(2)
        c_d1.download_button("📥 Descargar Ingresos (Excel)", res_df.to_csv(index=False), "ingresos.csv")
        c_d2.download_button("📥 Descargar Gastos (Excel)", egr_df.to_csv(index=False), "gastos.csv")

        st.subheader("📑 Reservas Registradas")
        for _, r in res_df.iterrows():
            with st.expander(f"{r['cliente']} - {r['auto']}"):
                st.write(f"Inicio: {r['inicio']} | Fin: {r['fin']}")
                st.write(f"Monto: R$ {r['total']}")
                if r['comprobante']: st.image(r['comprobante'], width=250)
                if st.button("Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()