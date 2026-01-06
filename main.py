import streamlit as st
import sqlite3
import pandas as pd
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
    .btn-social { display: flex; align-items: center; justify-content: center; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; margin: 10px 0; transition: 0.3s; }
    .btn-wa { background-color: #25D366; color: white !important; }
    .btn-ig { background-color: #E1306C; color: white !important; }
    .btn-maps { background-color: #4285F4; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS MEJORADA ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY", "Negro"),
        ("Toyota Vitz Perla", 200.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY", "Perla")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES DE APOYO ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - J&M ASOCIADOS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    
    texto = f"""
    CONTRATO Nro: {res['id']} | FECHA: {datetime.now().strftime('%d/%m/%Y')}
    --------------------------------------------------------------------------------------------------
    PARTES: J&M ASOCIADOS (Arrendador) y el Sr./Sra. {res['cliente']} (Arrendatario).
    
    DATOS DEL ARRENDATARIO:
    DOCUMENTO (CI/RG): {res['ci']}
    TELÉFONO/WA: {res['celular']}
    
    DATOS DEL VEHÍCULO:
    MARCA/MODELO: {res['auto']}
    PLACA: {placa} | COLOR: {color}
    
    DETALLES DE LA RESERVA:
    RECOGIDA: {res['inicio']}
    DEVOLUCIÓN: {res['fin']}
    VALOR TOTAL PAGADO: R$ {res['total']} (Vía PIX Santander - Marina Baez)
    --------------------------------------------------------------------------------------------------
    TÉRMINOS Y CONDICIONES:
    1. El vehículo se entrega en óptimas condiciones mecánicas y de limpieza.
    2. El Arrendatario es responsable legal por cualquier infracción de tránsito.
    3. Prohibido el uso del vehículo para fines ilícitos o subalquiler.
    4. En caso de siniestro, el cliente deberá informar inmediatamente al Arrendador.
    5. La devolución tardía generará cargos adicionales por hora.
    
    
    __________________________                    __________________________
        Firma J&M ASOCIADOS                           Firma Arrendatario
    """
    pdf.multi_cell(0, 7, texto)
    return pdf.output(dest='S').encode('latin-1')

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Verifica si el auto está marcado como "No Disponible" manualmente o si tiene reserva
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    if c.fetchone()[0] == "No Disponible":
        conn.close()
        return False
    
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# --- 4. INTERFAZ DE USUARIO ---
st.markdown("<h1 style='text-align:center;'>🚗 J&M ASOCIADOS - ALQUILER</h1>", unsafe_allow_html=True)
tab_res, tab_ubi, tab_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN Y CONTACTO", "🛡️ ADMINISTRACIÓN"])

with tab_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    for _, v in flota.iterrows():
        with st.container():
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="220"></div>', unsafe_allow_html=True)
            with st.expander(f"Ver Disponibilidad de {v['nombre']}"):
                col1, col2 = st.columns(2)
                d1 = col1.date_input("Inicio", key=f"d1{v['nombre']}")
                h1 = col1.time_input("Hora", time(9,0), key=f"h1{v['nombre']}")
                d2 = col2.date_input("Fin", key=f"d2{v['nombre']}")
                h2 = col2.time_input("Hora ", time(10,0), key=f"h2{v['nombre']}")
                
                dt_i, dt_f = datetime.combine(d1, h1), datetime.combine(d2, h2)
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    st.markdown("📝 **Datos Obligatorios para Contrato:**")
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    
                    total = max(1, (dt_f - dt_i).days) * v['precio']
                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total}</b><br>Llave: 24510861818 (Santander)<br>Titular: Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        if st.button("CONFIRMAR Y BLOQUEAR AUTO", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total, foto.read()))
                                conn.commit(); conn.close(); st.success("¡Reserva Confirmada!"); st.balloons()
                            else: st.error("Sube el comprobante de pago.")
                else: st.error("Vehículo no disponible para estas fechas.")

with tab_ubi:
    st.subheader("📍 Encuéntranos en Ciudad del Este")
    st.markdown('<iframe src="https://maps.google.com/?cid=3703490403065393590&g_mp=CiVnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLkdldFBsYWNl" width="100%" height="400" style="border-radius:15px; border:2px solid #D4AF37;"></iframe>', unsafe_allow_html=True)
    
    st.markdown("### 🔗 Enlaces Corporativos")
    c1, c2, c3 = st.columns(3)
    c1.markdown('<a href="https://wa.me/595991681191" class="btn-social btn-wa">💬 WhatsApp Business</a>', unsafe_allow_html=True)
    c2.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-social btn-ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)
    c3.markdown('<a href="https://maps.google.com/?cid=3703490403065393590&g_mp=CiVnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLkdldFBsYWNl" class="btn-social btn-maps">🗺️ Google Maps</a>', unsafe_allow_html=True)

with tab_adm:
    clave = st.text_input("Acceso Restringido", type="password")
    if clave == "8899":
        st.title("🛡️ PANEL FINANCIERO JM")
        conn = sqlite3.connect(DB_NAME)
        
        # --- SECCIÓN FINANZAS ---
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        ingresos = res_df['total'].sum()
        egresos = egr_df['monto'].sum()
        
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("INGRESOS (PIX)", f"R$ {ingresos:,.2f}")
        col_f2.metric("EGRESOS", f"R$ {egresos:,.2f}", delta_color="inverse")
        col_f3.metric("FLUJO DE CAJA", f"R$ {ingresos - egresos:,.2f}")

        # --- GESTIÓN DE EGRESOS ---
        with st.expander("💸 Registrar Nuevo Egreso"):
            concep = st.text_input("Concepto (Mantenimiento, Lavado, etc)")
            mont = st.number_input("Monto R$", min_value=0.0)
            if st.button("Guardar Egreso"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (concep, mont, date.today()))
                conn.commit(); st.rerun()

        # --- GESTIÓN DE RESERVAS Y CONTRATOS ---
        st.subheader("📑 Reservas Activas y Contratos")
        for _, r in res_df.iterrows():
            with st.expander(f"ORDEN #{r['id']} - {r['cliente']}"):
                ca, cb = st.columns(2)
                if r['comprobante']: ca.image(r['comprobante'], width=180, caption="Pago Recibido")
                
                f_data = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf_bytes = generar_contrato_pdf(r, f_data[0], f_data[1])
                cb.download_button(f"📥 DESCARGAR CONTRATO {r['cliente']}", pdf_bytes, f"Contrato_JM_{r['cliente']}.pdf")
                if cb.button(f"Eliminar Reserva {r['id']}", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

        # --- BLOQUEO DE AUTOS ---
        st.subheader("🚫 Bloqueo Manual de Flota")
        flota_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, fa in flota_adm.iterrows():
            col_b1, col_b2 = st.columns([3, 1])
            col_b1.write(f"**{fa['nombre']}** - Estado Actual: {fa['estado']}")
            nuevo_estado = "No Disponible" if fa['estado'] == "Disponible" else "Disponible"
            if col_b2.button(f"Cambiar a {nuevo_estado}", key=f"bloq{fa['nombre']}"):
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo_estado, fa['nombre']))
                conn.commit(); st.rerun()
        
        conn.close()