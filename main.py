import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO JM ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; border-radius: 8px; }
    .card-auto { background-color: rgba(0,0,0,0.5); padding: 20px; border-left: 5px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    .logout-btn { color: white !important; background-color: #8B0000 !important; border: none; padding: 5px 15px; border-radius: 5px; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_final_v16.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, chapa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA 123", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC 445", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "XAM 990", "Negro"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "HHP 112", "Perla")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES DE CONTRATO Y LÓGICA ---
def generar_contrato_pdf(reserva_data, auto_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    
    texto_contrato = f"""
    FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ARRENDATARIO: {reserva_data['cliente']}
    VEHÍCULO: {auto_info['nombre']} | PLACA: {auto_info['chapa']} | COLOR: {auto_info['color']}
    PERIODO: Desde {reserva_data['inicio']} hasta {reserva_data['fin']}
    MONTO TOTAL: R$ {reserva_data['total']}

    CLÁUSULAS:
    1. OBJETO: El alquiler del vehículo descrito arriba.
    2. ESTADO: Se entrega en perfectas condiciones mecánicas y de limpieza.
    3. COMBUSTIBLE: Debe ser devuelto con el mismo nivel recibido.
    4. SEGURO: El arrendatario es responsable por daños a terceros.
    5. MULTAS: Cualquier infracción de tránsito es responsabilidad del arrendatario.
    6. PROHIBICIÓN: No se permite fumar ni transportar animales.
    7. DEVOLUCIÓN: El retraso genera una multa del 10% del valor diario por hora.
    8. TERRITORIO: No se permite la salida del vehículo del territorio nacional sin permiso.
    9. MANTENIMIENTO: El arrendatario no puede realizar reparaciones por su cuenta.
    10. ACCIDENTES: En caso de siniestro, informar inmediatamente a JM Asociados.
    11. PAGO: Confirmado mediante PIX a la llave 24510861818.
    12. JURISDICCIÓN: Para cualquier conflicto, rigen las leyes de la República.
    
    Firma Arrendador: ___________________   Firma Cliente: ___________________
    """
    pdf.multi_cell(0, 5, texto_contrato)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SISTEMA DE ACCESO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False

# BOTÓN CERRAR SESIÓN ARRIBA IZQUIERDA
if st.session_state.logueado:
    col_log1, col_log2 = st.columns([1, 10])
    if col_log1.button("🚪 Salir"):
        st.session_state.logueado = False
        st.rerun()

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>JM ALQUILER</h1>", unsafe_allow_html=True)
    tab_acc1, tab_acc2 = st.tabs(["Ingresar", "Registrarse"])
    
    with tab_acc1:
        correo = st.text_input("Correo")
        clave = st.text_input("Clave", type="password")
        if st.button("ENTRAR"):
            if correo == "admin@jm.com" and clave == "8899":
                st.session_state.logueado, st.session_state.u_nom = True, "admin"; st.rerun()
            else:
                conn = sqlite3.connect(DB_NAME)
                u = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (correo, clave)).fetchone()
                conn.close()
                if u: st.session_state.logueado, st.session_state.u_nom = True, u[0]; st.rerun()
                else: st.error("Datos incorrectos")
    
    with tab_acc2:
        with st.form("reg"):
            n = st.text_input("Nombre"); e = st.text_input("Correo"); p = st.text_input("Clave"); c = st.text_input("WhatsApp")
            if st.form_submit_button("Crear Cuenta"):
                conn = sqlite3.connect(DB_NAME)
                try:
                    conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n,e,p,c)); conn.commit()
                    st.success("Registrado!")
                except: st.error("Error o correo duplicado")
                conn.close()

# --- 5. APP PRINCIPAL ---
else:
    t1, t2, t3 = st.tabs(["🚗 ALQUILAR", "📍 UBICACIÓN", "⚙️ PANEL MÁSTER"])

    with t1:
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        for _, v in flota.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"></div>', unsafe_allow_html=True)
                with st.expander(f"Confirmar fechas para {v['nombre']}"):
                    c_f1, c_f2 = st.columns(2)
                    dt1 = datetime.combine(c_f1.date_input("Inicio", key=f"d1{v['nombre']}"), time(9,0))
                    dt2 = datetime.combine(c_f2.date_input("Fin", key=f"d2{v['nombre']}"), time(9,0))
                    
                    if st.button(f"RESERVAR {v['nombre']}"):
                        total = max(1, (dt2-dt1).days) * v['precio']
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)", (st.session_state.u_nom, v['nombre'], dt1, dt2, total))
                        conn.commit(); conn.close()
                        st.success("✅ Reservado.")
                        msg = f"*JM RESERVA*\nAuto: {v['nombre']}\nTotal: R$ {total}\nPIX: 24510861818\nEnvíe comprobante aquí."
                        st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="wa-btn">📲 WHATSAPP CORPORATIVO</a>', unsafe_allow_html=True)

    with t2:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.8415758362675!2d-54.6200!3d-25.5100!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzM2LjAiUyA1NMKwMzcnMTIuMCJX!5e0!3m2!1ses!2spy!4v1640000000000" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="wa-btn" style="background:linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important;">📸 INSTAGRAM</a>', unsafe_allow_html=True)

    with t3:
        if st.session_state.u_nom == "admin":
            st.title("📊 ESTADÍSTICAS Y FINANZAS")
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            # Gráficas
            if not res.empty:
                st.plotly_chart(px.pie(res, values='total', names='auto', title="Ingresos por Auto", template="plotly_dark"))
                st.plotly_chart(px.bar(res, x='cliente', y='total', color='auto', title="Alquileres por Cliente", template="plotly_dark"))
                
                # Gestión de Reservas y Contratos
                st.subheader("📋 Gestión de Reservas")
                for _, r in res.iterrows():
                    col_r1, col_r2, col_r3 = st.columns([3, 1, 1])
                    col_r1.write(f"ID {r['id']} | {r['cliente']} | {r['auto']} | R$ {r['total']}")
                    
                    # Generar Contrato con datos del auto
                    v_info = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                    pdf_c = generar_contrato_pdf(r, v_info)
                    col_r2.download_button("📥 Contrato", pdf_c, f"Contrato_{r['id']}.pdf", key=f"pdf{r['id']}")
                    
                    if col_r3.button("🗑️ Borrar", key=f"del{r['id']}"):
                        conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
            else: st.info("No hay reservas aún.")
            conn.close()