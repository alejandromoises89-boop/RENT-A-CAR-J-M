import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
from fpdf import FPDF
import styles # Asegúrate de tener este archivo styles.py

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

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf_contrato(reserva):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    total_gs = reserva['total'] * COTIZACION_DIA
    
    pdf.multi_cell(0, 10, f"""
    FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ARRENDATARIO: {reserva['cliente']}
    DOCUMENTO: {reserva['ci']}
    WHATSAPP: {reserva['numero']}
    VEHICULO: {reserva['auto']}
    DESDE: {reserva['inicio']} 
    HASTA: {reserva['fin']}
    
    PRECIO PACTADO POR DIA: R$ {reserva['precio_pactado']}
    TOTAL PAGADO: R$ {reserva['total']} (Equivalente a Gs. {total_gs:,.0f})
    
    EL ARRENDATARIO DECLARA RECIBIR EL VEHICULO EN OPTIMAS CONDICIONES Y SE 
    HACE RESPONSABLE CIVIL Y PENALMENTE POR EL USO DEL MISMO DURANTE EL PERIODO MENCIONADO.
    """)
    return pdf.output(dest='S').encode('latin-1')

# --- FUNCIONES DISPONIBILIDAD ---
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
                    
                    dias = max(1, (dt_f - dt_i).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    precio_dia_gs = total_gs / dias

                    if c_n and c_d and c_w:
                        st.warning("⚠️ **ATENCIÓN:** Antes de proceder al pago, es obligatorio leer el contrato.")
                        st.markdown(f"""
                        <div style="background-color: #2b0606; color: #f1f1f1; padding: 20px; border: 1px solid #D4AF37; border-radius: 10px; height: 200px; overflow-y: scroll; font-size: 13px;">
                            <center><h4 style="color:#D4AF37;">CONTRATO DE ALQUILER</h4></center>
                            <b>ARRENDADOR:</b> JM ASOCIADOS | <b>ARRENDATARIO:</b> {c_n.upper()}<br>
                            <b>PRECIO PACTADO:</b> Gs. {precio_dia_gs:,.0f} por día. <b>TOTAL: Gs. {total_gs:,.0f}</b>.<br>
                            Usted se hace responsable civil y penalmente del vehículo.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y ACEPTAR CONTRATO", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("""INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, precio_pactado) 
                                             VALUES (?,?,?,?,?,?,?,?,?)""", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read(), v['precio']))
                                conn.commit(); conn.close()
                                st.success("¡Reserva confirmada!")
                                
                                msj_wa = f"""Hola JM, soy {c_n}.
He leído el contrato y acepto los términos.
🚗 Vehículo: {v['nombre']}
🗓️ Periodo: {dt_i.strftime('%d/%m/%Y')} al {dt_f.strftime('%d/%m/%Y')}
💰 Total: R$ {total_r}
Adjunto mi comprobante de pago."""
                                
                                texto_url = urllib.parse.quote(msj_wa)
                                link_wa = f"https://wa.me/595991681191?text={texto_url}"
                                
                                st.markdown(f'''
                                    <a href="{link_wa}" target="_blank" style="text-decoration:none;">
                                        <div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">
                                            📲 ENVIAR COMPROBANTE AL WHATSAPP
                                        </div>
                                    </a>
                                ''', unsafe_allow_html=True)
                            else:
                                st.warning("Por favor, adjunte la foto del comprobante.")
                else:
                    st.error("Vehículo no disponible para estas fechas.")

with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('''
        <div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden; margin-bottom: 20px;">
            <iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.547144342774!2d-54.6138652!3d-25.5184519!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68ff184000001%3A0xc34346816007c050!2sC.%20Farid%20Rahal%20Canan%2C%20Ciudad%20del%20Este!5e0!3m2!1ses!2spy!4v1700000000000" frameborder="0" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
        </div>
    ''', unsafe_allow_html=True)
    
    col_social1, col_social2 = st.columns(2)
    with col_social1:
        st.markdown('''<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank" style="text-decoration:none;"><div style="background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; font-size:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">📸 INSTAGRAM OFICIAL</div></a>''', unsafe_allow_html=True)
    with col_social2:
        st.markdown('''<a href="https://wa.me/595991681191" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; font-size:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">💬 WHATSAPP EMPRESARIAL</div></a>''', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave de Acceso", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL ESTRATÉGICO")
        st.write(f"**Cotización Actual:** 1 R$ = {COTIZACION_DIA:,.0f} Gs.")
        
        ing_r = res_df['total'].sum() if not res_df.empty else 0
        egr_r = egr_df['monto'].sum() if not egr_df.empty else 0
        util_r = ing_r - egr_r

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("INGRESOS TOTALES", f"R$ {ing_r:,.2f}")
            st.caption(f"Gs. {ing_r * COTIZACION_DIA:,.0f}")
        with c2:
            st.metric("GASTOS TOTALES", f"R$ {egr_r:,.2f}")
            st.caption(f"Gs. {egr_r * COTIZACION_DIA:,.0f}")
        with c3:
            st.metric("UTILIDAD NETA", f"R$ {util_r:,.2f}")
            st.caption(f"Gs. {util_r * COTIZACION_DIA:,.0f}")

        with st.expander("💰 ACTUALIZAR PRECIOS ACTUALES"):
            for idx, row in flota_adm.iterrows():
                col_p1, col_p2 = st.columns([2, 1])
                nuevo_p = col_p1.number_input(f"{row['nombre']}", value=float(row['precio']), key=f"p_adm_{row['nombre']}")
                if col_p2.button("GUARDAR", key=f"btn_p_{row['nombre']}"):
                    conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (nuevo_p, row['nombre']))
                    conn.commit(); st.rerun()

        with st.expander("📅 BLOQUEAR FECHAS / CARGAR HISTÓRICO"):
            with st.form("form_historico"):
                h_cli = st.text_input("Cliente")
                h_auto = st.selectbox("Vehículo", flota_adm['nombre'].tolist())
                h_pre = st.number_input("Precio pagado (R$ día)", min_value=0.0)
                h_ini = st.date_input("Inicio")
                h_fin = st.date_input("Fin")
                if st.form_submit_button("REGISTRAR Y BLOQUEAR"):
                    d = max(1, (h_fin - h_ini).days)
                    conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total, precio_pactado) VALUES (?,?,?,?,?,?)",
                                 (h_cli, h_auto, h_ini, h_fin, d*h_pre, h_pre))
                    conn.commit(); st.rerun()

        with st.expander("💸 CARGAR GASTO"):
            with st.form("g_form"):
                con = st.text_input("Concepto (Ej: Lavado, Taller, Repuesto)")
                mon_texto = st.text_input("Monto en Gs. (Usa puntos, ej: 150.000)", value="0")
                if st.form_submit_button("Guardar Gasto"):
                    try:
                        mon_limpio = float(mon_texto.replace(".", "").replace(",", ""))
                        mon_en_reales = mon_limpio / COTIZACION_DIA
                        if mon_limpio > 0:
                            conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", 
                                         (con, mon_en_reales, date.today()))
                            conn.commit(); st.success("Gasto guardado."); st.rerun()
                    except:
                        st.error("Formato de monto inválido.")

        st.subheader("🛠️ ESTADO DE LA FLOTA")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2, 1, 1])
            ca1.write(f"**{f['nombre']}**")
            ca2.write("🟢" if f['estado']=="Disponible" else "🔴 Taller")
            if ca3.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "En Taller" if f['estado']=="Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("📑 REGISTRO DE RESERVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"#{r['id']} - {r['cliente']} ({r['auto']})"):
                col_r1, col_r2 = st.columns([2, 1])
                with col_r1:
                    t_gs = r['total'] * COTIZACION_DIA
                    st.write(f"**Periodo:** {r['inicio']} a {r['fin']}")
                    st.write(f"**Total:** R$ {r['total']} | **Gs. {t_gs:,.0f}**")
                    pdf_data = generar_pdf_contrato(r)
                    st.download_button("📄 CONTRATO PDF", pdf_data, f"Contrato_{r['id']}.pdf", "application/pdf")
                with col_r2:
                    if r['comprobante']: st.image(r['comprobante'], width=150)
                    if st.button("🗑️ BORRAR", key=f"del_{r['id']}"):
                        conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                        conn.commit(); st.rerun()
        conn.close()
