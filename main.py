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

st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        html { scroll-behavior: smooth; }
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; margin-bottom: 10px; }
        .cotizacion-texto { text-align: center; color: #D4AF37; font-weight: bold; font-size: 1.1rem; margin-bottom: 20px; border: 1px solid #D4AF37; padding: 10px; border-radius: 10px; background: rgba(255,255,255,0.05); }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; }
        
        .btn-notif {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 15px;
            border-radius: 12px;
            text-decoration: none !important;
            font-weight: bold;
            font-size: 16px;
            margin-top: 10px;
            width: 100%;
            transition: 0.3s ease;
            border: none;
        }
        .btn-whatsapp { background-color: #25D366; color: white !important; box-shadow: 0 4px #128C7E; }
        .btn-email { background-color: #D4AF37; color: black !important; box-shadow: 0 4px #b08d2c; }
        .btn-icon { margin-right: 12px; font-size: 24px; }
        
        .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGICA DE DATOS ---
def obtener_cotizacion_brl():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/BRL"
        r = requests.get(url)
        return round(r.json()['rates']['PYG'])
    except:
        return 1450 

cotizacion_hoy = obtener_cotizacion_brl()

def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL)''')
    conn.commit()
    conn.close()

# --- 3. FLOTA CORREGIDA (Nombres vs Colores vs Links) ---
flota = [
    {
        "nombre": "Hyundai Tucson", 
        "color": "Blanco", 
        "precio_brl": 260, 
        "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"
    },
    {
        "nombre": "Toyota Vitz", 
        "color": "Blanco", 
        "precio_brl": 195, 
        "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"
    },
    {
        "nombre": "Toyota Vitz", 
        "color": "Negro", 
        "precio_brl": 195, 
        "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"
    },
    {
        "nombre": "Toyota Voxy", 
        "color": "Gris", 
        "precio_brl": 240, 
        "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"
    }
]

init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. INTERFAZ ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M ASOCIADOS</h1></div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", u
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p style="color:white;">Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cotizacion-texto">📊 Cotización Real hoy: 1 Real = {cotizacion_hoy:,} PYG</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "⚙️ Panel Master"])

    with tabs[0]:
        for auto in flota:
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            # Creamos un ID único para el ancla de cada auto
            auto_id = auto['nombre'].replace(" ", "") + auto['color']
            
            with st.container():
                st.markdown(f'<div class="card-auto" id="card_{auto_id}">', unsafe_allow_html=True)
                col_img, col_info = st.columns([1, 2])
                
                with col_img:
                    st.image(auto['img'], use_container_width=True)
                
                with col_info:
                    st.subheader(f"{auto['nombre']} - {auto['color']}")
                    st.write(f"💳 **Tarifa:** {auto['precio_brl']} BRL / Gs. {monto_pyg:,}")
                    f_ini = st.date_input("Recogida", key=f"i_{auto_id}")
                    f_fin = st.date_input("Devolución", key=f"f_{auto_id}")
                    
                    btn_alquilar = st.button("Alquilar", key=f"btn_{auto_id}")
                    
                    if btn_alquilar:
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_pyg, monto_brl) VALUES (?,?,?,?,?,?)",
                                             (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", str(f_ini), str(f_fin), monto_pyg, auto['precio_brl']))
                        conn.commit()
                        conn.close()
                        
                        msg_wa = f"*RESERVA J&M*\n👤 Cliente: {st.session_state.user_name}\n🚗 Auto: {auto['nombre']} {auto['color']}\n💰 Total: {auto['precio_brl']} BRL"
                        msg_em = f"Hola {st.session_state.user_name}, su reserva en J&M fue exitosa."
                        
                        # El mensaje de éxito y botones aparecen justo debajo del auto alquilado
                        st.markdown(f'''
                            <div id="confirm_{auto_id}" style="background:rgba(212, 175, 55, 0.1); padding:20px; border-radius:15px; border:2px solid #D4AF37; margin-top:20px; text-align:center;">
                                <h3 style="color:#D4AF37;">✅ ¡Reserva Exitosa!</h3>
                                <p style="color:black;">Notifique su pago aquí:</p>
                                <a href="https://wa.me/595991681191?text={urllib.parse.quote(msg_wa)}" target="_blank" class="btn-notif btn-whatsapp">
                                    <i class="fa-brands fa-whatsapp btn-icon"></i> Notificar vía WhatsApp
                                </a>
                                <a href="mailto:{st.session_state.user_name}?subject=Reserva J&M&body={urllib.parse.quote(msg_em)}" class="btn-notif btn-email">
                                    <span class="material-icons btn-icon">mail</span> Notificar vía Email
                                </a>
                                <div style="margin-top:15px;">
                                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=24510861818" style="border-radius:10px;">
                                    <p style="color:black; font-size:0.8rem;">Pagar a Marina Baez (PIX)</p>
                                </div>
                            </div>
                            <script>
                                document.getElementById("confirm_{auto_id}").scrollIntoView({{behavior: "smooth"}});
                            </script>
                        ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[2]:
            conn = sqlite3.connect('jm_asociados.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.dataframe(df)
            conn.close()
