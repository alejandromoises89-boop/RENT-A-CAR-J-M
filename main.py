import streamlit as st
import sqlite3
import pandas as pd
import requests # Necesario para la cotización
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles  

# --- 1. FUNCIÓN DE COTIZACIÓN EN LÍNEA (REAL A GUARANÍ) ---
def obtener_cotizacion():
    try:
        # Consulta a API de tipo de cambio
        url = "https://open.er-api.com/v6/latest/BRL"
        response = requests.get(url, timeout=5)
        data = response.json()
        return round(data['rates']['PYG'], 0)
    except:
        # Valor de respaldo si falla la conexión
        return 1450.0 

COTIZACION_DIA = obtener_cotizacion()

# --- 2. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")
try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("<style>.stApp { background-color: #000; color: white; }</style>", unsafe_allow_html=True)

# --- 3. BASE DE DATOS (Asegúrate de incluir total_pyg) ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Agregamos 'total_pyg' a la tabla para guardar el registro histórico
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, 
                  inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, total_pyg REAL)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/PGrYTDhJ/2098.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 4. FUNCIÓN PDF ACTUALIZADA ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    
    # Se agrega el monto en Guaraníes al texto del contrato
    cuerpotexto = f"""En Ciudad del Este, a {datetime.now().strftime('%d/%m/%Y')}, JM ASOCIADOS (Locador) y {res['cliente']} (Locatario) con CI {res['ci']}, acuerdan:

1. OBJETO: Alquiler del vehículo {res['auto']}, Placa: {placa}, Color: {color}.
2. PLAZO: Desde {res['inicio']} hasta {res['fin']}.
3. PRECIO: R$ {res['total']} (Equivalente a Gs. {res.get('total_pyg', 0):,.0f}).
... [Resto de cláusulas] ...
"""
    pdf.multi_cell(0, 7, cuerpotexto)
    return pdf.output(dest='S').encode('latin-1')

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

# --- 5. INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
# Barra de cotización superior
st.markdown(f'<div style="text-align:center; background:#D4AF37; color:black; padding:5px; border-radius:10px; font-weight:bold;">Cotización hoy: 1 Real = {COTIZACION_DIA:,.0f} Gs.</div>', unsafe_allow_html=True)

t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_pyg = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%">
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37; margin-bottom:0;">R$ {v['precio']} / día</p>
                    <p style="color: #28a745; font-weight: bold;">Gs. {precio_pyg:,.0f} / día</p>
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
                    
                    total_brl = max(1, (dt_f - dt_i).days) * v['precio']
                    total_pyg = total_brl * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_brl}</b><br>Equivalente a: <b>Gs. {total_pyg:,.0f}</b><br>Llave: 24510861818</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, total_pyg) VALUES (?,?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_brl, foto.read(), total_pyg))
                                conn.commit(); conn.close()
                                st.success(f"Reserva por Gs. {total_pyg:,.0f} guardada!")
                                st.rerun()

with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    
    # Mapa de Ciudad del Este (Versión estable sin errores de API)
    st.markdown('''
        <div style="border: 2px solid #D4AF37; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <iframe 
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57610.05739023021!2d-54.654344186523425!3d-25.5174415!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f690806437979b%3A0x6a2c300895318049!2sCiudad%20del%20Este%2C%20Paraguay!5e0!3m2!1ses!2spy!4v1700000000000!5m2!1ses!2spy" 
                width="100%" 
                height="450" 
                style="border:0;" 
                allowfullscreen="" 
                loading="lazy" 
                referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
    ''', unsafe_allow_html=True)
    
    # Botón de Instagram debajo del mapa
    st.markdown('<br><a href="https://www.instagram.com/jm_asociados_consultoria" target="_blank" style="text-decoration:none;"><div style="background-color:#E1306C; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">📸 VISITAR INSTAGRAM OFICIAL</div></a>', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave Admin", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        st.title("📊 BALANCE Y FINANZAS")
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_f1, c_f2, c_f3 = st.columns(3)
        c_f1.metric("INGRESOS", f"R$ {ing:,.2f}")
        c_f2.metric("GASTOS", f"R$ {egr:,.2f}")
        c_f3.metric("NETO", f"R$ {ing - egr:,.2f}")
        
        if not res_df.empty:
            fig = px.bar(res_df, x='auto', y='total', color='auto', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("💸 REGISTRAR GASTO"):
            con = st.text_input("Concepto")
            mon = st.number_input("Monto R$", 0.0)
            if st.button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, date.today()))
                conn.commit(); st.rerun()

        st.subheader("🛠️ ESTADO DE FLOTA")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            col_b1, col_b2 = st.columns([3, 1])
            col_b1.write(f"{f['nombre']} - ({f['estado']})")
            if col_b2.button("CAMBIAR", key=f"sw{f['nombre']}"):
                nuevo = "No Disponible" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                ca, cb = st.columns(2)
                if r['comprobante']: ca.image(r['comprobante'], width=200)
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf = generar_contrato_pdf(r, f_d[0], f_d[1])
                cb.download_button("📥 CONTRATO PDF", pdf, f"Contrato_{r['cliente']}.pdf", key=f"pdf{r['id']}")
                if cb.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
