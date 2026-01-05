import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN, ESTÉTICA Y DISEÑO ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%);
        color: #D4AF37;
    }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    
    /* Inputs en Negro/Transparente con borde Dorado */
    input, textarea, [data-baseweb="select"], [data-baseweb="input"] {
        background-color: rgba(0,0,0,0.7) !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }

    /* Botones Negros con Letras Doradas (Sin efectos de resaltado bruscos) */
    .stButton>button {
        background-color: #000000 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 5px;
    }

    .card-auto {
        background-color: rgba(0,0,0,0.4);
        padding: 20px;
        border-left: 4px solid #D4AF37;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    .btn-contact {
        display: block; width: 100%; padding: 10px; text-align: center;
        border-radius: 5px; text-decoration: none; font-weight: bold;
        margin-top: 10px; border: 1px solid #D4AF37;
    }
    .wa { background-color: #25D366; color: white !important; }
    .ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS E INICIALIZACIÓN ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_name' not in st.session_state: st.session_state.u_name = ""
if 'pagina' not in st.session_state: st.session_state.pagina = "login"

def init_db():
    conn = sqlite3.connect('jm_final_unificado.db')
    c = conn.cursor()
    # Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios_jm 
                 (nombre TEXT, celular TEXT, direccion TEXT, correo TEXT PRIMARY KEY, 
                  documento TEXT, password TEXT)''')
    # Reservas con Contrato guardado (BLOB)
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, 
                  h_entrega TEXT, h_devolucion TEXT, total REAL, contrato_blob BLOB)''')
    # Flota
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, chapa TEXT, chasis TEXT, precio REAL, img TEXT)')
    
    autos = [
        ("Hyundai Tucson", "AA-123", "TUC-7721", 260.0, "https://images.dealer.com/ddc/vehicles/2022/Hyundai/Tucson/SUV/perspective/front-left/2022_24.png"),
        ("Toyota Vitz Blanco", "BCC-445", "VTZ-001", 195.0, "https://vhr.com.py/wp-content/uploads/2021/04/VITZ-BLANCO.png"),
        ("Toyota Vitz Negro", "XAM-990", "VTZ-998", 195.0, "https://vhr.com.py/wp-content/uploads/2021/04/VITZ-NEGRO.png"),
        ("Toyota Voxy", "HHP-112", "VOX-556", 240.0, "https://www.toyota.com.py/storage/modelos/voxy/voxy_perla.png")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- 3. FUNCIONES DE APOYO ---
def generar_pdf_blob(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, f"Cliente: {d['cliente']}\nVehiculo: {d['auto']}\nChapa: {d['chapa']}\nPeriodo: {d['inicio']} al {d['fin']}\nTotal: R$ {d['total']}\n\nFirma Digital Registrada: {d['firma']}")
    return pdf.output(dest='S').encode('latin-1')

def get_fechas_bloqueadas(auto):
    conn = sqlite3.connect('jm_final_unificado.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, r in df.iterrows():
        start = datetime.strptime(r['inicio'], '%Y-%m-%d').date()
        end = datetime.strptime(r['fin'], '%Y-%m-%d').date()
        while start <= end:
            bloqueadas.add(start); start += timedelta(days=1)
    return bloqueadas

# --- 4. INTERFAZ DE ACCESO (LOGIN / REGISTRO) ---
if not st.session_state.logueado:
    if st.session_state.pagina == "login":
        st.markdown("<h2 style='text-align:center;'>Acceso JM</h2>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; font-size:60px;'>🔒</h1>", unsafe_allow_html=True)
        email = st.text_input("Correo")
        pw = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if email == "admin@jm.com" and pw == "8899":
                st.session_state.logueado = True; st.session_state.u_name = "admin"; st.rerun()
            else:
                conn = sqlite3.connect('jm_final_unificado.db')
                user = conn.execute("SELECT nombre FROM usuarios_jm WHERE correo=? AND password=?", (email, pw)).fetchone()
                conn.close()
                if user:
                    st.session_state.logueado = True; st.session_state.u_name = user[0]; st.rerun()
                else: st.error("Datos incorrectos")
        
        c1, c2, c3 = st.columns(3)
        if c1.button("Crear Cuenta"): st.session_state.pagina = "registro"; st.rerun()
        if c2.button("Olvidé mi contraseña"): st.session_state.pagina = "recuperar"; st.rerun()
        if c3.button("🔑 Biometría"): st.info("Escaneando FaceID/Huella...")

    elif st.session_state.pagina == "registro":
        st.markdown("### Registro de Nuevo Cliente")
        with st.form("reg_form"):
            n = st.text_input("Nombre Completo"); cel = st.text_input("Celular"); dir = st.text_input("Dirección")
            em = st.text_input("Correo"); doc = st.text_input("Documento (CPF/RG/CI/Pasaporte)"); psw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Guardar para Siempre"):
                conn = sqlite3.connect('jm_final_unificado.db')
                conn.execute("INSERT INTO usuarios_jm VALUES (?,?,?,?,?,?)", (n, cel, dir, em, doc, psw))
                conn.commit(); conn.close()
                st.success("¡Registrado!"); st.session_state.pagina = "login"; st.rerun()
        if st.button("Volver"): st.session_state.pagina = "login"; st.rerun()

    elif st.session_state.pagina == "recuperar":
        st.markdown("### Recuperar Acceso")
        m = st.text_input("Correo registrado")
        if st.button("Enviar enlace"): st.success(f"Enlace enviado a {m}"); st.session_state.pagina = "login"; st.rerun()

# --- 5. APLICACIÓN PRINCIPAL ---
else:
    st.markdown("<h2 style='text-align:center;'>JM ALQUILER DE VEHÍCULOS</h2>", unsafe_allow_html=True)
    if st.sidebar.button("Cerrar Sesión"): st.session_state.logueado = False; st.session_state.pagina = "login"; st.rerun()

    tabs = st.tabs(["🚗 Flota", "📍 Ubicación", "🛡️ Admin Máster"])

    # --- TABS FLOTA ---
    with tabs[0]:
        conn = sqlite3.connect('jm_final_unificado.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:350px; border-radius:10px; border:1px solid #D4AF37;">
                    <h3>{a['nombre']}</h3>
                    <p>Precio: R$ {a['precio']} / día | Chapa: {a['chapa']}</p>
                </div>''', unsafe_allow_html=True)
                
                bloq = get_fechas_bloqueadas(a['nombre'])
                with st.expander("RESERVAR VEHÍCULO"):
                    firma = st.text_input("Firma Digital (Nombre Completo)", key=f"f_{a['nombre']}")
                    c1, c2 = st.columns(2)
                    d_i = c1.date_input("Entrega", date.today(), key=f"di_{a['nombre']}")
                    h_e = c1.time_input("Hora", time(9,0), key=f"he_{a['nombre']}")
                    d_f = c2.date_input("Devolución", d_i + timedelta(days=1), key=f"df_{a['nombre']}")
                    h_d = c2.time_input("Hora", time(9,0), key=f"hd_{a['nombre']}")
                    
                    if d_i in bloq or d_f in bloq:
                        st.error("⚠️ Fechas ya reservadas.")
                    else:
                        total = max((d_f - d_i).days, 1) * a['precio']
                        st.write(f"### Total: R$ {total}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn_{a['nombre']}"):
                            if not firma: st.error("Debe firmar")
                            else:
                                pdf = generar_pdf_blob({'cliente':st.session_state.u_name,'auto':a['nombre'],'chapa':a['chapa'],'inicio':d_i,'fin':d_f,'total':total,'firma':firma})
                                conn = sqlite3.connect('jm_final_unificado.db')
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, h_entrega, h_devolucion, total, contrato_blob) VALUES (?,?,?,?,?,?,?,?)",
                                             (st.session_state.u_name, a['nombre'], d_i, d_f, str(h_e), str(h_d), total, pdf))
                                conn.commit(); conn.close()
                                st.success("✅ Reserva y Contrato guardados.")
                                msg = f"Reserva JM: {a['nombre']} - R$ {total}"
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-contact wa">📤 ENVIAR COMPROBANTE WHATSAPP</a>', unsafe_allow_html=True)

    # --- TAB UBICACIÓN ---
    with tabs[1]:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.23456789!2d-54.611111!3d-25.511111!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQwLjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1234567890" width="100%" height="400" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-contact wa">💬 WhatsApp Corporativo</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-contact ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)

    # --- TAB ADMIN (CONTRATOS) ---
    with tabs[2]:
        if st.session_state.u_name == "admin":
            st.markdown("### 🛡️ PANEL MÁSTER Y CONTRATOS")
            conn = sqlite3.connect('jm_final_unificado.db')
            df_r = pd.read_sql_query("SELECT id, cliente, auto, inicio, fin, total, contrato_blob FROM reservas", conn)
            conn.close()
            
            for _, r in df_r.iterrows():
                with st.container():
                    c_i, c_b = st.columns([3,1])
                    c_i.write(f"**Cliente:** {r['cliente']} | **Auto:** {r['auto']} | **Total:** R$ {r['total']}")
                    if r['contrato_blob']:
                        c_b.download_button("📄 Contrato", r['contrato_blob'], f"Contrato_{r['id']}.pdf", "application/pdf", key=f"dl_{r['id']}")
                st.divider()

            pin = st.text_input("PIN Maestro", type="password")
            if st.button("LIMPIAR REGISTROS"):
                if pin == "0000":
                    conn = sqlite3.connect('jm_final_unificado.db'); conn.execute("DELETE FROM reservas"); conn.commit(); conn.close()
                    st.success("Historial borrado"); st.rerun()
        else: st.warning("Acceso exclusivo Admin.")