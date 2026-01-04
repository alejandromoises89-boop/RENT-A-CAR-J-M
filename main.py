import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")

# --- 2. GESTIÓN DE ESTADO (BLINDAJE) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- 3. ESTILO CSS "ROMANO DORADO" ---
st.markdown("""
<style>
    /* Fondo Degradado Bordó profundo */
    .stApp {
        background: radial-gradient(circle, #4A0404 0%, #1A0000 100%);
    }

    /* Encabezado Principal */
    .header-container {
        text-align: center;
        margin-bottom: 30px;
    }
    .title-jm {
        font-family: 'Times New Roman', Times, serif;
        color: #D4AF37;
        font-size: 55px;
        font-weight: bold;
        letter-spacing: 5px;
        margin-bottom: 0px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
    }
    .subtitle-jm {
        font-family: 'Times New Roman', Times, serif;
        color: #D4AF37;
        font-size: 22px;
        letter-spacing: 3px;
        margin-top: -10px;
    }

    /* Candado y Cuadros Dorados */
    .lock-style {
        font-size: 50px;
        color: #D4AF37;
        text-align: center;
        margin: 20px 0;
    }

    /* Inputs con bordes dorados finos */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #D4AF37 !important;
        color: #D4AF37 !important;
        border-radius: 4px !important;
        font-family: 'Times New Roman', serif;
    }

    /* Botón ENTRAR Bordó destacado */
    .stButton>button {
        background-color: #600000 !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
        font-family: 'Times New Roman', serif;
        font-weight: bold !important;
        font-size: 20px !important;
        width: 100%;
        border-radius: 5px !important;
    }

    /* Estilo de Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Times New Roman', serif;
        color: #D4AF37 !important;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. PANTALLA DE LOGIN ---
def mostrar_login():
    st.markdown("""
        <div class="header-container">
            <p class="title-jm">ACCESO A J&M</p>
            <p class="subtitle-jm">ALQUILER DE VEHÍCULOS</p>
        </div>
        <div class="lock-style">🔒</div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_prestige"):
            user = st.text_input("USUARIO / TELÉFONO")
            pw = st.text_input("CONTRASEÑA", type="password")
            btn_login = st.form_submit_button("ENTRAR")

            if btn_login:
                if user == "admin" and pw == "2026":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Credenciales Incorrectas")

# --- 5. APLICACIÓN PRINCIPAL (POST-LOGIN) ---
def mostrar_app():
    st.markdown('<p class="title-jm" style="font-size:35px;">J&M ASOCIADOS</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚗 CATÁLOGO", "📜 HISTORIAL", "💬 RESEÑAS", "🛡️ PANEL CONTROL"])

    with tab1:
        st.markdown('<p style="color:#D4AF37; font-family:serif;">Seleccione su flota de alta gama</p>', unsafe_allow_html=True)
        # Aquí va la lógica de los cuadros blancos de los autos
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
                <div style="background:white; padding:20px; border-radius:10px; color:black; text-align:center;">
                    <img src="https://i.ibb.co/Y7ZHY8kX/pngegg.png" width="250">
                    <h3>Toyota Vitz 2012</h3>
                    <p>US$ 30 / día | Seguro Internacional | ABS</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Reservar Vitz"):
                st.success("Redirigiendo a Pago PIX...")

    with tab4:
        st.header("Análisis FODA y Finanzas")
        if st.checkbox("Ver Estadísticas Diarias"):
            df = pd.DataFrame({"Día": ["Lun", "Mar", "Mie"], "Ingresos": [1500, 2200, 1800]})
            fig = px.bar(df, x="Día", y="Ingresos", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig)
            
        if st.button("Exportar Reporte Anual PDF"):
            st.info("Generando diapositiva expositoria...")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. EJECUCIÓN LÓGICA ---
if not st.session_state.autenticado:
    mostrar_login()
else:
    mostrar_app()

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL, fecha_registro TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    conn.commit()
    conn.close()

def obtener_cotizacion_brl():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        return round(r.json()['rates']['PYG'])
    except: return 1450 

cotizacion_hoy = obtener_cotizacion_brl()
init_db()

# --- 3. FLOTA (ORDEN Y LINKS VERIFICADOS) ---
flota = [
    {"nombre": "Toyota Vitz", "color": "Negro", "precio_brl": 195, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio_brl": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio_brl": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio_brl": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. INTERFAZ ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">ACCESO PRIVADO</div>', unsafe_allow_html=True)
    u = st.text_input("Usuario / Correo")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR AL PORTAL"):
        if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
            st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
        else:
            st.session_state.role, st.session_state.user_name = "user", u
        st.session_state.logged_in = True
        st.rerun()
else:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">Alquiler de Vehículos</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cotizacion-texto">Cotización del día: 1 Real = {cotizacion_hoy:,} PYG</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación & Redes", "⭐ Reseñas", "⚙️ Panel Master"] if st.session_state.role == "admin" else ["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación & Redes", "⭐ Reseñas"])

    # --- TAB 1: CATALOGO ---
    with tabs[0]:
        for idx, auto in enumerate(flota):
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1: st.image(auto['img'], use_container_width=True)
                with c2:
                    st.subheader(f"{auto['nombre']} {auto['color']}")
                    st.write(f"Tarifa Diaria: **{auto['precio_brl']} BRL** (Gs. {monto_pyg:,})")
                    if st.button("Solicitar Reserva", key=f"cat_{idx}"):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_pyg, monto_brl, fecha_registro) VALUES (?,?,?,?,?,?,?)",
                                             (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", "Pendiente", "Pendiente", monto_pyg, auto['precio_brl'], datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("✅ Solicitud enviada. Verifique en 'Mi Historial'")
                st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: MI HISTORIAL ---
    with tabs[1]:
        st.subheader(f"Mis Alquileres: {st.session_state.user_name}")
        conn = sqlite3.connect('jm_asociados.db')
        df_mine = pd.read_sql_query(f"SELECT auto, inicio, fin, monto_brl, fecha_registro FROM reservas WHERE cliente = '{st.session_state.user_name}'", conn)
        st.dataframe(df_mine, use_container_width=True)
        conn.close()

    # --- TAB 3: UBICACIÓN & REDES ---
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

    # --- TAB 4: RESEÑAS ---
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

   # --- TAB 5: PANEL MASTER (SOLO ADMIN) ---
    if st.session_state.role == "admin":
        with tabs[4]:
            st.title("⚙️ Administración Central")
            conn = sqlite3.connect('jm_asociados.db')
            
            # --- 1. MÉTRICAS Y GRÁFICOS ---
            df_all = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_re = pd.read_sql_query("SELECT * FROM resenas", conn)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Ingresos Totales (BRL)", f"{df_all['monto_brl'].sum():,} BRL")
                st.write("Popularidad de la Flota")
                st.bar_chart(df_all['auto'].value_counts())
            with c2:
                st.write("Últimas Reseñas Recibidas")
                st.dataframe(df_re[['cliente', 'comentario', 'estrellas']].tail(5), use_container_width=True)
            
            st.divider()

            # --- 2. GESTIÓN DE REGISTROS (BORRADO DE PRUEBAS) ---
            st.subheader("🗑️ Gestión de Alquileres")
            st.write("Utilice esta opción para limpiar las pruebas antes de la exposición.")
            
            if not df_all.empty:
                st.dataframe(df_all, use_container_width=True) # Mostrar tabla completa
                
                # Botón de borrado masivo
                if st.button("BORRAR TODOS LOS ALQUILERES (Limpiar Pruebas)"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM reservas")
                    conn.commit()
                    st.warning("⚠️ Todos los registros de alquiler han sido eliminados.")
                    st.rerun()
            else:
                st.info("No hay alquileres registrados actualmente.")

            st.divider()
            
            # --- 3. EXPORTACIÓN ---
            st.write("Exportar reporte para balance de metas:")
            st.download_button("📥 Descargar Excel (CSV)", df_all.to_csv(index=False).encode('utf-8'), "reporte_jm_final.csv")
            
            conn.close()


