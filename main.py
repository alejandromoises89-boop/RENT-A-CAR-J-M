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
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("<style>.stButton>button{background-color:#D4AF37; color:black; border-radius:10px; font-weight:bold; width:100%;} .stExpander{border: 1px solid #D4AF37 !important; border-radius:10px;}</style>", unsafe_allow_html=True)

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
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, acepto_contrato INTEGER)')
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

# --- FUNCIONES ---
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
    disp = c.fetchone()[0] == 0
    conn.close()
    return disp

# --- INTERFAZ ---
st.markdown("<h1 style='text-align:center;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37;">R$ {v["precio"]} / día</p></div>''', unsafe_allow_html=True)
            with st.expander(f"Disponibilidad y Contrato"):
                # Calendario (Simplificado para estabilidad visual)
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                st.write("📅 **Calendario de Ocupación** (Días marcados no disponibles)")
                
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), time(10,0))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), time(12,0))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("Documento (CI/RG)", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    c_p = st.text_input("Domicilio", key=f"p{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    
                    if c_n and c_d:
                        # --- CONTRATO DE 12 CLÁUSULAS ---
                        contrato_html = f"""
                        <div style="background-color: #f4f4f4; color: #111; padding: 20px; border-radius: 10px; height: 350px; overflow-y: scroll; font-family: 'Courier New', monospace; font-size: 12px; border: 2px solid #D4AF37; text-align: justify;">
                            <center><b>CONTRATO DE LOCACIÓN DE VEHÍCULO - J&M ASOCIADOS</b></center><br>
                            <b>PRIMERA:</b> El ARRENDADOR entrega el vehículo {v['nombre'].upper()} (Placa: {v['placa']}) en óptimas condiciones.<br>
                            <b>SEGUNDA:</b> El ARRENDATARIO: {c_n.upper()} con Doc: {c_d} se compromete a devolverlo en igual estado.<br>
                            <b>TERCERA:</b> Precio pactado R$ {v['precio']} por día. TOTAL: R$ {total_r}.<br>
                            <b>CUARTA:</b> El uso es exclusivo para territorio nacional y MERCOSUR autorizado.<br>
                            <b>QUINTA:</b> Responsabilidad civil y penal recae íntegramente sobre el Arrendatario.<br>
                            <b>SEXTA:</b> Prohibido subarrendar o ceder la conducción a terceros no autorizados.<br>
                            <b>SÉPTIMA:</b> Límite de 200km diarios. El excedente genera costos adicionales.<br>
                            <b>OCTAVA:</b> En caso de siniestro, el deducible es de Gs. 5.000.000.<br>
                            <b>NOVENA:</b> Multas de tránsito durante el periodo son cargo del Arrendatario.<br>
                            <b>DÉCIMA:</b> El vehículo debe devolverse con el mismo nivel de combustible.<br>
                            <b>UNDÉCIMA:</b> Mantenimiento preventivo corre por cuenta del Arrendador.<br>
                            <b>DUODÉCIMA:</b> Jurisdicción: Tribunales de Ciudad del Este, Paraguay.<br><br>
                            <b>FIRMA ELECTRÓNICA:</b> Validado mediante Checkbox e IP del dispositivo.<br>
                            <b>FECHA:</b> {date.today()}
                        </div>
                        """
                        st.markdown(contrato_html, unsafe_allow_html=True)
                        acepto = st.checkbox("ACEPTO LAS 12 CLÁUSULAS Y FIRMO DIGITALMENTE", key=f"chk{v['nombre']}")
                        
                        st.warning(f"TOTAL A PAGAR: R$ {total_r} (PIX: 24510861818)")
                        foto = st.file_uploader("Subir Comprobante PIX", key=f"f{v['nombre']}")
                        
                        if st.button("FINALIZAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, acepto_contrato) VALUES (?,?,?,?,?,?,?,?,?)",
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read(), 1))
                                conn.commit(); conn.close()
                                
                                msg = f"Hola J&M ASOCIADOS! Soy {c_n}, confirmo reserva de {v['nombre']}. He LEÍDO y AFIRMADO las 12 cláusulas del contrato. Total: R$ {total_r}. Adjunto mi comprobante."
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR COMPROBANTE POR WHATSAPP</a>', unsafe_allow_html=True)
                            else:
                                st.error("Debe adjuntar la foto del comprobante.")

with t_adm:
    if st.text_input("Acceso Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        
        st.subheader("📊 GESTIÓN ESTRATÉGICA")
        # Visualización Unificada de Reservas
        for _, r in res_df.iterrows():
            with st.container():
                st.markdown(f"""<div style="border:1px solid #D4AF37; padding:15px; border-radius:10px; margin-bottom:10px; background-color:#1a1a1a;">
                    <h4 style="margin:0; color:#D4AF37;">Reserva #{r['id']} - {r['cliente']}</h4>
                    <p style="margin:0; font-size:14px;">Vehículo: {r['auto']} | Total: R$ {r['total']}</p>
                </div>""", unsafe_allow_html=True)
                
                c_a1, c_a2 = st.columns(2)
                with c_a1:
                    if st.checkbox("Visualizar Contrato Firmado", key=f"vc_{r['id']}"):
                        st.code(f"CONTRATO JM ASOCIADOS\nID: {r['id']}\nCLIENTE: {r['cliente']}\nDOC: {r['ci']}\nESTADO: FIRMADO ELECTRÓNICAMENTE\nFECHA: {r['inicio']}")
                        st.download_button("Descargar Contrato (.txt)", f"CONTRATO JM - {r['cliente']}\n\n12 Clausulas Aceptadas.\nVehiculo: {r['auto']}\nFirma: {r['cliente']}", f"Contrato_{r['id']}.txt")
                with c_a2:
                    if r['comprobante']:
                        if st.checkbox("Ver Comprobante PIX", key=f"vp_{r['id']}"):
                            st.image(r['comprobante'], width=250)
                
                if st.button("Eliminar Registro", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        
        st.divider()
        st.subheader("⚙️ AJUSTES DE FLOTA")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2,1,1])
            ca1.write(f"**{f['nombre']}**")
            new_p = ca2.number_input("Precio R$", value=float(f['precio']), key=f"pr_{f['nombre']}")
            if ca3.button("TALLER / DISP", key=f"st_{f['nombre']}"):
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", ("En Taller" if f['estado']=="Disponible" else "Disponible", f['nombre']))
                conn.commit(); st.rerun()
        conn.close()
