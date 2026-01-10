import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, date, time
from streamlit_drawable_canvas import st_canvas
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="JM Alquiler | Triple Frontera VIP", layout="wide", page_icon="🚗")

def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Playfair+Display:wght@700&display=swap');

    :root {
        --bordo: #600010; --gold: #D4AF37; --ivory: #FDFCFB;
    }

    /* Estética Glassmorphism Luxury */
    .stApp { background-color: var(--ivory); font-family: 'Inter', sans-serif; }
    
    [data-testid="stHeader"] { background: rgba(96, 0, 16, 0.9); backdrop-filter: blur(10px); }
    
    .luxury-card {
        background: white; padding: 2rem; border-radius: 2.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid rgba(212, 175, 55, 0.2);
        margin-bottom: 20px; animation: fadeIn 0.8s ease-out;
    }

    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--bordo); }

    /* Botones VIP */
    .stButton>button {
        border-radius: 1.5rem !important; background: var(--bordo) !important;
        color: white !important; letter-spacing: 0.2em !important; font-weight: bold !important;
        border: none !important; text-transform: uppercase; transition: 0.4s; width: 100%;
    }
    .stButton>button:hover { background: var(--gold) !important; box-shadow: 0 5px 15px rgba(212,175,55,0.4); }

    /* Status Pill */
    .pill { padding: 4px 12px; border-radius: 1rem; font-size: 0.75rem; font-weight: bold; }
    .disponible { background: #dcfce7; color: #166534; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- CONEXIÓN A GOOGLE SHEETS (PERSISTENCIA) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    res_df = conn.read(worksheet="reservations")
except:
    res_df = pd.DataFrame(columns=["car", "total", "date", "customer"])

# --- LÓGICA DE MONEDA ---
@st.cache_data(ttl=3600)
def get_exchange():
    try:
        return requests.get("https://open.er-api.com/v6/latest/BRL").json()['rates']['PYG']
    except: return 1450.0

PYG_RATE = get_exchange()

# --- NAVBAR CUSTOM ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; background: var(--bordo); padding: 1rem 5%; border-radius: 0 0 2rem 2rem; margin-bottom: 2rem;">
        <div style="color: white;">
            <h2 style="margin:0; color: white !important;">JM <span style="color:var(--gold);">ALQUILER</span></h2>
            <small style="letter-spacing: 0.1em;">TRIPLE FRONTERA VIP</small>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 1rem; text-align: right;">
            <div style="color: var(--gold); font-weight: bold; font-size: 1.2rem;">Gs. {int(1245 * (PYG_RATE/1450)*1450):,}</div>
            <small style="color: white; font-size: 0.6rem;">BRL MARKET</small>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- DATOS DE FLOTA ---
FLEET = [
    {
        "id": "AAVI502", "name": "Hyundai Tucson 2012", "price": 260, 
        "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png",
        "specs": {"Potencia": "184 CV", "Tanque": "58 L", "Maletero": "591 L", "Motor": "2.0 CRDi VGT (DIESEL)"}
    }
]

# --- APP TABS ---
tab_cat, tab_loc, tab_adm = st.tabs(["💎 CATÁLOGO", "📍 SEDE", "⚙️ ADMIN"])

with tab_cat:
    # Banner Hero
    st.markdown("""
        <div style="background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&q=80'); background-size: cover; padding: 4rem; border-radius: 2.5rem; text-align: center; color: white; margin-bottom: 2rem;">
            <h1 style="color: white !important; font-size: 3rem;">Domina el Camino.</h1>
            <p style="color: var(--gold); letter-spacing: 0.2em;">CALIDAD CERTIFICADA MERCOSUR</p>
        </div>
    """, unsafe_allow_html=True)

    for car in FLEET:
        col_img, col_info = st.columns([1, 1])
        with col_img:
            st.image(car['img'], use_container_width=True)
        
        with col_info:
            st.markdown(f"""
                <small style="color: var(--gold); font-weight: bold;">{car['id']}</small>
                <h1 style="margin-top: 0;">{car['name']}</h1>
                <div class="luxury-card" style="padding: 1rem;">
                    <p><b>FICHA TÉCNICA DETALLADA</b></p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                        <div>⚡ POTENCIA: {car['specs']['Potencia']}</div>
                        <div>⛽ TANQUE: {car['specs']['Tanque']}</div>
                        <div>📦 MALETERO: {car['specs']['Maletero']}</div>
                        <div>⚙️ MOTOR: {car['specs']['Motor']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Disponibilidad Mini (Visual)
            st.write("📅 DISPONIBILIDAD ENERO 2026")
            st.image("https://i.imgur.com/8Qp5QYx.png", width=300) # Placeholder calendario

            if st.button("GESTIONAR RESERVA", key=car['id']):
                st.session_state.booking_car = car
                st.session_state.step = 1
                st.toggle("show_modal", value=True)

# --- BOOKING WIZARD (MODAL SIMULADO) ---
if st.session_state.get("booking_car"):
    with st.expander("📝 PROCESO DE RESERVA VIP", expanded=True):
        car = st.session_state.booking_car
        step = st.session_state.get("step", 1)
        
        # Header del Wizard
        cols_step = st.columns(3)
        for i, s_name in enumerate(["Cronograma", "Pagos", "Contrato"]):
            color = "var(--gold)" if (i+1) <= step else "#ccc"
            cols_step[i].markdown(f"<div style='text-align:center; border-bottom: 3px solid {color}; padding-bottom:5px; color:{color}; font-weight:bold;'>{s_name}</div>", unsafe_allow_html=True)

        if step == 1:
            st.markdown("### Protocolo de Reserva (1 Día)")
            st.info(f"Para formalizar el bloqueo de la unidad, se requiere el pago inicial de **R$ {car['price']}**.")
            
            c1, c2 = st.columns(2)
            d_in = c1.date_input("RETIRO DE LA UNIDAD", value=date(2026,1,10))
            t_in = c2.selectbox("HORA", ["08:00", "09:00", "10:00"], key="t1")
            
            d_out = c1.date_input("DEVOLUCIÓN DE LA UNIDAD", value=date(2026,1,10))
            t_out = c2.selectbox("HORA", ["12:00", "13:00", "17:00"], key="t2")
            
            st.markdown(f"""
                <div style="background: var(--bordo); color: white; padding: 2rem; border-radius: 2rem; text-align: center; margin: 1rem 0;">
                    <small>PAGO INICIAL REQUERIDO (GS.)</small>
                    <h1 style="color: white !important; margin:0;">{(car['price'] * PYG_RATE):,.0f}</h1>
                    <small>● CONVERSIÓN BANCARIA ACTUALIZADA</small>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("PROCEDER AL PORTAL DE PAGO"): 
                st.session_state.step = 2
                st.rerun()

        elif step == 2:
            st.markdown("### Portal de Pagos")
            st.text_input("Nombre del Titular")
            st.text_input("C.I. / R.G. / Pasaporte")
            
            pay_method = st.radio("SELECCIONE PLATAFORMA", ["BANCARD / QR", "PIX BRASIL", "TRANSFERENCIA", "EFECTIVO"], horizontal=True)
            
            if pay_method == "BANCARD / QR":
                st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=JM_ALQUILER_{car['price']}", width=200)
                st.caption("ESCANEA DESDE CUALQUIER APP BANCARIA DE PARAGUAY")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.file_uploader("RESPALDO DE OPERACIÓN (FOTO)")
            
            if st.button("REVISAR CONTRATO"): 
                st.session_state.step = 3
                st.rerun()

        elif step == 3:
            st.markdown("### Contrato de Arrendamiento")
            st.write(f"**ARRENDADOR:** JM ASOCIADOS | **ARRENDATARIO:** Cliente VIP | **UNIDAD:** {car['name']}")
            
            st.write("FIRMA DEL TITULAR:")
            canvas_result = st_canvas(fill_color="rgba(255, 255, 255, 0)", stroke_width=2, stroke_color="#600010", background_color="#eee", height=150, key="canvas")
            
            if st.checkbox("Confirmo el pago de reserva de 1 día y acepto todas las cláusulas."):
                if st.button("CONFIRMAR Y BLOQUEAR UNIDAD"):
                    # Aquí va la lógica de guardado en GSheets
                    st.success("¡Tu reserva está lista! Bloqueamos el vehículo para vos.")
                    st.balloons()
                    # Generar Link de WhatsApp
                    msg = f"Reserva Confirmada: {car['name']} para {date.today()}"
                    st.markdown(f"[ENVIAR COMPROBANTE POR WHATSAPP](https://wa.me/595991681191?text={msg})")

with tab_adm:
    pwd = st.text_input("Acceso Admin", type="password")
    if pwd == "8899":
        st.title("Business Intelligence Dashboard")
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Revenue BRL", f"R$ {res_df['total'].sum() if not res_df.empty else 0}")
        # Aquí puedes añadir los gráficos de Plotly solicitados