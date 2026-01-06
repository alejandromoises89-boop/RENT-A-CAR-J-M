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
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    # Flota corregida: Toyota Voxy Gris añadido
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR REPLACE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES ---
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
    PARTES: J&M ASOCIADOS y el Sr./Sra. {res['cliente']}.
    DOCUMENTO: {res['ci']} | TELÉFONO: {res['celular']}
    
    VEHÍCULO: {res['auto']} | PLACA: {placa} | COLOR: {color}
    RECOGIDA: {res['inicio']} | DEVOLUCIÓN: {res['fin']}
    VALOR TOTAL: R$ {res['total']} (Pagado vía PIX)
    --------------------------------------------------------------------------------------------------
    TÉRMINOS: El arrendatario asume responsabilidad total por el uso del vehículo.
    """
    pdf.multi_cell(0, 7, texto)
    return pdf.output(dest='S').encode('latin-1')

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    if c.fetchone()[0] == "No Disponible":
        conn.close()
        return False
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# --- 4. INTERFAZ ---
st.markdown("<h1 style='text-align:center;'>🚗 J&M ASOCIADOS</h1>", unsafe_allow_html=True)
tab_res, tab_ubi, tab_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMIN"])

with tab_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    for _, v in flota.iterrows():
        with st.container():
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="220"></div>', unsafe_allow_html=True)
            with st.expander(f"Alquilar {v['nombre']}"):
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    st.write("✅ Disponible")
                    c_n = st.text_input("Nombre", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI", key=f"d{v['nombre']}")
                    c_w = st.text_input("WA", key=f"w{v['nombre']}")
                    total = max(1, (dt_f - dt_i).days) * v['precio']
                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO: R$ {total}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        if st.button("RESERVAR", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total, foto.read()))
                            conn.commit(); conn.close(); st.success("Confirmado!"); st.rerun()
                else: st.error("No disponible.")

with tab_ubi:
    # Mapa previsualizado de Ciudad del Este
    st.markdown("""
        <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.5234551466!2d-54.6133096!3d-25.5205466!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f685f7e5f8f4ed%3A0x336570e74f7c71b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v1700000000000!5m2!1ses!2spy" 
        width="100%" height="450" style="border:2px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.markdown('<a href="https://wa.me/595991681191" class="btn-social btn-wa">💬 WhatsApp Business</a>', unsafe_allow_html=True)
    c2.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="btn-social btn-ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)

with tab_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        st.metric("INGRESOS", f"R$ {res_df['total'].sum():,.2f}")
        
        st.subheader("📋 Gestión de Reservas (Borrar/Contratos)")
        for _, r in res_df.iterrows():
            with st.expander(f"Orden {r['id']} - {r['cliente']}"):
                col_a, col_b = st.columns([2,1])
                if r['comprobante']: col_a.image(r['comprobante'], width=150)
                
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf = generar_contrato_pdf(r, f_d[0], f_d[1])
                col_b.download_button("📥 CONTRATO", pdf, f"Contrato_{r['cliente']}.pdf", key=f"pdf{r['id']}")
                
                # BOTÓN PARA BORRAR RESERVA
                if col_b.button("🗑️ ELIMINAR RESERVA", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()