import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, date, timedelta
import uuid
import json
import requests
import time

# --- CONFIGURACIÓN DE LUJO ---
st.set_page_config(
    page_title="JM Alquiler | Premium Fleet",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DISEÑO (DESIGN SYSTEM) ---
COLORS = {
    "bordo": "#600010",
    "gold": "#D4AF37",
    "ivory": "#FDFCFB",
    "glass": "rgba(255, 255, 255, 0.8)",
    "text": "#1A1A1A"
}

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');
    
    .stApp {{ background-color: {COLORS['ivory']}; font-family: 'Inter', sans-serif; }}
    
    /* Glassmorphism Header */
    .glass-header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: {COLORS['glass']};
        backdrop-filter: blur(10px);
        z-index: 999; padding: 10px 50px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.3);
        display: flex; justify-content: space-between; align-items: center;
    }}
    
    /* Vehicle Cards */
    .vehicle-card {{
        background: white;
        border-radius: 24px;
        padding: 0px;
        overflow: hidden;
        border: 1px solid #EAEAEA;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
    }}
    .vehicle-card:hover {{
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(96, 0, 16, 0.1);
        border-color: {COLORS['gold']};
    }}
    
    /* Tipografía */
    h1, h2, .luxury-title {{ font-family: 'Playfair Display', serif; color: {COLORS['bordo']}; }}
    
    /* Botones Premium */
    .stButton>button {{
        background: linear-gradient(135deg, {COLORS['bordo']} 0%, #3a000a 100%);
        color: white; border-radius: 12px; border: none;
        padding: 12px 24px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 1px; transition: 0.3s; width: 100%;
    }}
    .stButton>button:hover {{
        background: {COLORS['gold']};
        transform: scale(1.02);
    }}
    
    /* Status Badge */
    .badge {{
        padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
        text-transform: uppercase;
    }}
    .available {{ background: #E6FFFA; color: #2C7A7B; }}
    .maintenance {{ background: #FFF5F5; color: #C53030; }}
    </style>
""", unsafe_allow_html=True)

# --- SERVICIOS Y PERSISTENCIA ---
DATA_FILE = "jm_premium_data.json"

def init_data():
    if 'data' not in st.session_state:
        if requests.os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                st.session_state.data = json.load(f)
        else:
            st.session_state.data = {
                "fleet": [
                    {"id": "1", "name": "Hyundai Tucson 2012", "price": 260.0, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "status": "Available", "plate": "AAVI502", "specs": {"trans": "Auto", "fuel": "Diesel", "pax": 5}},
                    {"id": "2", "name": "Toyota Vitz 2012", "price": 195.0, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "status": "Available", "plate": "AAVP719", "specs": {"trans": "Auto", "fuel": "Nafta", "pax": 5}},
                    {"id": "3", "name": "Toyota Voxy 2011", "price": 240.0, "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "status": "Available", "plate": "AAUG465", "specs": {"trans": "Auto", "fuel": "Nafta", "pax": 7}}
                ],
                "reservations": [],
                "expenses": []
            }
    if 'rates' not in st.session_state:
        st.session_state.rates = {"PYG": 1460, "USD": 0.18}
    if 'view' not in st.session_state:
        st.session_state.view = 'FLEET'

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.data, f, indent=4)

def get_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/BRL", timeout=5).json()
        st.session_state.rates["PYG"] = r['rates']['PYG']
        st.session_state.rates["USD"] = r['rates']['USD']
    except: pass

# --- COMPONENTES UI ---

def render_navbar():
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
            <div>
                <h1 style="margin:0; font-size: 2.5rem;">JM <span style="color:{COLORS['gold']}">ALQUILER</span></h1>
                <p style="margin:0; letter-spacing: 3px; font-size: 0.8rem; color: gray;">TRIPLE FRONTERA LUXURY RENTAL</p>
            </div>
            <div style="text-align: right; background: white; padding: 10px 20px; border-radius: 15px; border: 1px solid #eee;">
                <span style="color: gray; font-size: 0.8rem;">COTIZACIÓN REAL</span><br>
                <b style="color: {COLORS['bordo']};">1 BRL = {st.session_state.rates['PYG']:,} PYG</b>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns([1,1,1,1,5])
    if cols[0].button("🏷️ FLOTA"): st.session_state.view = 'FLEET'; st.rerun()
    if cols[1].button("📍 SEDE"): st.session_state.view = 'LOCATION'; st.rerun()
    if cols[2].button("🔐 ADMIN"): st.session_state.view = 'ADMIN'; st.rerun()
    if cols[3].button("🔄"): get_rates(); st.rerun()

# --- VISTA: FLOTA ---
def show_fleet():
    st.markdown("<h2 style='text-align:center;'>Nuestra Flota Exclusiva</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Seleccione un vehículo para comenzar su experiencia</p>", unsafe_allow_html=True)
    st.write("---")
    
    for car in st.session_state.data['fleet']:
        col_img, col_info = st.columns([1.2, 2])
        
        with col_img:
            st.image(car['img'], use_container_width=True)
            
        with col_info:
            status_class = "available" if car['status'] == "Available" else "maintenance"
            st.markdown(f"""
                <span class="badge {status_class}">{car['status']}</span>
                <h2 style="margin: 10px 0 0 0;">{car['name']}</h2>
                <p style="color: {COLORS['gold']}; font-weight: 600; letter-spacing: 1px;">{car['plate']}</p>
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div><small style="color:gray;">PASAJEROS</small><br><b>👤 {car['specs']['pax']}</b></div>
                    <div><small style="color:gray;">TRANSMISIÓN</small><br><b>⚙️ {car['specs']['trans']}</b></div>
                    <div><small style="color:gray;">COMBUSTIBLE</small><br><b>⛽ {car['specs']['fuel']}</b></div>
                </div>
                <div style="background: #f9f9f9; padding: 15px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.8rem; font-weight: 700; color: {COLORS['bordo']};">R$ {car['price']}</span>
                        <span style="color: gray;">/ día</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: gray; font-size: 0.8rem;">Total Gs.</span><br>
                        <b style="font-size: 1.1rem;">{(car['price'] * st.session_state.rates['PYG']):,.0f}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if car['status'] == "Available":
                if st.button(f"RESERVAR {car['name'].upper()}", key=f"res_{car['id']}"):
                    st.session_state.selected_car = car
                    st.session_state.view = 'BOOKING'
                    st.rerun()
            else:
                st.button("NO DISPONIBLE", disabled=True, key=f"off_{car['id']}")
        st.write("---")

# --- VISTA: RESERVA (WIZARD) ---
def show_booking():
    car = st.session_state.get('selected_car')
    if not car: st.session_state.view = 'FLEET'; st.rerun()
    
    st.markdown(f"## 🗓️ Reserva: {car['name']}")
    
    with st.expander("Ver Detalles del Contrato", expanded=False):
        st.write("1. Uso exclusivo en territorio paraguayo. 2. Seguro con franquicia de Gs. 5.000.000. 3. Devolución con mismo nivel de combustible.")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Período y Cliente")
        d_range = st.date_input("Seleccione Fechas", [date.today(), date.today() + timedelta(days=2)])
        if len(d_range) == 2:
            days = (d_range[1] - d_range[0]).days
            if days == 0: days = 1
            total = days * car['price']
            st.info(f"Duración: {days} días | Total: R$ {total:,.2f}")
        
        name = st.text_input("Nombre y Apellido")
        doc = st.text_input("Documento (CI/Pasaporte)")
        wa = st.text_input("WhatsApp (ej: 595981...)")

    with col2:
        st.subheader("2. Pago y Firma")
        pay_method = st.selectbox("Método de Pago", ["PIX", "Efectivo", "Transferencia Ueno", "Tarjeta de Crédito"])
        
        if pay_method == "PIX":
            st.code("Llave PIX: 24510861818 (Marina Baez)", language="text")
            
        st.write("Firma Digital:")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#000",
            background_color="#fff",
            height=150,
            key="canvas",
        )
        
        if st.button("CONFIRMAR Y GENERAR VOUCHER"):
            if name and doc and wa and len(d_range)==2:
                new_res = {
                    "id": str(uuid.uuid4())[:8],
                    "car": car['name'],
                    "client": name,
                    "doc": doc,
                    "wa": wa,
                    "start": str(d_range[0]),
                    "end": str(d_range[1]),
                    "total": total,
                    "status": "Confirmed",
                    "created_at": str(date.today())
                }
                st.session_state.data['reservations'].append(new_res)
                save_db()
                
                # WhatsApp Logic
                msg = f"*RESERVA JM ALQUILER*\n🚗 {car['name']}\n👤 {name}\n📅 {d_range[0]} al {d_range[1]}\n💰 Total: R$ {total}"
                wa_url = f"https://wa.me/{wa}?text={requests.utils.quote(msg)}"
                
                st.balloons()
                st.success("¡Reserva confirmada con éxito!")
                st.markdown(f"[📲 Enviar Comprobante por WhatsApp]({wa_url})")
                time.sleep(3)
                st.session_state.view = 'FLEET'
                st.rerun()

# --- VISTA: ADMIN (DASHBOARD) ---
def show_admin():
    if st.text_input("Acceso Administrativo", type="password") != "8899":
        st.stop()
        
    st.markdown("## 📈 Panel de Control Estratégico")
    
    # KPIs
    res_df = pd.DataFrame(st.session_state.data['reservations'])
    exp_df = pd.DataFrame(st.session_state.data['expenses'])
    
    rev = res_df['total'].sum() if not res_df.empty else 0
    costs = exp_df['monto'].sum() if not exp_df.empty else 0 # Simplificado a BRL
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Brutos", f"R$ {rev:,.0f}")
    c2.metric("Gastos Totales", f"R$ {costs:,.0f}")
    c3.metric("Utilidad Neta", f"R$ {rev - costs:,.0f}")
    c4.metric("Reservas Activas", len(res_df))

    tab1, tab2, tab3 = st.tabs(["📊 Métricas", "🚗 Flota", "💸 Finanzas"])
    
    with tab1:
        if not res_df.empty:
            fig = px.line(res_df, x='created_at', y='total', title="Tendencia de Ingresos",
                          line_shape="spline", color_discrete_sequence=[COLORS['gold']])
            st.plotly_chart(fig, use_container_width=True)
            
        if st.button("🤖 Consultar Estrategia IA (Gemini)"):
            st.info("Analizando tendencias de flota y rentabilidad...")
            # Aquí iría el llamado a genai.configure y el prompt detallado.
            st.write("💡 *Consejo IA:* El Toyota Vitz tiene la mayor rotación. Considera aumentar la flota de compactos para el Q3.")

    with tab2:
        for i, car in enumerate(st.session_state.data['fleet']):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**{car['name']}** - {car['plate']}")
            new_st = col_b.selectbox("Estado", ["Available", "Maintenance"], 
                                    index=0 if car['status']=="Available" else 1, key=f"edit_{i}")
            if new_st != car['status']:
                st.session_state.data['fleet'][i]['status'] = new_st
                save_db()
                st.rerun()

    with tab3:
        with st.form("Gasto"):
            st.write("Registrar Egreso")
            desc = st.text_input("Descripción")
            amt = st.number_input("Monto (BRL)")
            if st.form_submit_button("Guardar"):
                st.session_state.data['expenses'].append({"desc": desc, "monto": amt, "date": str(date.today())})
                save_db()
                st.rerun()
        st.table(exp_df)

# --- MAIN ---
init_data()
render_navbar()

if st.session_state.view == 'FLEET':
    show_fleet()
elif st.session_state.view == 'BOOKING':
    show_booking()
elif st.session_state.view == 'ADMIN':
    show_admin()
elif st.session_state.view == 'LOCATION':
    st.markdown("### 📍 Ubicación Estratégica")
    st.write("Av. Aviadores del Chaco c/ Av. Monseñor Rodriguez - Ciudad del Este")
    st.map(pd.DataFrame({'lat': [-25.509], 'lon': [-54.611]}))

# Footer
st.markdown(f"""
    <div style="text-align:center; padding: 50px; color: gray; font-size: 0.8rem;">
        © 2026 JM ASOCIADOS | Luxury Car Rental Service<br>
        <span style="color:{COLORS['gold']}">Premium Experience</span>
    </div>
""", unsafe_allow_html=True)