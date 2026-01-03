import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
from datetime import datetime
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
    .header-jm { text-align: center; color: #D4AF37; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: black !important; }
    .stMetric { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; border: 1px solid #D4AF37; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS REFORZADA ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    # Tabla de Reservas
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto REAL)''')
    # Tabla de Comentarios
    c.execute('''CREATE TABLE IF NOT EXISTS comentarios 
                 (id INTEGER PRIMARY KEY, usuario TEXT, mensaje TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

def verificar_choque_fechas(auto, inicio, fin):
    conn = sqlite3.connect('jm_asociados.db')
    query = f"SELECT * FROM reservas WHERE auto = '{auto}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    nuevo_inicio = pd.to_datetime(inicio)
    nuevo_fin = pd.to_datetime(fin)
    
    for _, row in df.iterrows():
        existente_inicio = pd.to_datetime(row['inicio'])
        existente_fin = pd.to_datetime(row['fin'])
        # Lógica de choque: (InicioA <= FinB) AND (FinA >= InicioB)
        if (nuevo_inicio <= existente_fin) and (nuevo_fin >= existente_inicio):
            return False # Hay choque
    return True # Disponible

def guardar_reserva(cliente, auto, inicio, fin, monto):
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto) VALUES (?,?,?,?,?)",
              (cliente, auto, str(inicio), str(fin), monto))
    conn.commit()
    conn.close()

# --- 3. FUNCIONES DE INTERFAZ ---
def obtener_flota():
    return [
        {"id": "TUCSON", "nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260000, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
        {"id": "VITZ_W", "nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
        {"id": "VITZ_N", "nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
        {"id": "VOXY", "nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
    ]

# --- 4. LÓGICA DE NAVEGACIÓN ---
init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if user == "admin@jymasociados.com" and pw == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", user
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1></div>', unsafe_allow_html=True)
    
    # PESTAÑAS
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "💬 Comentarios", "⚙️ Panel Master"])

    with tabs[0]: # CATALOGO CON BLOQUEO
        for auto in obtener_flota():
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} - {auto['color']}")
                f1 = st.date_input("Inicio", key=f"i_{auto['id']}")
                f2 = st.date_input("Fin", key=f"f_{auto['id']}")
                if st.button(f"Reservar {auto['id']}", key=f"b_{auto['id']}"):
                    if verificar_choque_fechas(auto['nombre'], f1, f2):
                        guardar_reserva(st.session_state.user_name, auto['nombre'], f1, f2, auto['precio'])
                        st.success("✅ Disponible. Generando Contrato...")
                        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_24510861818")
                    else:
                        st.error("❌ Este vehículo ya está reservado en esas fechas.")

    with tabs[1]: # MI HISTORIAL
        st.subheader("Mis Alquileres")
        conn = sqlite3.connect('jm_asociados.db')
        df_h = pd.read_sql_query(f"SELECT * FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        st.table(df_h)
        conn.close()

    with tabs[2]: # COMENTARIOS
        st.subheader("Tu opinión nos importa")
        msg = st.text_area("Deja tu reseña:")
        if st.button("Enviar Comentario"):
            conn = sqlite3.connect('jm_asociados.db')
            conn.cursor().execute("INSERT INTO comentarios (usuario, mensaje, fecha) VALUES (?,?,?)", 
                                 (st.session_state.user_name, msg, str(datetime.now())))
            conn.commit()
            conn.close()
            st.success("Gracias por tu comentario.")

    with tabs[3]: # PANEL MASTER (ESTADISTICAS)
        if st.session_state.role == "admin":
            st.title("Estadísticas Reales")
            conn = sqlite3.connect('jm_asociados.db')
            df_m = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_c = pd.read_sql_query("SELECT * FROM comentarios", conn)
            
            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Ingresos Totales", f"Gs. {df_m['monto'].sum():,}")
            m2.metric("Total Reservas",
