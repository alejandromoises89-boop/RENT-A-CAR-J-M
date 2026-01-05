import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTÉTICA ELEGANTE ---
st.set_page_config(page_title="JM ALQUILER", layout="wide")

st.markdown("""
<style>
    /* Fondo Degradé Bordo Elegante */
    .stApp {
        background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%);
        color: #D4AF37;
    }
    
    /* Textos y Etiquetas en Dorado Fino */
    h1, h2, h3, p, label, .stMarkdown {
        color: #D4AF37 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Entradas de datos simplificadas */
    input, textarea, [data-baseweb="select"], [data-baseweb="input"] {
        background-color: rgba(0,0,0,0.5) !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }

    /* Botones Negros con letras Doradas (Sin efectos de resaltado) */
    .stButton>button {
        background-color: #000000 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 5px;
        transition: none !important; /* Quita el resaltado al clic */
    }
    
    .stButton>button:active, .stButton>button:focus {
        background-color: #000000 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }

    .card-auto {
        background-color: rgba(0,0,0,0.3);
        padding: 15px;
        border-left: 3px solid #D4AF37;
        margin-bottom: 15px;
    }

    .btn-contact {
        display: block;
        width: 100%;
        padding: 10px;
        text-align: center;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 10px;
        border: 1px solid #D4AF37;
    }
    .wa { background-color: #25D366; color: white !important; }
    .ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE PERSISTENCIA Y DATOS ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_name' not in st.session_state: st.session_state.u_name = ""

def init_db():
    conn = sqlite3.connect('jm_final_elegant.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, h_entrega TEXT, h_devolucion TEXT, total REAL, contrato_blob BLOB)')
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

# --- 3. FUNCIONES DE NEGOCIO ---
def generar_pdf_silent(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO ARRENDAMIENTO JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, f"Cliente: {d['cliente']}\nAuto: {d['auto']}\nPlazo: {d['inicio']} al {d['fin']}\nTotal: R$ {d['total']}\n\nFirma: {d['firma']}")
    return pdf.output(dest='S').encode('latin-1')

def get_bloqueos(auto):
    conn = sqlite3.connect('jm_final_elegant.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueos = set()
    for _, r in df.iterrows():
        start = datetime.strptime(r['inicio'], '%Y-%m-%d').date()
        end = datetime.strptime(r['fin'], '%Y-%m-%d').date()
        while start <= end:
            bloqueos.add(start)
            start += timedelta(days=1)
    return bloqueos

# --- 4. ACCESO ---
if not st.session_state.logueado:
    st.markdown("<h2 style='text-align:center;'>Acceso JM</h2>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size:60px;'>🔒</h1>", unsafe_allow_html=True)
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        st.session_state.logueado = True; st.session_state.u_name = user; st.rerun()
    st.button("Crear cuenta")
    st.button("Olvidé mi contraseña")
else:
    # --- APP PRINCIPAL ---
    st.markdown("<h2 style='text-align:center;'>JM ALQUILER DE VEHÍCULOS</h2>", unsafe_allow_html=True)
    if st.sidebar.button("Cerrar Sesión"): st.session_state.logueado = False; st.rerun()

    menu = st.tabs(["🚗 Flota", "📍 Ubicación", "🛡️ Admin"])

    with menu[0]:
        conn = sqlite3.connect('jm_final_elegant.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <h4>{a['nombre']}</h4>
                    <p>Precio: R$ {a['precio']} / día</p>
                </div>''', unsafe_allow_html=True)
                
                bloq = get_bloqueos(a['nombre'])
                with st.expander("RESERVAR"):
                    firma = st.text_input("Firma Digital (Nombre Completo)", key=f"f_{a['nombre']}")
                    c1, c2 = st.columns(2)
                    d_i = c1.date_input("Entrega", date.today(), key=f"di_{a['nombre']}")
                    h_e = c1.time_input("Hora", time(9,0), key=f"he_{a['nombre']}")
                    d_f = c2.date_input("Devolución", d_i + timedelta(days=1), key=f"df_{a['nombre']}")
                    h_d = c2.time_input("Hora", time(9,0), key=f"hd_{a['nombre']}")
                    
                    if d_i in bloq or d_f in bloq:
                        st.error("⚠️ Fechas no disponibles.")
                    else:
                        total = max((d_f - d_i).days, 1) * a['precio']
                        st.write(f"### Total: R$ {total}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn_{a['nombre']}"):
                            if not firma: st.error("Firme para continuar")
                            else:
                                # Generar y Guardar automáticamente
                                pdf = generar_pdf_silent({'cliente':st.session_state.u_name,'auto':a['nombre'],'inicio':d_i,'fin':d_f,'total':total,'firma':firma})
                                conn = sqlite3.connect('jm_final_elegant.db')
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, h_entrega, h_devolucion, total, contrato_blob) VALUES (?,?,?,?,?,?,?,?)",
                                             (st.session_state.u_name, a['nombre'], d_i, d_f, str(h_e), str(h_d), total, pdf))
                                conn.commit(); conn.close()
                                
                                st.success("✅ Reserva registrada automáticamente.")
                                wa_msg = f"Reserva JM: {a['nombre']}. Cliente: {st.session_state.u_name}. R$ {total}"
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(wa_msg)}" class="btn-contact wa">📤 ENVIAR COMPROBANTE WHATSAPP</a>', unsafe_allow_html=True)

    with menu[1]:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.234567!2d-54.612345!3d-25.512345!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ0LjQiUyA1NMKwMzYnNDQuNCJX!5e0!3m2!1ses!2spy!4v1620000000000" width="100%" height="300" style="border:1px solid #D4AF37;"></iframe>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-contact wa">💬 WhatsApp Corporativo</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-contact ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)

    with menu[2]:
        if st.session_state.u_name == "admin":
            st.write("📊 Panel Administrativo")
            pin = st.text_input("PIN Maestro", type="password")
            if st.button("Limpiar Registros"):
                if pin == "0000":
                    conn = sqlite3.connect('jm_final_elegant.db'); conn.execute("DELETE FROM reservas"); conn.commit(); conn.close()
                    st.success("Borrado"); st.rerun()
        else: st.warning("Solo Administrador")
