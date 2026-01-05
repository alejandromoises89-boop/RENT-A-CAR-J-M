import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, date
from fpdf import FPDF
import io

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="JM ASOCIADOS | ALQUILER DE VEHICULOS", layout="wide")

# --- 2. GESTIÓN DE ESTADOS ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'vista_login' not in st.session_state:
    st.session_state.vista_login = "inicio"
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"

# --- 3. FUNCIONES CORE ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, monto_brl REAL, estado TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS egresos 
                (id INTEGER PRIMARY KEY, tipo TEXT, monto REAL, fecha DATE, descripcion TEXT)''')
    conn.commit()
    conn.close()

def check_disponibilidad(auto, f_inicio, f_fin):
    conn = sqlite3.connect('jm_asociados.db')
    query = "SELECT * FROM reservas WHERE auto = ? AND NOT (fin < ? OR inicio > ?)"
    df = pd.read_sql_query(query, conn, params=(auto, f_inicio, f_fin))
    conn.close()
    return df.empty

def obtener_cotizacion_brl():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        return round(r.json()['rates']['PYG'])
    except: return 1450 

def generar_contrato(cliente, auto, inicio, fin, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"""
    Vehiculo: {auto}
    Arrendatario: {cliente}
    Desde: {inicio} | Hasta: {fin}
    Costo Total: R$ {total}

    El arrendatario declara recibir el vehiculo en condiciones optimas. 
    Se compromete a la devolucion en fecha y hora pactada.
    
    Firmado digitalmente por JM ASOCIADOS y el Cliente.
    """)
    return pdf.output(dest='S').encode('latin-1')

init_db()
cotizacion_hoy = obtener_cotizacion_brl()

# --- 4. DISEÑOS CSS ---
def aplicar_estilo_login():
    st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle, #4A0404 0%, #1A0000 100%); color: white; }
        .title-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 50px; font-weight: bold; text-align: center; letter-spacing: 5px; margin-bottom:0px; }
        .subtitle-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 18px; text-align: center; text-transform: uppercase; letter-spacing: 3px; }
        .stTextInput>div>div>input { background-color: rgba(255,255,255,0.05)!important; border: 1px solid #D4AF37!important; color: #D4AF37!important; }
        .stButton>button { background-color: #600000!important; color: #D4AF37!important; border: 1px solid #D4AF37!important; font-family: 'Times New Roman', serif; font-weight: bold; width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

def aplicar_estilo_app():
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #333; }
        .header-app { background-color: #4A0404; padding: 25px; color: #D4AF37; text-align: center; border-bottom: 5px solid #D4AF37; margin-bottom: 30px; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .btn-wa { background-color: #25D336; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE NAVEGACIÓN ---
if not st.session_state.autenticado:
    aplicar_estilo_login()
    st.markdown('<p class="title-jm">ACCESO A JM</p><p class="subtitle-jm">ALQUILER DE VEHÍCULOS</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("USUARIO")
        p = st.text_input("CONTRASEÑA", type="password")
        if st.button("INGRESAR"):
            if (u == "admin" and p == "2026") or (u != "" and p != ""):
                st.session_state.autenticado = True
                st.session_state.user_name = u
                st.rerun()
else:
    aplicar_estilo_app()
    st.markdown('<div class="header-app"><h1>JM ASOCIADOS - GESTIÓN</h1></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Localización", "⭐ Reseñas", "🛡️ Panel Master"])

    # TAB 1: CATALOGO Y RESERVAS
    with tabs[0]:
        st.info(f"💰 Cotización BRL/PYG: {cotizacion_hoy}")
        flota = [
             {"nombre": "Toyota Vitz 2012 (Negro)", "precio": 195, "specs": "Automático | Nafta | Económico", "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
            {"nombre": "Hyundai Tucson 2012", "precio": 260, "specs": "4x2 | Diesel | Confort", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"nombre": "Toyota Voxy 2009", "precio": 240, "specs": "Familiar | 7 Pasajeros | Amplio", "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
            {"nombre": "Toyota Vitz 2012 (Blanco)", "precio": 195, "specs": "Automático | Aire Full | Carta Verde", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
        ]
        for auto in flota:
            with st.container():
                st.markdown(f'<div class="card-auto"><h2>{auto["nombre"]}</h2><h3>R$ {auto["precio"]} / día</h3></div>', unsafe_allow_html=True)
                with st.expander(f"Agendar {auto['nombre']}"):
                    c1, c2 = st.columns(2)
                    f_i = c1.date_input("Inicio", min_value=date.today(), key=f"i_{auto['nombre']}")
                    f_f = c2.date_input("Fin", min_value=f_i, key=f"f_{auto['nombre']}")
                    if st.button(f"Verificar Disponibilidad", key=f"btn_{auto['nombre']}"):
                        if check_disponibilidad(auto['nombre'], f_i, f_f):
                            total = ((f_f - f_i).days + 1) * auto['precio']
                            st.success(f"Disponible! Total: R$ {total}")
                            conn = sqlite3.connect('jm_asociados.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_brl, estado) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.user_name, auto['nombre'], f_i, f_f, total, "Pendiente"))
                            conn.commit()
                            conn.close()
                            st.info("Reserva guardada. Descarga el contrato en la pestaña 'Mis Alquileres'")
                        else:
                            st.error("Fechas no disponibles")

    # TAB 6: MIS ALQUILERES (CONTRATOS CLIENTE)
    with tabs[1]:
        st.subheader("📋 Mis Contratos y Reservas")
        conn = sqlite3.connect('jm_asociados.db')
        df_c = pd.read_sql_query("SELECT * FROM reservas WHERE cliente = ?", conn, params=(st.session_state.user_name,))
        conn.close()
        if not df_c.empty:
            for _, row in df_c.iterrows():
                with st.expander(f"Contrato #{row['id']} - {row['auto']}"):
                    pdf_data = generar_contrato(row['cliente'], row['auto'], row['inicio'], row['fin'], row['monto_brl'])
                    st.download_button("📄 Descargar PDF", data=pdf_data, file_name=f"Contrato_JM_{row['id']}.pdf", key=f"dl_{row['id']}")
        else:
            st.info("No tienes reservas.")

    # --- TAB 7: UBICACIÓN & REDES ---
    with tabs[2]:
        col_m, col_t = st.columns([2, 1])
        with col_m:
            st.markdown("### 📍 Nuestra Oficina Principal")
            # MAPA ENFOCADO EN FARID RAHAL Y CURUPAYTY, CDE
            st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.4475475143!2d-54.6133!3d-25.5158!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzU2LjkiUyA1NMKwMzYnNDcuOSJX!5e0!3m2!1ses!2spy!4v1625678901234!5m2!1ses!2spy" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        with col_t:
            st.markdown("### 🏢 Dirección")
            st.write("**Edificio Aramí** (Frente al Edificio España)")
            st.write("Esq. Farid Rahal y Curupayty")
            st.write("Ciudad del Este, Paraguay")
            st.divider()
            st.markdown(f'''
                <a href="https://instagram.com/jymasociados" target="_blank" class="btn-notif btn-instagram">
                    <i class="fa-brands fa-instagram btn-icon"></i> Instagram Oficial
                </a>
                <a href="https://wa.me/595991681191" target="_blank" class="btn-notif btn-whatsapp">
                    <i class="fa-brands fa-whatsapp btn-icon"></i> Contacto WhatsApp
                </a>
            ''', unsafe_allow_html=True)

    # --- TAB 8: RESEÑAS ---
    with tabs[3]:
        st.subheader("⭐ Danos tu Calificación")
        with st.form("form_resena"):
            coment = st.text_area("¿Qué le pareció nuestro servicio?")
            estrellas = st.select_slider("Calificación", options=[1, 2, 3, 4, 5], value=5)
            if st.form_submit_button("Publicar Comentario"):
                conn = sqlite3.connect('jm_asociados.db')
                conn.cursor().execute("INSERT INTO resenas (cliente, comentario, estrellas, fecha) VALUES (?,?,?,?)",
                                     (st.session_state.user_name, coment, estrellas, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("¡Gracias por ayudarnos a mejorar!")

    # TAB 9: PANEL MASTER (ADMIN)
    with tabs[4]:
        if st.text_input("PIN Maestro", type="password") == "2026":
            conn = sqlite3.connect('jm_asociados.db')
            df_all = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.subheader("📅 Todas las Reservas (Control de Conflictos)")
            st.dataframe(df_all, use_container_width=True)
            
            if not df_all.empty:
                sel = st.selectbox("Contrato a descargar", df_all['id'])
                r = df_all[df_all['id'] == sel].iloc[0]
                pdf_m = generar_contrato(r['cliente'], r['auto'], r['inicio'], r['fin'], r['monto_brl'])
                st.download_button("📥 Descargar Copia Admin", pdf_m, f"Admin_JM_{sel}.pdf")
            
            # Estadísticas
            df_eg = pd.read_sql_query("SELECT * FROM egresos", conn)
            st.metric("UTILIDAD NETA", f"R$ {df_all['monto_brl'].sum() - df_eg['monto'].sum()}")
            conn.close()

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
