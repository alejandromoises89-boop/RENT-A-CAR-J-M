import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO JM ---
st.set_page_config(page_title="JM ALQUILER - SISTEMA CORPORATIVO", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; border-radius: 8px; }
    .card-auto { background-color: rgba(0,0,0,0.5); padding: 20px; border-left: 5px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .pix-box { background-color: rgba(212, 175, 55, 0.1); border: 2px dashed #D4AF37; padding: 15px; border-radius: 10px; margin: 10px 0; text-align: center; color: #D4AF37; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY", "Negro"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY", "Perla")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    cuerpo = f"""
    CONTRATO Nro: {res['id']} | FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ARRENDATARIO: {res['cliente']} | VEHICULO: {res['auto']} | PLACA: {placa} | COLOR: {color}
    INICIO: {res['inicio']} | FIN: {res['fin']} | TOTAL: R$ {res['total']}

    CLÁUSULAS:
    1. El arrendatario asume responsabilidad civil y criminal del vehículo.
    2. El vehículo debe ser devuelto en las mismas condiciones.
    3. Multas e infracciones corren por cuenta del cliente.
    4. Prohibido subalquilar o prestar el vehículo a terceros.
    5. En caso de accidente, avisar de inmediato a JM Asociados.
    ... (Contrato de 12 Cláusulas legales JM)
    """
    pdf.multi_cell(0, 6, cuerpo)
    return pdf.output(dest='S').encode('latin-1')

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# --- 4. LOGIN / REGISTRO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False

if not st.session_state.logueado:
    st.title("🔑 JM ACCESO")
    c1, c2 = st.tabs(["Entrar", "Registrar"])
    with c1:
        corr = st.text_input("Correo")
        passw = st.text_input("Clave", type="password")
        if st.button("INGRESAR"):
            if corr == "admin@jm.com" and passw == "8899":
                st.session_state.logueado, st.session_state.u_nom = True, "admin"; st.rerun()
            else:
                conn = sqlite3.connect(DB_NAME)
                u = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (corr, passw)).fetchone()
                conn.close()
                if u: st.session_state.logueado, st.session_state.u_nom = True, u[0]; st.rerun()
                else: st.error("Error de acceso")
    with c2:
        with st.form("reg"):
            n = st.text_input("Nombre"); e = st.text_input("Correo"); p = st.text_input("Clave"); cel = st.text_input("WhatsApp")
            if st.form_submit_button("Crear"):
                conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n,e,p,cel)); conn.commit(); conn.close()
                st.success("Listo!"); st.rerun()
else:
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logueado = False; st.rerun()

    t1, t2, t3 = st.tabs(["🚗 ALQUILAR", "📍 MAPA", "🛡️ PANEL ADMIN"])

    with t1:
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        for _, v in flota.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"></div>', unsafe_allow_html=True)
                with st.expander(f"Programar: {v['nombre']}"):
                    c_in, c_fn = st.columns(2)
                    dt1 = datetime.combine(c_in.date_input("Inicio", key=f"d1{v['nombre']}"), c_in.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                    dt2 = datetime.combine(c_fn.date_input("Fin", key=f"d2{v['nombre']}"), c_fn.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                    
                    if esta_disponible(v['nombre'], dt1, dt2):
                        total = max(1, (dt2-dt1).days) * v['precio']
                        st.markdown(f"""
                        <div class="pix-box">
                            <h4>💰 DATOS DE PAGO PIX</h4>
                            <p><b>Monto a Transferir:</b> R$ {total}</p>
                            <p><b>Llave PIX (CNPJ/CPF):</b> 24510861818</p>
                            <p><b>Beneficiario:</b> Marina Baez</p>
                            <p><b>Banco:</b> Santander</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        comp = st.file_uploader("Subir Comprobante (Captura de Pantalla)", type=['png', 'jpg', 'jpeg'], key=f"up{v['nombre']}")
                        
                        if st.button(f"Confirmar Reserva {v['nombre']}"):
                            if comp:
                                binary_img = comp.read()
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?)", 
                                             (st.session_state.u_nom, v['nombre'], dt1, dt2, total, binary_img))
                                conn.commit(); conn.close()
                                st.success("✅ RESERVA CONFIRMADA. El administrador verificará su pago.")
                                msg_wa = f"Hola, soy {st.session_state.u_nom}. Acabo de reservar el {v['nombre']} y subí el comprobante PIX de R$ {total} al sistema."
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg_wa)}" class="wa-btn">📲 AVISAR POR WHATSAPP</a>', unsafe_allow_html=True)
                            else:
                                st.error("⚠️ Debe subir el comprobante para finalizar.")
                    else: st.error("❌ NO DISPONIBLE EN ESTAS FECHAS")

    with t2:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.4019283734133!2d-54.6434446!3d-25.5083056!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68500e5f4ec0d%3A0x336570e74f87f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses-419!2spy!4v17158000000005" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

    with t3:
        if st.session_state.u_nom == "admin":
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.title("🛡️ CONTROL ADMINISTRATIVO")
            st.metric("TOTAL INGRESOS", f"R$ {res['total'].sum():,.2f}")
            
            for _, r in res.iterrows():
                with st.expander(f"Reserva {r['id']} - {r['cliente']}"):
                    c_x1, c_x2 = st.columns(2)
                    c_x1.write(f"**Auto:** {r['auto']} | **Monto:** R$ {r['total']}")
                    if r['comprobante']:
                        c_x1.image(r['comprobante'], caption="Comprobante Enviado", width=250)
                    
                    f_i = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                    pdf = generar_contrato_pdf(r, f_i[0], f_i[1])
                    c_x2.download_button("📥 DESCARGAR CONTRATO", pdf, f"Contrato_{r['id']}.pdf")
                    if c_x2.button("🗑️ Borrar", key=f"del{r['id']}"):
                        conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
            conn.close()