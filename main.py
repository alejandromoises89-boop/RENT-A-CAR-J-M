import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
import requests
import uuid
import datetime
import time
import os

# --- 1. CONFIGURACIÓN INICIAL Y ESTÉTICA DE LUJO ---
st.set_page_config(
    page_title="JM Alquiler | Premium Car Rental",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Colores de la marca (Extraídos de constants.ts)
COLOR_BORDO = "#600010"
COLOR_GOLD = "#D4AF37"
COLOR_IVORY = "#FDFCFB"

# INYECCIÓN DE CSS (El secreto para que se vea como React)
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;900&family=Playfair+Display:wght@700;900&display=swap');
        
        /* Fondo y Fuente Global */
        .stApp {{
            background-color: {COLOR_IVORY};
            font-family: 'Inter', sans-serif;
        }}
        
        /* Títulos de Lujo */
        h1, h2, h3 {{
            font-family: 'Playfair Display', serif !important;
            color: {COLOR_BORDO} !important;
            letter-spacing: -0.02em;
        }}
        
        /* Navbar Personalizado (Ocultar el de Streamlit) */
        header {{visibility: hidden;}}
        .custom-nav {{
            background: rgba(96, 0, 16, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-bottom: 2px solid {COLOR_GOLD};
            border-radius: 0 0 20px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            color: white;
        }}
        
        /* Tarjetas de Vehículos */
        .vehicle-card {{
            background: white;
            border-radius: 2.5rem; /* 3rem en React */
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            border: 1px solid #eee;
            transition: transform 0.3s;
        }}
        .vehicle-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(96, 0, 16, 0.15);
        }}
        
        /* Botones Estilizados */
        div.stButton > button {{
            background-color: {COLOR_BORDO};
            color: white;
            border-radius: 1.5rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            border: none;
            padding: 0.6rem 1.2rem;
            width: 100%;
            transition: all 0.3s;
        }}
        div.stButton > button:hover {{
            background-color: {COLOR_GOLD};
            color: white;
            box-shadow: 0 5px 15px rgba(212, 175, 55, 0.4);
        }}
        
        /* Inputs Premium */
        div[data-baseweb="input"] {{
            border-radius: 1rem;
            background-color: #f9f9f9;
            border: 1px solid #eee;
        }}
        
        /* Pills de Estado */
        .status-pill {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            display: inline-block;
        }}
        .available {{ background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
        .maintenance {{ background-color: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}

    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE DATOS Y ESTADO (StorageService) ---

# Datos Iniciales (Copiados de constants.ts)
INITIAL_FLEET = [
    {
        "id": "1", "nombre": "Hyundai Tucson 2012", "precio": 260.0,
        "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible",
        "placa": "AAVI502", "motor": "2.0 CRDi", "specs": ["Diesel", "Aut", "5 Pasajeros"]
    },
    {
        "id": "2", "nombre": "Toyota Vitz 2012", "precio": 195.0,
        "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible",
        "placa": "AAVP719", "motor": "1.3 VVT-i", "specs": ["Nafta", "Aut", "Económico"]
    },
    {
        "id": "3", "nombre": "Toyota Vitz RS 2012", "precio": 210.0,
        "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", 
        "estado": "Disponible", "placa": "AAOR725", "motor": "1.5 RS", "specs": ["Sport", "Secuencial", "Paddle Shift"]
    },
    {
        "id": "4", "nombre": "Toyota Voxy 2011", "precio": 240.0,
        "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible",
        "placa": "AAUG465", "motor": "2.0 Valvematic", "specs": ["7 Pasajeros", "Puertas Elec.", "Familiar"]
    }
]

# Inicializar Session State (Persistencia durante la sesión)
if 'fleet' not in st.session_state: st.session_state.fleet = INITIAL_FLEET
if 'reservations' not in st.session_state: st.session_state.reservations = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'current_tab' not in st.session_state: st.session_state.current_tab = "Unidades"

# Lógica de Moneda (CurrencyService)
if 'rates' not in st.session_state:
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/BRL")
        data = resp.json()
        pyg_rate = data['rates']['PYG']
    except:
        pyg_rate = 1450.0 # Fallback
    st.session_state.rates = {"PYG": int(pyg_rate), "USD": 0.18}

def to_pyg(brl_amount):
    return int(brl_amount * st.session_state.rates['PYG'])

# --- 3. COMPONENTES VISUALES ---

def render_navbar():
    # Navbar HTML personalizado
    st.markdown(f"""
        <div class="custom-nav">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="font-family:'Playfair Display'; font-size:1.5rem; font-weight:900;">JM <span style="color:{COLOR_GOLD}">Alquiler</span></div>
                <div style="font-size:0.7rem; letter-spacing:0.2em; opacity:0.8; margin-top:5px;">TRIPLE FRONTERA VIP</div>
            </div>
            <div style="font-weight:bold; font-size:0.9rem;">1 BRL = {st.session_state.rates['PYG']} Gs.</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Botones de navegación (simulados)
    col1, col2, col3 = st.columns(3)
    if col1.button("🚘 UNIDADES", use_container_width=True): st.session_state.current_tab = "Unidades"
    if col2.button("📍 SEDE CENTRAL", use_container_width=True): st.session_state.current_tab = "Sede"
    if col3.button("🛡️ ADMIN", use_container_width=True): st.session_state.current_tab = "Admin"
    st.markdown("---")

# --- 4. VISTA: CATÁLOGO DE UNIDADES (Booking Wizard) ---

@st.dialog("Gestión de Reserva Premium")
def booking_wizard(vehicle):
    st.markdown(f"### Reservando: {vehicle['nombre']}")
    st.caption(f"Placa: {vehicle['placa']} | Tarifa Diaria: R$ {vehicle['precio']}")
    
    # --- PASO 1: CRONOGRAMA ---
    st.markdown("#### 1. Cronograma")
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Fecha Retiro", min_value=datetime.date.today())
    start_time = c1.time_input("Hora", value=datetime.time(8,0))
    end_date = c2.date_input("Fecha Devolución", min_value=start_date)
    end_time = c2.time_input("Hora ", value=datetime.time(17,0))
    
    # Validaciones de Horario (Lógica de React)
    start_dt = datetime.datetime.combine(start_date, start_time)
    end_dt = datetime.datetime.combine(end_date, end_time)
    
    # Cálculo de días y precio
    duration = end_dt - start_dt
    days = duration.days + (1 if duration.seconds > 0 else 0)
    if days < 1: days = 1
    
    total_brl = days * vehicle['precio']
    reserva_fee = vehicle['precio'] # 1 día de seña
    
    st.info(f"📅 Total: {days} días | **Total Alquiler: R$ {total_brl:,.2f}**")
    
    # --- PASO 2: PAGOS ---
    st.markdown("---")
    st.markdown("#### 2. Datos y Pago (Reserva 1 Día)")
    
    name = st.text_input("Nombre Completo")
    ci = st.text_input("Documento (CI / RG)")
    
    method = st.radio("Método de Pago", ["QR Bancard", "PIX Brasil", "Transferencia", "Efectivo"], horizontal=True)
    
    # Generación de QR (Igual que en React)
    if method == "QR Bancard":
        qr_str = f"JM_ASOCIADOS_RES_BANCARD_{ci}_{reserva_fee}"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_str}", caption=f"Escanear para pagar R$ {reserva_fee}", width=150)
    elif method == "PIX Brasil":
        qr_str = f"PIX_SANTANDER_MARINA_BAEZ_{reserva_fee}"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_str}", caption=f"PIX Santander R$ {reserva_fee}", width=150)
    
    uploaded_file = st.file_uploader("Adjuntar Comprobante")

    # --- PASO 3: FIRMA ---
    st.markdown("---")
    st.markdown("#### 3. Firma Digital")
    st.caption("Acepto los términos del contrato de arrendamiento JM.")
    
    canvas_result = st_canvas(
        stroke_width=2,
        stroke_color=COLOR_BORDO,
        background_color="#fff",
        height=100,
        width=400,
        drawing_mode="freedraw",
        key="canvas",
    )
    
    if st.button("CONFIRMAR Y BLOQUEAR UNIDAD"):
        if name and ci and uploaded_file:
            # Guardar Reserva
            new_res = {
                "id": str(uuid.uuid4()),
                "cliente": name,
                "auto": vehicle['nombre'],
                "total": total_brl,
                "status": "Confirmada",
                "fechaRegistro": datetime.datetime.now().isoformat()
            }
            st.session_state.reservations.append(new_res)
            
            # Link WhatsApp (React Logic)
            msg = f"Reserva JM: {name} | Auto: {vehicle['nombre']} | Fecha: {start_date} a {end_date}"
            wa_link = f"https://wa.me/595991681191?text={msg}"
            
            st.success("¡Reserva Exitosa!")
            st.markdown(f"[📲 ENVIAR A WHATSAPP]({wa_link})")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Por favor complete todos los campos y adjunte comprobante.")

def view_catalog():
    # Hero Section
    st.markdown(f"""
        <div style="background-color:{COLOR_BORDO}; padding:3rem; border-radius:2rem; color:white; margin-bottom:2rem; position:relative;">
            <div style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0.1; background-image:url('https://www.transparenttextures.com/patterns/dark-leather.png');"></div>
            <h1 style="color:white !important; font-size:3.5rem; margin-bottom:0.5rem;">Domina el <span style="color:{COLOR_GOLD}">Camino.</span></h1>
            <p style="font-size:1.2rem; opacity:0.8;">Calidad Certificada MERCOSUR. Gestión de flota ejecutiva.</p>
        </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(2)
    for idx, vehicle in enumerate(st.session_state.fleet):
        with cols[idx % 2]:
            # HTML Card
            status_class = "available" if vehicle['estado'] == "Disponible" else "maintenance"
            st.markdown(f"""
                <div class="vehicle-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:{COLOR_GOLD}; font-weight:900; letter-spacing:0.1em;">{vehicle['placa']}</span>
                        <span class="status-pill {status_class}">{vehicle['estado']}</span>
                    </div>
                    <img src="{vehicle['img']}" style="width:100%; height:200px; object-fit:contain; margin:1rem 0;">
                    <h3 style="margin:0; font-size:1.5rem;">{vehicle['nombre']}</h3>
                    <div style="color:gray; font-size:0.8rem; margin-bottom:1rem;">{', '.join(vehicle['specs'])}</div>
                    <h2 style="margin:0;">R$ {vehicle['precio']} <span style="font-size:0.8rem; color:gray">/ día</span></h2>
                    <div style="font-size:0.8rem; color:{COLOR_GOLD}; font-weight:bold;">Gs. {to_pyg(vehicle['precio']):,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Botón de Acción
            if vehicle['estado'] == "Disponible":
                if st.button(f"Gestionar Reserva {vehicle['placa']}", key=vehicle['id']):
                    booking_wizard(vehicle)
            else:
                st.button("En Mantenimiento", disabled=True, key=vehicle['id'])

# --- 5. VISTA: ADMIN DASHBOARD (Con Gemini y Plotly) ---

def view_admin():
    st.markdown("## 🛡️ Panel Administrativo")
    
    # Auth Simple
    password = st.text_input("Clave de Acceso", type="password")
    if password != "8899":
        st.warning("Ingrese la clave administrativa.")
        return

    # Cálculos
    df = pd.DataFrame(st.session_state.reservations)
    total_rev = df['total'].sum() if not df.empty else 0
    
    # KPI Cards
    k1, k2, k3 = st.columns(3)
    k1.metric("Ingresos Totales", f"R$ {total_rev:,.2f}")
    k2.metric("Reservas Activas", len(df) if not df.empty else 0)
    k3.metric("Flota Operativa", f"{len(st.session_state.fleet)} Unidades")
    
    st.markdown("---")
    
    # Gráficos
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ingresos por Vehículo")
        if not df.empty:
            fig = px.pie(df, values='total', names='auto', color_discrete_sequence=[COLOR_BORDO, COLOR_GOLD, '#333'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos suficientes.")
            
    with c2:
        st.subheader("Inteligencia de Negocio (Gemini AI)")
        if st.button("Generar Reporte de Estrategia"):
            # Usamos la API Key del entorno o input
            api_key = os.getenv("API_KEY") 
            if not api_key:
                st.error("Configure API_KEY en entorno.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    # Usamos el modelo compatible con el código original
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    prompt = f"Analiza estos ingresos: R$ {total_rev}. Dame 3 consejos breves para rentar más autos en Paraguay."
                    with st.spinner("Consultando IA..."):
                        response = model.generate_content(prompt)
                        st.success("Análisis Completado:")
                        st.info(response.text)
                except Exception as e:
                    st.error(f"Error AI: {e}")

    # Gestión de Gastos (Simulada)
    st.markdown("### Gestión Fiscal")
    with st.expander("Registrar Nuevo Gasto"):
        desc = st.text_input("Descripción")
        monto = st.number_input("Monto (R$)")
        if st.button("Guardar Gasto"):
            st.session_state.expenses.append({"desc": desc, "monto": monto})
            st.success("Guardado.")

# --- 6. VISTA: SEDE CENTRAL ---
def view_location():
    st.markdown(f"<h1 style='text-align:center'>Sede <span style='color:{COLOR_GOLD}'>Central</span></h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:white; padding:2rem; border-radius:2rem; box-shadow:0 10px 30px rgba(0,0,0,0.1);">
            <h3>📍 Ciudad del Este</h3>
            <p>Av. Aviadores del Chaco c/ Av. Monseñor Rodriguez</p>
            <h3>📞 Contacto 24/7</h3>
            <p>+595 991 681 191</p>
            <h3>⏰ Horario</h3>
            <p>Lun-Vie: 08:00 - 17:00</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.map(pd.DataFrame({'lat': [-25.5097], 'lon': [-54.6986]})) # Mapa simple CDE

# --- 7. ROUTER PRINCIPAL ---

render_navbar()

if st.session_state.current_tab == "Unidades":
    view_catalog()
elif st.session_state.current_tab == "Sede":
    view_location()
elif st.session_state.current_tab == "Admin":
    view_admin()

# Footer
st.markdown("---")
st.markdown("<center style='color:gray; font-size:0.8rem;'>© 2024 JM Asociados. Excellence in Mobility Services.</center>", unsafe_allow_html=True)