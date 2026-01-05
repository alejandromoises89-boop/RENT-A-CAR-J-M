import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y DISEÑO DE BOTONES INVERTIDOS ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    /* Fondo y textos generales */
    .stApp { background-color: #4A0404; color: #D4AF37; }
    h1, h2, h3, p, label { color: #D4AF37 !important; font-weight: bold; }
    
    /* Inputs en Negro con borde Dorado */
    input, textarea, [data-baseweb="select"], [data-baseweb="input"] {
        background-color: black !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
    }
    
    /* BOTONES: Fondo Negro, Letras Doradas, Borde Dorado */
    .stButton>button {
        background-color: black !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
        font-weight: bold;
        width: 100%;
        border-radius: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #D4AF37 !important;
        color: black !important;
    }
    
    .card-auto {
        background-color: black;
        padding: 20px;
        border: 3px solid #D4AF37;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    
    .btn-wa { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-align: center; display: block; text-decoration: none; margin-top: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCIA Y BASE DE DATOS ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'perfil' not in st.session_state: st.session_state.perfil = "user"

def init_db():
    conn = sqlite3.connect('jm_master_v4.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, h_entrega TEXT, h_devolucion TEXT, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, chapa TEXT, chasis TEXT, precio REAL, img TEXT)')
    
    autos = [
        ("Hyundai Tucson", "AA-123", "TUC-7721", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"),
        ("Toyota Vitz Blanco", "BCC-445", "VTZ-001", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png"),
        ("Toyota Vitz Negro", "XAM-990", "VTZ-998", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"),
        ("Toyota Voxy", "HHP-112", "VOX-556", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- 3. FUNCIONES DE APOYO ---
def get_fechas_ocupadas(auto):
    conn = sqlite3.connect('jm_master_v4.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    fechas = set()
    for _, r in df.iterrows():
        start = datetime.strptime(r['inicio'], '%Y-%m-%d').date()
        end = datetime.strptime(r['fin'], '%Y-%m-%d').date()
        while start <= end:
            fechas.add(start)
            start += timedelta(days=1)
    return fechas

def generar_pdf(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 10, "CONTRATO JM ASOCIADOS", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    cuerpo = f"Cliente: {d['cliente']}\nAuto: {d['auto']} (Chapa: {d['chapa']})\nEntrega: {d['inicio']} {d['he']}\nDevolución: {d['fin']} {d['hd']}\nTotal: R$ {d['total']}\n\nFirma Digital: {d['firma']}"
    pdf.multi_cell(0, 10, cuerpo)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. ACCESO JM ---
if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>Acceso JM</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size:80px;'>🔒</h1>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    user = col_l.text_input("Usuario")
    pw = col_r.text_input("Contraseña", type="password")
    
    if st.button("INGRESAR"):
        if user == "admin" and pw == "8899": st.session_state.perfil = "admin"
        st.session_state.logueado = True; st.session_state.u_name = user; st.rerun()
    
    st.button("Crear cuenta y Guardar")
    st.button("Olvidé mi contraseña")
    st.button("Acceso con Biometría")

# --- 5. APLICACIÓN PRINCIPAL ---
else:
    st.markdown("<h2 style='text-align:center;'>JM ALQUILER DE VEHICULOS</h2>", unsafe_allow_html=True)
    if st.sidebar.button("Cerrar Sesión 🚪"): st.session_state.logueado = False; st.rerun()

    menu = st.tabs(["🚗 Vehículos", "📍 Ubicación", "🛡️ Panel Máster"])

    with menu[0]:
        conn = sqlite3.connect('jm_master_v4.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:250px; border-radius:10px;">
                    <h3>{a['nombre']}</h3>
                    <p>Precio: R$ {a['precio']} p/ día</p>
                </div>''', unsafe_allow_html=True)
                
                ocupadas = get_fechas_ocupadas(a['nombre'])
                
                with st.expander("📝 RESERVAR"):
                    st.write("✒️ **FIRMA DIGITAL**")
                    firma = st.text_input("Firma (Nombre Completo)", key=f"f_{a['nombre']}")
                    
                    c1, c2 = st.columns(2)
                    d_i = c1.date_input("Fecha Entrega", date.today(), key=f"di_{a['nombre']}")
                    h_e = c1.time_input("Hora Entrega", time(9,0), key=f"he_{a['nombre']}")
                    d_f = c2.date_input("Fecha Devolución", d_i + timedelta(days=1), key=f"df_{a['nombre']}")
                    h_d = c2.time_input("Hora Devolución", time(9,0), key=f"hd_{a['nombre']}")
                    
                    if d_i in ocupadas or d_f in ocupadas:
                        st.error("⚠️ Este auto ya está alquilado en esas fechas.")
                    else:
                        total_p = max((d_f - d_i).days, 1) * a['precio']
                        st.markdown(f"### Total: R$ {total_p}")
                        st.info("🏦 **PAGO PIX:** Chave: JMASOCIADOS2026")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn_{a['nombre']}"):
                            if not firma: st.error("Debe firmar")
                            else:
                                conn = sqlite3.connect('jm_master_v4.db')
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, h_entrega, h_devolucion, total) VALUES (?,?,?,?,?,?,?)",
                                             (st.session_state.u_name, a['nombre'], d_i, d_f, str(h_e), str(h_d), total_p))
                                conn.commit(); conn.close()
                                
                                st.success("✅ ¡Reserva Guardada!")
                                pdf = generar_pdf({'cliente': st.session_state.u_name, 'auto': a['nombre'], 'chapa': a['chapa'], 'inicio': d_i, 'fin': d_f, 'he': h_e, 'hd': h_d, 'total': total_p, 'firma': firma})
                                st.download_button("📥 DESCARGAR CONTRATO", pdf, f"Contrato_{a['nombre']}.pdf")
                                
                                msg = f"Reserva JM: {a['nombre']}. Cliente: {st.session_state.u_name}. R$ {total_p}"
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-wa">📤 ENVIAR COMPROBANTE</a>', unsafe_allow_html=True)

    with menu[1]:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.234567!2d-54.612345!3d-25.512345!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ0LjQiUyA1NMKwMzYnNDQuNCJX!5e0!3m2!1ses!2spy!4v1620000000000" width="100%" height="400" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

    with menu[2]:
        if st.session_state.perfil == "admin":
            st.title("Administración de Finanzas")
            conn = sqlite3.connect('jm_master_v4.db'); res = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.metric("TOTAL INGRESOS", f"R$ {res['total'].sum():,.2f}")
            st.plotly_chart(px.bar(res, x="auto", y="total", template="plotly_dark"), use_container_width=True)
            
            st.subheader("🗑️ Limpiar Historial")
            pin = st.text_input("PIN Maestro", type="password")
            if st.button("BORRAR TODO"):
                if pin == "0000":
                    conn.execute("DELETE FROM reservas"); conn.commit(); st.success("Borrado"); st.rerun()
                else: st.error("PIN Incorrecto")
            conn.close()
        else: st.warning("Acceso Admin.")