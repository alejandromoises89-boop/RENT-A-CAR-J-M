import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, date, timedelta
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURACIÓN E IDENTIDAD VISUAL ---
st.set_page_config(page_title="JM Alquiler | Triple Frontera VIP", layout="wide", page_icon="🚗")

# Inyección de CSS para "Executive Luxury" y "Glassmorphism"
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

    :root {
        --bordo: #600010;
        --gold: #D4AF37;
        --ivory: #FDFCFB;
    }

    .stApp { background-color: var(--ivory); font-family: 'Inter', sans-serif; }
    
    /* Headers Luxury */
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--bordo); }

    /* Glassmorphism Header */
    .glass-header {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 2rem;
        padding: 2rem;
        border: 1px solid rgba(212, 175, 55, 0.3);
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Luxury Cards */
    .car-card {
        background: white;
        padding: 2rem;
        border-radius: 3rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 1px solid #eee;
        transition: transform 0.3s ease;
    }
    .car-card:hover { transform: translateY(-10px); border-color: var(--gold); }

    /* Botones VIP */
    .stButton>button {
        border-radius: 3rem !important;
        background-color: var(--bordo) !important;
        color: white !important;
        border: none !important;
        padding: 0.8rem 2.5rem !important;
        font-weight: bold !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase;
        transition: all 0.4s ease;
    }
    .stButton>button:hover {
        background-color: var(--gold) !important;
        box-shadow: 0 5px 15px rgba(212, 175, 55, 0.4);
    }

    /* Status Pills */
    .pill-available {
        background: #d4edda; color: #155724;
        padding: 0.2rem 1rem; border-radius: 1rem; font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE DATOS ---
if 'fleet' not in st.session_state:
    st.session_state.fleet = [
        {"id": "1", "nombre": "Hyundai Tucson 2012", "precio": 260.0, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible", "placa": "AAVI502", "motor": "2.0 CRDi", "transmision": "Automática", "specs": "Diesel, 5 Pasajeros, Valija Amplia"},
        {"id": "2", "nombre": "Toyota Vitz 2012", "precio": 195.0, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible", "placa": "AAVP719", "motor": "1.3 VVT-i", "transmision": "Automática", "specs": "Nafta, Bajo Consumo, Urbano"},
        {"id": "3", "nombre": "Toyota Vitz RS 2012", "precio": 210.0, "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "estado": "Disponible", "placa": "AAOR725", "motor": "1.5 RS", "transmision": "Secuencial", "specs": "Nafta, Suspensión Deportiva"},
        {"id": "4", "nombre": "Toyota Voxy 2011", "precio": 240.0, "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible", "placa": "AAUG465", "motor": "2.0 Valvematic", "transmision": "Automática", "specs": "Nafta, 7 Pasajeros, Puertas Eléctricas"}
    ]

if 'reservations' not in st.session_state: st.session_state.reservations = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LÓGICA DE MONEDA ---
@st.cache_data(ttl=3600)
def get_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/BRL")
        return r.json()['rates']['PYG']
    except: return 1450.0

PYG_RATE = get_rates()

# --- NAVEGACIÓN ---
selected = st.sidebar.radio("MENÚ VIP", ["💎 Unidades", "📍 Sede Central", "⚙️ Admin"])

# --- MÓDULO: UNIDADES ---
if selected == "💎 Unidades":
    st.markdown("""
        <div class="glass-header">
            <h1 style='margin:0;'>Domina el Camino.</h1>
            <p style='color: var(--gold); letter-spacing: 0.1em;'>CALIDAD CERTIFICADA MERCOSUR</p>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for idx, car in enumerate(st.session_state.fleet):
        with cols[idx % 2]:
            st.markdown(f"""
                <div class="car-card">
                    <img src="{car['img']}" style="width:100%; filter: drop-shadow(0 10px 10px rgba(0,0,0,0.1));">
                    <span class="pill-available">● {car['estado']}</span>
                    <h2 style="margin-top:1rem;">{car['nombre']}</h2>
                    <p style="font-size: 1.5rem; color: var(--bordo); font-weight: bold;">
                        R$ {car['precio']} <small style="color:#888; font-size:0.9rem;">/ {(car['precio']*PYG_RATE):,.0f} Gs</small>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("REVISAR DISPONIBILIDAD Y DETALLES"):
                st.write(f"**Motor:** {car['motor']} | **Placa:** {car['placa']}")
                st.info(f"✨ {car['specs']}")
                
                # BOOKING WIZARD
                st.markdown("### 📝 Solicitud de Reserva")
                col_a, col_b = st.columns(2)
                d_in = col_a.date_input("Recogida", min_value=date.today(), key=f"in_{car['id']}")
                d_out = col_b.date_input("Devolución", min_value=d_in, key=f"out_{car['id']}")
                
                total_days = (d_out - d_in).days or 1
                total_brl = total_days * car['precio']
                
                st.write(f"Total: **R$ {total_brl}** / **{total_brl*PYG_RATE:,.0f} Gs**")
                
                if st.button("GESTIONAR RESERVA", key=f"btn_{car['id']}"):
                    st.session_state.current_car = car
                    st.session_state.booking_data = {"days": total_days, "total": total_brl, "start": d_in}
                    st.switch_page("pages/booking_flow.py") if False else st.warning("Redirigiendo al Portal de Pagos...") # Simulación de flujo

# --- MÓDULO: ADMIN (REPORTE IA) ---
elif selected == "⚙️ Admin":
    pwd = st.text_input("Acceso Restringido", type="password")
    if pwd == "8899":
        st.title("Admin Strategic Dashboard")
        
        # KPI Cards
        rev = sum(r['total'] for r in st.session_state.reservations)
        exp = sum(e['amount'] for e in st.session_state.expenses)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue (BRL)", f"R$ {rev:,.2f}")
        c2.metric("Expenses", f"R$ {exp:,.2f}")
        c3.metric("Profit", f"R$ {(rev-exp):,.2f}", delta_color="normal")

        # Gráfico Area
        if st.session_state.reservations:
            df = pd.DataFrame(st.session_state.reservations)
            fig = px.area(df, x='date', y='total', title="Flujo de Caja", color_discrete_sequence=['#600010'])
            st.plotly_chart(fig, use_container_width=True)

        # Gemini AI
        if st.button("✨ GENERAR REPORTE DE ESTRATEGIA"):
            st.info("Analizando datos de flota y mercado en Ciudad del Este...")
            # Aquí iría la llamada real a genai
            st.success("Consigna IA: Incrementar tarifas un 15% los fines de semana debido a alta demanda de turistas brasileños. Priorizar mantenimiento del Voxy (7 plazas).")

# --- FOOTER ---
st.markdown("---")
st.caption("JM Alquiler Premium - Luxury Experience. Ciudad del Este, Paraguay.")