import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
import requests
from datetime import datetime
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN Y COTIZACIÓN EN TIEMPO REAL ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

def obtener_cotizacion_brl():
    try:
        # Consulta a API de cambios para obtener el cambio BRL/PYG
        url = "https://api.exchangerate-api.com/v4/latest/BRL"
        response = requests.get(url)
        data = response.json()
        return round(data['rates']['PYG'])
    except:
        return 1450  # Valor de respaldo

cotizacion_hoy = obtener_cotizacion_brl()

st.markdown(f"""
<style>
    .stApp {{ background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }}
    .header-jm {{ text-align: center; color: #D4AF37; margin-bottom: 20px; }}
    .cotizacion-box {{ 
        background-color: rgba(212, 175, 55, 0.15); 
        padding: 15px; 
        border-radius: 12px; 
        text-align: center; 
        border: 1px solid #D4AF37; 
        margin-bottom: 25px;
        font-size: 1.2rem;
    }}
    .card-auto {{ background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; }}
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL)''')
    conn.commit()
    conn.close()

# --- 3. FLOTA CON PRECIOS ACTUALIZADOS EN REALES ---
flota = [
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio_brl": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio_brl": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
    {"nombre": "Toyota Vitz", "color": "Negro", "precio_brl": 195, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio_brl": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
]
# --- 4. INTERFAZ DE USUARIO ---
init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
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
    
    # Barra de Cotización
    st.markdown(f'<div class="cotizacion-box"><b>Referencia Cambios Chaco:</b> 1 Real = {cotizacion_hoy:,} Gs.</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Reservas", "⚙️ Panel Master"])

    with tabs[0]:
        for auto in flota:
            monto_pyg_total = auto['precio_brl'] * cotizacion_hoy
            st.markdown(f'<div class="card-auto">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} ({auto['color']})")
                st.write(f"💳 **Precio:** {auto['precio_brl']} Reales / día")
                st.write(f"🇵🇾 **Conversión:** Gs. {monto_pyg_total:,} aprox.")
                
                f_ini = st.date_input("Inicio", key=f"i_{auto['nombre']}_{auto['color']}")
                f_fin = st.date_input("Fin", key=f"f_{auto['nombre']}_{auto['color']}")
                
                if st.button("Alquilar", key=f"btn_{auto['nombre']}_{auto['color']}"):
                    conn = sqlite3.connect('jm_asociados.db')
                    conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_pyg, monto_brl) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", str(f_ini), str(f_fin), monto_pyg_total, auto['precio_brl']))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Vehículo Reservado")
                    
                    # Mensajes con los nuevos precios
                    msg_whatsapp = f"*RESERVA J&M ASOCIADOS*\n\n👤 Cliente: {st.session_state.user_name}\n🚗 Vehículo: {auto['nombre']} {auto['color']}\n💰 Total: {auto['precio_brl']} BRL (Gs. {monto_pyg_total:,})"
                    
                    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=24510861818", caption="PIX: Marina Baez")
                    st.markdown(f'[📲 Notificar a la Empresa](https://wa.me/595991681191?text={urllib.parse.quote(msg_whatsapp)})', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[2]:
            conn = sqlite3.connect('jm_asociados.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.metric("Total Reales Proyectados", f"{df['monto_brl'].sum():,} BRL")
            st.dataframe(df)
            conn.close()
