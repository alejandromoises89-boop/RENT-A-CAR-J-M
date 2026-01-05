import streamlit as st
import sqlite3
import pandas as pd
import base64
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E IDENTIDAD VISUAL ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA OFICIAL", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; padding: 15px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 60px; margin-bottom: 0; }
        .header-jm p { color: #D4AF37; font-size: 20px; font-style: italic; }
        
        /* Inputs Dorados */
        .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; background-color: rgba(255,255,255,0.1) !important; color: white !important; border-radius: 10px !important; }
        
        /* Botones Bordó Destacados */
        div.stButton > button { 
            background-color: #800000 !important; color: #D4AF37 !important; 
            border: 2px solid #D4AF37 !important; font-weight: bold; 
            width: 100%; border-radius: 15px; height: 50px; font-size: 18px;
        }
        
        /* Pestañas Blancas */
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
        .stTabs [data-baseweb="tab"]:hover { border-bottom: 4px solid #800000 !important; }
        
        /* Cards de Autos */
        .card-auto { background: white; color: black; padding: 15px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 20px; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA DE BLOQUEO ---
def init_db():
    conn = sqlite3.connect('jm_final_v8.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, chapa TEXT, chasis TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini DATE, f_fin DATE, cliente TEXT, monto REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, password TEXT, nombre TEXT)''')
    
    # Datos iniciales si la flota está vacía
    if c.execute("SELECT count(*) FROM flota").fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
            ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
            ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chapa, chasis) VALUES (?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def verificar_disponibilidad(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_final_v8.db')
    # Lógica: No debe haber ninguna reserva donde las fechas se crucen
    query = "SELECT * FROM reservas WHERE auto_id = ? AND NOT (f_fin < ? OR f_ini > ?)"
    res = conn.execute(query, (auto_id, f_ini, f_fin)).fetchone()
    conn.close()
    return res is None

# --- 3. FLUJO DE LOGIN (PANTALLA ÚNICA) ---
init_db()
aplicar_estilos_premium()

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ACCESO AL SISTEMA</p></div>', unsafe_allow_html=True)
    
    tab_login, tab_reg, tab_pass = st.tabs(["ENTRAR", "CREAR CUENTA", "RECUPERAR"])
    
    with tab_login:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            u = st.text_input("Correo o Teléfono", key="login_user")
            p = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("ENTRAR AL SISTEMA"):
                if u == "admin" and p == "admin123":
                    st.session_state.autenticado = True
                    st.session_state.user = "Admin"
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    conn = sqlite3.connect('jm_final_v8.db')
                    res = conn.execute("SELECT nombre FROM usuarios WHERE user=? AND password=?", (u, p)).fetchone()
                    if res:
                        st.session_state.autenticado = True
                        st.session_state.user = res[0]
                        st.session_state.role = "user"
                        st.rerun()
                    else:
                        st.error("Credenciales Inválidas")

    with tab_reg:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            new_u = st.text_input("Nro de Teléfono (Usuario)")
            new_n = st.text_input("Nombre y Apellido")
            new_p = st.text_input("Crear Contraseña", type="password")
            if st.button("REGISTRAR MI CUENTA"):
                conn = sqlite3.connect('jm_final_v8.db')
                try:
                    conn.execute("INSERT INTO usuarios VALUES (?,?,?)", (new_u, new_p, new_n))
                    conn.commit()
                    st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                except:
                    st.error("Este usuario ya existe.")

    with tab_pass:
        st.info("Para recuperar su acceso, contacte con la administración de JM Asociados.")
        st.markdown('<a href="https://wa.me/595991681191" class="btn-social" style="background:#25D366; color:white; padding:10px; border-radius:10px; text-decoration:none;">📲 WhatsApp Soporte</a>', unsafe_allow_html=True)

else:
    # --- 4. SISTEMA PRINCIPAL (POST-LOGIN) ---
    with st.sidebar:
        st.markdown(f"### Bienvenido\n**{st.session_state.user}**")
        st.divider()
        if st.button("CERRAR SESIÓN"):
            st.session_state.autenticado = False
            st.rerun()

    st.markdown('<div class="header-jm"><h1>JM ASOCIADOS</h1></div>', unsafe_allow_html=True)
    
    menu = ["🚗 Catálogo", "⭐ Reseñas", "📍 Ubicación"]
    if st.session_state.role == "admin":
        menu.append("🛡️ Panel de Control")
    
    tabs = st.tabs(menu)

    with tabs[0]: # CATÁLOGO CON BLOQUEO DINÁMICO
        st.subheader("Vehículos Disponibles")
        conn = sqlite3.connect('jm_final_v8.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn)
        
        for i, r in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="card-auto">
                    <img src="{r['img']}" width="150" style="float:right; border-radius:10px;">
                    <h3>{r['nombre']}</h3>
                    <p><b>Chapa:</b> {r['chapa']} | <b>Precio:</b> R$ {r['precio_brl']}</p>
                    <p><b>Gs. {r['precio_brl']*1450:,.0f} por día</b></p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"Verificar disponibilidad de {r['nombre']}"):
                    c1, c2 = st.columns(2)
                    f_ini = c1.date_input("Fecha Entrega", key=f"f1_{i}")
                    f_fin = c2.date_input("Fecha Devolución", key=f"f2_{i}")
                    
                    if verificar_disponibilidad(r['id'], f_ini, f_fin):
                        st.success("✅ Disponible para estas fechas.")
                        if st.button(f"Confirmar Reserva {r['nombre']}", key=f"btn_{i}"):
                            dias = max((f_fin - f_ini).days, 1)
                            total = dias * r['precio_brl']
                            conn.execute("INSERT INTO reservas (auto_id, f_ini, f_fin, cliente, monto) VALUES (?,?,?,?,?)", 
                                         (r['id'], f_ini, f_fin, st.session_state.user, total))
                            conn.commit()
                            st.balloons()
                            st.success(f"Reserva realizada con éxito por R$ {total}")
                    else:
                        st.error("❌ Ocupado. Por favor elija otras fechas u otro vehículo.")

    with tabs[1]: # RESEÑAS
        st.subheader("Muro de Clientes")
        comentario = st.text_area("Escriba su experiencia:")
        if st.button("Publicar Comentario"):
            st.success("Gracias por su comentario. Se ha publicado correctamente.")

    with tabs[2]: # UBICACIÓN
        st.subheader("Encuéntranos en Google Maps")
        # Link directo de Embed para evitar errores de API Key
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.5!2d-54.6!3d-25.5!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzAwLjAiUyA1NMKwMzYnMDAuMCJX!5e0!3m2!1ses!2spy!4v1611111111111" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[3]: # PANEL ADMIN
            st.subheader("Gestión de Finanzas y Reservas")
            pin = st.text_input("Ingrese PIN Administrativo", type="password")
            if pin == "1234":
                conn = sqlite3.connect('jm_final_v8.db')
                res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
                st.write("### Listado de Alquileres Activos")
                st.dataframe(res_df)
                st.metric("INGRESOS TOTALES RECAUDADOS", f"R$ {res_df['monto'].sum():,.2f}")
                
                if st.button("Limpiar historial de reservas"):
                    conn.execute("DELETE FROM reservas")
                    conn.commit()
                    st.rerun()
            else:
                st.warning("Ingrese el PIN correcto para ver finanzas.")
