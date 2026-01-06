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
    .pix-box { background-color: rgba(212, 175, 55, 0.1); border: 2px dashed #D4AF37; padding: 15px; border-radius: 10px; margin: 10px 0; text-align: center; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Ya no necesitamos tabla de usuarios para el acceso, pero la dejamos para historial
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
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

# --- 3. GENERADOR DE CONTRATO ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    cuerpo = f"""
    CONTRATO Nro: {res['id']} | FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ----------------------------------------------------------------------
    DATOS DEL ARRENDATARIO:
    NOMBRE: {res['cliente']}
    CI/DOCUMENTO: {res['ci']}
    CELULAR: {res['celular']}
    
    DATOS DEL VEHÍCULO:
    VEHICULO: {res['auto']} | PLACA: {placa} | COLOR: {color}
    INICIO: {res['inicio']} | FIN: {res['fin']}
    MONTO TOTAL: R$ {res['total']}
    ----------------------------------------------------------------------
    CLÁUSULAS PRINCIPALES:
    1. El arrendatario asume responsabilidad civil y criminal del vehículo.
    2. El vehículo se entrega con mantenimiento al día y limpio.
    3. Multas e infracciones son responsabilidad del firmante.
    4. El pago se confirma mediante transferencia PIX a Marina Baez.
    5. Jurisdicción: Leyes de la República de Paraguay.

    Firma Arrendador: _________________    Firma Cliente: _________________
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

# --- 4. APP PRINCIPAL ---
st.markdown("<h1 style='text-align:center;'>🚗 JM ALQUILER EXPRESS</h1>", unsafe_allow_html=True)

tab_user, tab_map, tab_admin = st.tabs(["🚗 RESERVAR AHORA", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with tab_user:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    for _, v in flota.iterrows():
        with st.container():
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"></div>', unsafe_allow_html=True)
            with st.expander(f"Seleccionar Fechas para {v['nombre']}"):
                col1, col2 = st.columns(2)
                d1 = col1.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                h1 = col1.time_input("Hora Entrega", time(9,0), key=f"h1{v['nombre']}")
                d2 = col2.date_input("Fecha Fin", key=f"d2{v['nombre']}")
                h2 = col2.time_input("Hora Devolución", time(10,0), key=f"h2{v['nombre']}")
                
                dt_inicio = datetime.combine(d1, h1)
                dt_fin = datetime.combine(d2, h2)
                
                if esta_disponible(v['nombre'], dt_inicio, dt_fin):
                    st.success("✅ Disponible en este horario")
                    
                    # CAMPOS OBLIGATORIOS PARA EL CONTRATO
                    st.markdown("#### 📝 Datos para el Contrato")
                    c_nom = st.text_input("Nombre Completo", key=f"nom{v['nombre']}")
                    c_ci = st.text_input("Nro. de Documento (CI/RG)", key=f"ci{v['nombre']}")
                    c_cel = st.text_input("WhatsApp de Contacto", key=f"cel{v['nombre']}")
                    
                    total = max(1, (dt_fin - dt_inicio).days) * v['precio']
                    
                    if c_nom and c_ci and c_cel:
                        st.markdown(f"""
                        <div class="pix-box">
                            <h4>💰 PAGAR PARA BLOQUEAR FECHAS</h4>
                            <p>Monto: <b>R$ {total}</b></p>
                            <p>Llave PIX: <b>24510861818</b> (Banco Santander)</p>
                            <p>Beneficiario: <b>Marina Baez</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        foto = st.file_uploader("Subir foto del pago PIX", type=['jpg', 'png', 'jpeg'], key=f"foto{v['nombre']}")
                        
                        if st.button(f"FINALIZAR RESERVA {v['nombre']}"):
                            if foto:
                                binary_img = foto.read()
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_nom, c_ci, c_cel, v['nombre'], dt_inicio, dt_fin, total, binary_img))
                                conn.commit(); conn.close()
                                st.balloons()
                                st.success(f"✅ ¡Reserva Exitosa, {c_nom}! Las fechas han sido bloqueadas.")
                                
                                # Link WhatsApp
                                msg = f"Hola JM, soy {c_nom}. Reservé el {v['nombre']} de {d1} a {d2}. Pago enviado."
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="wa-btn">📲 AVISAR POR WHATSAPP</a>', unsafe_allow_html=True)
                            else:
                                st.warning("⚠️ Sube el comprobante para bloquear el auto.")
                    else:
                        st.info("ℹ️ Completa tu nombre, documento y celular para ver los datos de pago.")
                else:
                    st.error("❌ Estas fechas ya están ocupadas por otro cliente.")

with tab_map:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.4019283734133!2d-54.6434446!3d-25.5083056!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68500e5f4ec0d%3A0x336570e74f87f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses-419!2spy!4v17158000000006" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

with tab_admin:
    st.subheader("🔑 Acceso Administrativo")
    admin_pass = st.text_input("Clave de Admin", type="password")
    if admin_pass == "8899":
        conn = sqlite3.connect(DB_NAME)
        res = pd.read_sql_query("SELECT * FROM reservas", conn)
        st.metric("INGRESOS TOTALES", f"R$ {res['total'].sum():,.2f}")
        
        for _, r in res.iterrows():
            with st.expander(f"Reserva {r['id']} - {r['cliente']}"):
                col1, col2 = st.columns(2)
                col1.write(f"**Documento:** {r['ci']} | **Cel:** {r['celular']}")
                col1.write(f"**Fechas:** {r['inicio']} al {r['fin']}")
                if r['comprobante']:
                    col1.image(r['comprobante'], width=200, caption="Pago del cliente")
                
                # Obtener placa y color
                f_inf = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf = generar_contrato_pdf(r, f_inf[0], f_inf[1])
                col2.download_button("📥 DESCARGAR CONTRATO", pdf, f"Contrato_{r['cliente']}.pdf", key=f"pdf{r['id']}")
                
                if col2.button("🗑️ Borrar Reserva", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()