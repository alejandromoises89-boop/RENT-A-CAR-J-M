import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="JM ALQUILER - SISTEMA CORPORATIVO", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; border-radius: 8px; }
    .card-auto { background-color: rgba(0,0,0,0.5); padding: 20px; border-left: 5px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid white; }
    .ig-btn { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid white; }
    .logout-container { position: absolute; top: 10px; left: 10px; z-index: 1000; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_final.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, estado TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, descripcion TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 3. GENERADOR DE CONTRATOS ---
def crear_pdf_contrato(datos, placa):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO DE VEHICULO - JM", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    
    cuerpo = f"""
    CONTRATO Nro: {datos['id']} | FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ARRENDATARIO: {datos['cliente']} | VEHICULO: {datos['auto']} | PLACA: {placa}
    ENTREGA: {datos['inicio']} | DEVOLUCION: {datos['fin']} | MONTO: R$ {datos['total']}
    
    CLAUSULAS LEGALES:
    1. OBJETO: El alquiler del vehiculo descrito para uso particular.
    2. ESTADO: Se entrega en perfecto estado mecanico y de limpieza.
    3. COMBUSTIBLE: Debe devolverse con el mismo nivel de combustible recibido.
    4. SEGURO: El cliente es responsable por daños no cubiertos por terceros.
    5. MULTAS: Las infracciones de transito son responsabilidad del cliente.
    6. PROHIBICIONES: No se permite fumar ni transportar animales.
    7. DEMORAS: El retraso genera una multa del 10% por hora de demora.
    8. TERRITORIO: No se permite la salida del vehiculo del pais sin autorizacion.
    9. MANTENIMIENTO: Prohibido realizar reparaciones sin aviso previo.
    10. ACCIDENTES: Informar inmediatamente a JM Asociados ante cualquier siniestro.
    11. PAGO: Confirmado mediante PIX a la llave: 24510861818.
    12. JURISDICCION: Para cualquier conflicto rigen las leyes locales vigentes.
    
    Firma Arrendador: _________________    Firma Arrendatario: _________________
    """
    pdf.multi_cell(0, 7, cuerpo)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SESIÓN Y CONTROL DE ACCESO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_nom' not in st.session_state: st.session_state.u_nom = ""

if st.session_state.logueado:
    if st.button("🚪 Cerrar Sesión", key="logout_top"):
        st.session_state.logueado = False
        st.rerun()

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>JM ACCESO</h1>", unsafe_allow_html=True)
    c1, c2 = st.tabs(["Ingresar", "Registrarse"])
    with c1:
        corr = st.text_input("Correo")
        passw = st.text_input("Clave", type="password")
        if st.button("ENTRAR"):
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
            if st.form_submit_button("Registrar"):
                conn = sqlite3.connect(DB_NAME)
                try:
                    conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n,e,p,cel)); conn.commit()
                    st.success("Registrado!")
                except: st.error("El correo ya existe.")
                conn.close()

# --- 5. APP PRINCIPAL ---
else:
    tab1, tab2, tab3 = st.tabs(["🚗 ALQUILER", "📍 CONTACTO", "🛡️ ADMINISTRACION"])

    with tab1:
        st.write(f"Sesión: **{st.session_state.u_nom}**")
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        
        for _, v in flota.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{v["nombre"]} ({v["estado"]})</h3><img src="{v["img"]}" width="250"></div>', unsafe_allow_html=True)
                
                if v['estado'] == "Disponible":
                    with st.expander(f"Programar Alquiler: {v['nombre']}"):
                        f1, f2 = st.columns(2)
                        d1 = f1.date_input("Entrega", key=f"d1{v['nombre']}")
                        h1 = f1.time_input("Hora", time(9,0), key=f"h1{v['nombre']}")
                        d2 = f2.date_input("Devolución", key=f"d2{v['nombre']}")
                        h2 = f2.time_input("Hora ", time(10,0), key=f"h2{v['nombre']}")
                        
                        dt1, dt2 = datetime.combine(d1, h1), datetime.combine(d2, h2)
                        if st.button(f"Confirmar Reserva {v['nombre']}"):
                            total = max(1, (dt2-dt1).days) * v['precio']
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total, estado) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.u_nom, v['nombre'], dt1, dt2, total, "Confirmada"))
                            conn.commit(); conn.close()
                            
                            st.success("✅ VEHICULO BLOQUEADO")
                            txt = f"*JM ALQUILER*\nHola {st.session_state.u_nom}, reserva confirmada.\nAuto: {v['nombre']}\nTotal: R$ {total}\nPIX: 24510861818"
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(txt)}" class="wa-btn">📲 WHATSAPP CORPORATIVO 0991681191</a>', unsafe_allow_html=True)
                else:
                    st.error("Vehículo en mantenimiento o no disponible.")

    with tab2:
        st.subheader("Ubícanos en Ciudad del Este")
        st.markdown('<iframe src="https://maps.google.com/?cid=3703490403065393590&g_mp=CiVnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLkdldFBsYWNl3" width="100%" height="400" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="ig-btn">📸 INSTAGRAM OFICIAL</a>', unsafe_allow_html=True)

    with tab3:
        if st.session_state.u_nom == "admin":
            st.title("🛡️ PANEL DE FINANZAS Y CONTROL")
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            egr = pd.read_sql_query("SELECT * FROM egresos", conn)
            
            # Finanzas
            total_in = res['total'].sum()
            total_eg = egr['monto'].sum()
            st.metric("SALDO NETO (FLUJO CAJA)", f"R$ {total_in - total_eg:,.2f}", delta=f"Ingresos: {total_in}")
            
            st.subheader("📉 Estadísticas de Alquiler")
            if not res.empty:
                fig = px.pie(res, values='total', names='auto', title="Ingresos por Vehículo", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Contratos y Reservas")
            for _, r in res.iterrows():
                col1, col2, col3 = st.columns([3,1,1])
                col1.write(f"ID: {r['id']} | {r['cliente']} | {r['auto']}")
                
                placa = conn.execute("SELECT placa FROM flota WHERE nombre=?", (r['auto'],)).fetchone()[0]
                pdf_contrato = crear_pdf_contrato(r, placa)
                col2.download_button("📥 Contrato", pdf_contrato, f"Contrato_{r['id']}.pdf", key=f"dl_{r['id']}")
                
                if col3.button("🗑️ Borrar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

            st.divider()
            st.subheader("🔧 Gestión de Taller y Egresos")
            with st.expander("Registrar Egreso (Gasto)"):
                desc = st.text_input("Concepto")
                monto = st.number_input("Monto", min_value=0.0)
                if st.button("Guardar Gasto"):
                    conn.execute("INSERT INTO egresos (descripcion, monto, fecha) VALUES (?,?,?)", (desc, monto, date.today()))
                    conn.commit(); st.rerun()

            st.divider()
            if st.button("🚨 LIMPIAR TODAS LAS RESERVAS"):
                if st.text_input("PIN DE SEGURIDAD", type="password") == "0000":
                    conn.execute("DELETE FROM reservas"); conn.commit(); st.rerun()
            conn.close()
        else:
            st.warning("Acceso exclusivo para Administrador.")