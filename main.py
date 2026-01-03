import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
import requests
from datetime import datetime
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

# Importar Font Awesome para los iconos
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

def obtener_cotizacion_brl():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/BRL"
        response = requests.get(url)
        return round(response.json()['rates']['PYG'])
    except:
        return 1450 

cotizacion_hoy = obtener_cotizacion_brl()

st.markdown(f"""
<style>
    .stApp {{ background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }}
    .header-jm {{ text-align: center; color: #D4AF37; margin-bottom: 20px; }}
    .card-auto {{ background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; }}
    
    /* Estilo para Botones Personalizados */
    .btn-notif {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 12px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        font-size: 16px;
        margin-top: 10px;
        transition: transform 0.2s, opacity 0.2s;
        border: none;
        width: 100%;
        cursor: pointer;
    }}
    .btn-notif:hover {{ transform: scale(1.02); opacity: 0.9; color: white !important; }}
    .btn-whatsapp {{ background-color: #25D366; color: white !important; }}
    .btn-email {{ background-color: #D4AF37; color: black !important; }}
    .btn-icon {{ margin-right: 10px; font-size: 20px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. LOGICA DE NEGOCIO ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL)''')
    conn.commit()
    conn.close()

flota = [
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio_brl": 260, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio_brl": 195, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Vitz", "color": "Negro", "precio_brl": 195, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio_brl": 240, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. INTERFAZ ---
if not st.session_state.logged_in:
    # Bloque de Login (Simplificado para brevedad, mantener tu logica actual)
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", u
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "⚙️ Panel Master"])

    with tabs[0]:
        for auto in flota:
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            st.markdown(f'<div class="card-auto">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} ({auto['color']})")
                st.write(f"💳 **Precio:** {auto['precio_brl']} Reales / día (aprox Gs. {monto_pyg:,})")
                
                f_ini = st.date_input("Inicio", key=f"i_{auto['nombre']}_{auto['color']}")
                f_fin = st.date_input("Fin", key=f"f_{auto['nombre']}_{auto['color']}")
                
                if st.button("Alquilar", key=f"btn_{auto['nombre']}_{auto['color']}"):
                    conn = sqlite3.connect('jm_asociados.db')
                    conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_pyg, monto_brl) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", str(f_ini), str(f_fin), monto_pyg, auto['precio_brl']))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Vehículo Reservado")
                    
                    # Mensajes personalizados
                    msg_wa = f"*NUEVA RESERVA J&M*\n\n👤 Cliente: {st.session_state.user_name}\n🚗 Vehículo: {auto['nombre']}\n📅 Fechas: {f_ini} al {f_fin}\n💰 Total: {auto['precio_brl']} BRL"
                    msg_email = f"Es un placer saludarte, {st.session_state.user_name}. Tu reserva ha sido procesada con éxito en J&M ASOCIADOS."

                    # BOTONES CON ICONOS Y COLORES OFICIALES
                    st.markdown(f'''
                        <a href="https://wa.me/595991681191?text={urllib.parse.quote(msg_wa)}" target="_blank" class="btn-notif btn-whatsapp">
                            <i class="fa-brands fa-whatsapp btn-icon"></i> Notificar Empresa por WhatsApp
                        </a>
                        <a href="mailto:{st.session_state.user_name}?subject=Confirmacion Reserva J&M&body={urllib.parse.quote(msg_email)}" class="btn-notif btn-email">
                            <i class="fa-solid fa-envelope btn-icon"></i> Notificar Cliente por Email
                        </a>
                    ''', unsafe_allow_html=True)
                    
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_KEY_24510861818", caption="Escanea para pagar PIX")
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[2]:
            # (Mantener lógica de Panel Master anterior)
            st.write("### Control Maestro")
            conn = sqlite3.connect('jm_asociados.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.dataframe(df)
            conn.close()
