import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, date, timedelta
import uuid
import json
import requests
import time
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM Alquiler | Premium Car Rental",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES Y DISEÑO (DESIGN SYSTEM) ---
COLORS = {
    "bordo": "#600010",
    "gold": "#D4AF37",
    "ivory": "#FDFCFB",
    "glass": "rgba(255, 255, 255, 0.9)",
    "dark": "#1A1A1A"
}

DATA_FILE = "jm_premium_data.json"
ADMIN_KEY = "8899"
CORPORATE_WA = "595991681191"

# CSS Personalizado para Look SPA de Lujo
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');
    
    .stApp {{ background-color: {COLORS['ivory']}; font-family: 'Inter', sans-serif; }}
    
    h1, h2, h3, .luxury-text {{ font-family: 'Playfair Display', serif; color: {COLORS['bordo']}; }}
    
    /* Tarjeta de Vehículo Asimétrica */
    .vehicle-container {{
        background: white;
        border-radius: 30px;
        padding: 25px;
        margin-bottom: 30px;
        border-left: 8px solid {COLORS['bordo']};
        box-shadow: 0 15px 35px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }}
    .vehicle-container:hover {{ transform: scale(1.01); border-left-color: {COLORS['gold']}; }}
    
    /* Botones */
    .stButton>button {{
        background: linear-gradient(135deg, {COLORS['bordo']} 0%, #3a000a 100%);
        color: white; border-radius: 12px; border: none;
        padding: 15px; font-weight: 600; letter-spacing: 1px; width: 100%;
    }}
    .stButton>button:hover {{ background: {COLORS['gold']}; color: white; border: none; }}
    
    /* Indicadores */
    .status-pill {{
        padding: 5px 15px; border-radius: 20px; font-size: 0.7rem; font-weight: bold;
        text-transform: uppercase; letter-spacing: 1px;
    }}
    .available {{ background: #e6fffa; color: #234e52; }}
    .maintenance {{ background: #fff5f5; color: #742a2a; }}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---

def get_default_data():
    return {
        "fleet": [
            {"id": "1", "nombre": "Hyundai Tucson 2012", "precio": 260.0, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible", "placa": "AAVI502", "specs": {"trans": "Automática", "fuel": "Diesel", "pax": 5}},
            {"id": "2", "nombre": "Toyota Vitz 2012", "precio": 195.0, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible", "placa": "AAVP719", "specs": {"trans": "Automática", "fuel": "Nafta", "pax": 5}},
            {"id": "3", "nombre": "Toyota Vitz RS 2012", "precio": 195.0, "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "estado": "Disponible", "placa": "AAOR725", "specs": {"trans": "Secuencial", "fuel": "Nafta", "pax": 5}},
            {"id": "4", "nombre": "Toyota Voxy 2011", "precio": 240.0, "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible", "placa": "AAUG465", "specs": {"trans": "Automática", "fuel": "Nafta", "pax": 7}}
        ],
        "reservations": [],
        "expenses": []
    }

def init_session():
    if 'data' not in st.session_state:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    st.session_state.data = json.load(f)
            except:
                st.session_state.data = get_default_data()
        else:
            st.session_state.data = get_default_data()
    
    if 'view' not in st.session_state: st.session_state.view = 'HOME'
    if 'rates' not in st.session_state: st.session_state.rates = {"PYG": 1460}

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.data, f, indent=4)

def get_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/BRL", timeout=5).json()
        st.session_state.rates["PYG"] = r['rates']['PYG']
    except: pass

# --- COMPONENTES DE INTERFAZ ---

def render_header():
    col_logo, col_text, col_rate = st.columns([1, 4, 2])
    with col_logo:
        st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=80)
    with col_text:
        st.markdown(f"<h1 style='margin:0;'>JM <span style='color:{COLORS['gold']}'>ALQUILER</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='letter-spacing:4px; font-size:0.7rem; color:gray; margin:0;'>TRIPLE FRONTERA VIP SERVICE</p>", unsafe_allow_html=True)
    with col_rate:
        st.markdown(f"""
            <div style="background:white; border:1px solid #eee; padding:10px; border-radius:15px; text-align:center;">
                <small style="color:gray;">Cotización Hoy</small><br>
                <b style="color:{COLORS['bordo']}; font-size:1.1rem;">1 BRL = Gs. {st.session_state.rates['PYG']:,}</b>
            </div>
        """, unsafe_allow_html=True)

def render_nav():
    st.write("")
    c1, c2, c3, c4, _ = st.columns([1,1,1,1,3])
    if c1.button("🚗 FLOTA"): st.session_state.view = 'HOME'; st.rerun()
    if c2.button("📍 SEDE"): st.session_state.view = 'MAP'; st.rerun()
    if c3.button("🔐 ADMIN"): st.session_state.view = 'ADMIN'; st.rerun()
    if c4.button("🔄"): get_rates(); st.rerun()
    st.divider()

# --- VISTAS ---

def view_home():
    st.markdown("<h2 style='text-align:center;'>Vehículos Disponibles</h2>", unsafe_allow_html=True)
    
    for car in st.session_state.data['fleet']:
        with st.container():
            # Diseño Asimétrico: Imagen izquierda, Info derecha
            col_img, col_info = st.columns([1.5, 2])
            
            with col_img:
                st.image(car['img'], use_container_width=True)
            
            with col_info:
                status_class = "available" if car['estado'] == "Disponible" else "maintenance"
                st.markdown(f"""
                    <div class="vehicle-container">
                        <span class="status-pill {status_class}">{car['estado']}</span>
                        <h2 style="margin:10px 0;">{car['nombre']}</h2>
                        <p style="color:gray; font-size:0.9rem;">Placa: <b>{car['placa']}</b></p>
                        <div style="display:flex; justify-content:space-between; margin:20px 0;">
                            <div><small>👤</small><br><b>{car['specs']['pax']} Pasajeros</b></div>
                            <div><small>⚙️</small><br><b>{car['specs']['trans']}</b></div>
                            <div><small>⛽</small><br><b>{car['specs']['fuel']}</b></div>
                        </div>
                        <div style="display:flex; align-items:flex-end; gap:10px;">
                            <span style="font-size:2rem; font-weight:bold; color:{COLORS['bordo']};">R$ {car['precio']}</span>
                            <span style="color:gray; margin-bottom:10px;">/ día</span>
                        </div>
                        <p style="color:{COLORS['gold']}; font-weight:bold;">Aprox. Gs. {(car['precio'] * st.session_state.rates['PYG']):,.0f}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if car['estado'] == "Disponible":
                    if st.button(f"SOLICITAR RESERVA", key=f"btn_{car['id']}"):
                        st.session_state.selected_car = car
                        st.session_state.view = 'BOOKING'
                        st.rerun()
                else:
                    st.button("NO DISPONIBLE", disabled=True, key=f"dis_{car['id']}")

def view_booking():
    car = st.session_state.get('selected_car')
    if not car: st.session_state.view = 'HOME'; st.rerun()
    
    st.markdown(f"## 📝 Reserva de {car['nombre']}")
    
    col_form, col_summary = st.columns([2, 1])
    
    with col_form:
        st.subheader("Datos del Arrendatario")
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        documento = c2.text_input("CI / Pasaporte")
        whatsapp = c1.text_input("WhatsApp (con código de país)")
        metodo = c2.selectbox("Forma de Pago", ["PIX", "Efectivo", "Transferencia", "Tarjeta"])
        
        st.subheader("Período de Alquiler")
        fechas = st.date_input("Rango de Fechas", [date.today(), date.today() + timedelta(days=3)])
        
        st.subheader("Firma del Contrato")
        st.write("Dibuja tu firma abajo:")
        canvas_result = st_canvas(
            stroke_width=2, stroke_color="#000", background_color="#fff",
            height=150, key="signature", drawing_mode="freedraw"
        )
        
    with col_summary:
        st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:20px; border:1px solid {COLORS['gold']};">
                <h3 style="margin-top:0;">Resumen</h3>
                <p>Vehículo: <b>{car['nombre']}</b></p>
                <hr>
        """, unsafe_allow_html=True)
        
        if len(fechas) == 2:
            dias = (fechas[1] - fechas[0]).days or 1
            total_brl = dias * car['precio']
            st.write(f"Días: **{dias}**")
            st.write(f"Total: **R$ {total_brl:,.2f}**")
            st.write(f"Total Gs: **{total_brl * st.session_state.rates['PYG']:,.0f}**")
        
        if st.button("CONFIRMAR ALQUILER"):
            if not nombre or not whatsapp or not canvas_result.json_data:
                st.error("Por favor, completa todos los campos y firma.")
            else:
                new_id = str(uuid.uuid4())[:8]
                reserva = {
                    "id": new_id, "cliente": nombre, "doc": documento, "carro": car['nombre'],
                    "inicio": str(fechas[0]), "fin": str(fechas[1]), "total": total_brl,
                    "status": "Confirmado", "pago": metodo
                }
                st.session_state.data['reservations'].append(reserva)
                save_db()
                
                # Link WhatsApp
                msg = f"*RESERVA JM ALQUILER*\nID: {new_id}\nCliente: {nombre}\nAuto: {car['nombre']}\nTotal: R$ {total_brl}"
                st.balloons()
                st.success("¡Reserva guardada!")
                st.markdown(f"[📲 Enviar Comprobante al WhatsApp](https://wa.me/{CORPORATE_WA}?text={requests.utils.quote(msg)})")
                time.sleep(4)
                st.session_state.view = 'HOME'
                st.rerun()

def view_admin():
    if st.text_input("Clave Maestra", type="password") != ADMIN_KEY:
        st.warning("Acceso restringido")
        return

    st.markdown("## 🛡️ Panel de Control")
    
    # Métricas
    df_res = pd.DataFrame(st.session_state.data['reservations'])
    df_exp = pd.DataFrame(st.session_state.data['expenses'])
    
    m1, m2, m3 = st.columns(3)
    rev = df_res['total'].sum() if not df_res.empty else 0
    m1.metric("Ingresos (BRL)", f"R$ {rev:,.2f}")
    m2.metric("Gastos", f"{len(df_exp)}")
    m3.metric("Ocupación", f"{len(df_res)}")

    tab1, tab2, tab3 = st.tabs(["📋 Reservas", "🚗 Flota", "💸 Gastos"])
    
    with tab1:
        st.dataframe(df_res, use_container_width=True)
        if st.button("✨ Analizar con Gemini AI"):
            st.info("Función de análisis inteligente activada. (Requiere API Key en secrets)")

    with tab2:
        for i, v in enumerate(st.session_state.data['fleet']):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{v['nombre']}** ({v['placa']})")
            new_st = col2.selectbox("Estado", ["Disponible", "Taller"], 
                                    index=0 if v['estado']=="Disponible" else 1, key=f"v_{i}")
            if new_st != v['estado']:
                st.session_state.data['fleet'][i]['estado'] = new_st
                save_db(); st.rerun()

    with tab3:
        with st.form("gasto_nuevo"):
            d = st.text_input("Descripción")
            m = st.number_input("Monto BRL")
            if st.form_submit_button("Añadir Gasto"):
                st.session_state.data['expenses'].append({"item": d, "monto": m, "fecha": str(date.today())})
                save_db(); st.rerun()
        st.table(df_exp)

# --- FLUJO PRINCIPAL ---
init_session()
render_header()
render_nav()

if st.session_state.view == 'HOME':
    view_home()
elif st.session_state.view == 'BOOKING':
    view_booking()
elif st.session_state.view == 'ADMIN':
    view_admin()
elif st.session_state.view == 'MAP':
    st.markdown("### 📍 Nuestra Ubicación")
    st.markdown("Av. Aviadores del Chaco c/ Av. Monseñor Rodriguez - Ciudad del Este")
    st.map(pd.DataFrame({'lat': [-25.509], 'lon': [-54.611]}))

st.markdown(f"""
    <div style="text-align:center; padding: 40px; color: gray; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 50px;">
        JM ALQUILER PREMIUM &copy; 2026 - Ciudad del Este, Paraguay<br>
        <span style="color:{COLORS['gold']}">Excelencia en Movilidad VIP</span>
    </div>
""", unsafe_allow_html=True)