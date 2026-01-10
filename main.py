import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
import requests
import uuid
import datetime
import os
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM Alquiler | Premium Car Rental",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES Y ESTILOS ---
COLOR_BORDO = "#600010"
COLOR_GOLD = "#D4AF37"
COLOR_BG = "#FDFCFB"
ADMIN_KEY = "8899"
CORPORATE_WA = "595991681191"

# Inyección de CSS para replicar el diseño Luxury/Glassmorphism de la app React
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;900&family=Playfair+Display:wght@700;900&display=swap');
        
        /* General App Styling */
        .stApp {{
            background-color: {COLOR_BG};
            font-family: 'Inter', sans-serif;
        }}
        
        h1, h2, h3, h4 {{
            font-family: 'Playfair Display', serif !important;
            color: {COLOR_BORDO} !important;
        }}
        
        /* Custom Navbar Simulation */
        .nav-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 2rem;
            background: rgba(96, 0, 16, 0.95);
            border-bottom: 2px solid {COLOR_GOLD};
            border-radius: 0 0 20px 20px;
            color: white;
            margin-bottom: 2rem;
        }}
        
        /* Cards styling */
        .vehicle-card {{
            background: white;
            border-radius: 2.5rem;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            border: 1px solid #eee;
            transition: all 0.3s ease;
        }}
        .vehicle-card:hover {{
            box-shadow: 0 20px 40px rgba(96, 0, 16, 0.15);
            transform: translateY(-5px);
        }}
        
        /* Buttons Override */
        div.stButton > button {{
            background-color: {COLOR_BORDO};
            color: white;
            border-radius: 1.5rem;
            border: none;
            padding: 0.5rem 2rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            transition: all 0.3s;
            width: 100%;
        }}
        div.stButton > button:hover {{
            background-color: {COLOR_GOLD};
            color: white;
            box-shadow: 0 5px 15px rgba(212, 175, 55, 0.4);
        }}
        
        /* Inputs styling */
        div.stTextInput > div > div > input {{
            border-radius: 1rem;
            background-color: #f9f9f9;
            border: 1px solid #eee;
        }}
        div.stTextInput > div > div > input:focus {{
            border-color: {COLOR_GOLD};
            box-shadow: none;
        }}
        
        /* Status Pills */
        .status-pill {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        .status-available {{ background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
        .status-maintenance {{ background-color: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}
        
    </style>
""", unsafe_allow_html=True)

# --- DATOS INICIALES (Mismos que constants.ts) ---
INITIAL_FLEET = [
    {
        "id": "1", "nombre": "Hyundai Tucson 2012", "precio": 260.0,
        "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible",
        "placa": "AAVI502", "motor": "2.0 CRDi", "transmision": "Automática",
        "specs": ["Diesel", "5 Pasajeros", "Consumo 10km/l", "6 Airbags"]
    },
    {
        "id": "2", "nombre": "Toyota Vitz 2012", "precio": 195.0,
        "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible",
        "placa": "AAVP719", "motor": "1.3 VVT-i", "transmision": "Automática",
        "specs": ["Nafta", "5 Pasajeros", "Económico", "Doble Airbag"]
    },
    {
        "id": "3", "nombre": "Toyota Vitz RS 2012", "precio": 210.0,
        "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", 
        "estado": "Disponible", "placa": "AAOR725", "motor": "1.5 RS", "transmision": "Secuencial",
        "specs": ["Nafta", "Sport", "Paddle Shift", "Frenos Disco 4R"]
    },
    {
        "id": "4", "nombre": "Toyota Voxy 2011", "precio": 240.0,
        "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible",
        "placa": "AAUG465", "motor": "2.0 Valvematic", "transmision": "Automática",
        "specs": ["Nafta", "7 Pasajeros", "Puertas Eléctricas", "Cámara Reversa"]
    }
]

# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if 'fleet' not in st.session_state:
    st.session_state.fleet = INITIAL_FLEET
if 'reservations' not in st.session_state:
    st.session_state.reservations = []
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Unidades"
if 'rates' not in st.session_state:
    # Intento de obtener cotización real
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/BRL")
        data = resp.json()
        pyg = data['rates']['PYG']
    except:
        pyg = 1450.0
    st.session_state.rates = {"PYG": int(pyg), "USD": 0.18}

# --- FUNCIONES AUXILIARES ---
def format_currency(amount, currency="BRL"):
    if currency == "BRL":
        return f"R$ {amount:,.2f}"
    elif currency == "PYG":
        return f"Gs. {int(amount * st.session_state.rates['PYG']):,.0f}"

def check_availability(vehicle_name, start_date, end_date, start_time, end_time):
    start_dt = datetime.datetime.combine(start_date, start_time)
    end_dt = datetime.datetime.combine(end_date, end_time)
    
    for res in st.session_state.reservations:
        if res['auto'] == vehicle_name and res['status'] != 'Cancelada':
            res_start = datetime.datetime.fromisoformat(res['inicio'])
            res_end = datetime.datetime.fromisoformat(res['fin'])
            # Lógica de solapamiento
            if start_dt < res_end and end_dt > res_start:
                return False
    return True

# --- COMPONENTES UI ---

def render_navbar():
    col1, col2, col3 = st.columns([2, 6, 2])
    with col1:
        st.markdown(f"<h3 style='margin:0; color:white !important;'>JM <span style='color:{COLOR_GOLD}'>Alquiler</span></h3>", unsafe_allow_html=True)
    with col2:
        # Menú de navegación manual usando columnas para simular botones centrados
        b1, b2, b3 = st.columns(3)
        if b1.button("🚘 UNIDADES"): st.session_state.current_tab = "Unidades"
        if b2.button("📍 SEDE CENTRAL"): st.session_state.current_tab = "Sede"
        if b3.button("🛡️ ADMIN"): st.session_state.current_tab = "Admin"
    with col3:
        st.markdown(f"<div style='text-align:right; font-weight:bold; color:{COLOR_GOLD}'>1 BRL = {st.session_state.rates['PYG']} Gs.</div>", unsafe_allow_html=True)
    
    st.markdown("---")

# --- VISTA 1: CATÁLOGO DE UNIDADES ---
@st.dialog("Gestión de Reserva")
def open_booking_modal(vehicle):
    st.markdown(f"### Reservando: {vehicle['nombre']}")
    st.caption(f"Placa: {vehicle['placa']} | Tarifa Diaria: {format_currency(vehicle['precio'])}")
    
    # --- PASO 1: CRONOGRAMA ---
    st.subheader("1. Cronograma")
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Fecha Retiro", min_value=datetime.date.today())
    start_time = c1.time_input("Hora Retiro", value=datetime.time(8, 0))
    end_date = c2.date_input("Fecha Devolución", min_value=start_date)
    end_time = c2.time_input("Hora Devolución", value=datetime.time(17, 0))
    
    # Cálculos
    days = (end_date - start_date).days
    if days == 0 and end_time > start_time: days = 1 # Mínimo 1 día si es mismo día
    if days < 1: days = 1
    
    total_brl = days * vehicle['precio']
    reserva_fee = vehicle['precio'] # 1 día de reserva
    
    if not check_availability(vehicle['nombre'], start_date, end_date, start_time, end_time):
        st.error("⚠️ El vehículo NO está disponible en estas fechas.")
        return

    st.info(f"📅 Total Días: {days} | Total Alquiler: **{format_currency(total_brl)}**")
    
    # --- PASO 2: DATOS Y PAGO ---
    st.markdown("---")
    st.subheader("2. Datos y Pago")
    
    name = st.text_input("Nombre Completo del Titular")
    ci = st.text_input("Documento (C.I. / R.G. / Pasaporte)")
    
    method = st.radio("Método de Pago (Reserva 1 día)", ["QR Bancard", "PIX Brasil", "Transferencia Ueno", "Efectivo en Sede"], horizontal=True)
    
    if method == "QR Bancard":
        qr_data = f"JM_ASOCIADOS_RES_BANCARD_{ci}_{reserva_fee}"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}", width=150, caption="Escanear con App Bancaria")
    elif method == "PIX Brasil":
        pix_data = f"PIX_SANTANDER_MARINA_BAEZ_24510861818_{reserva_fee}"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={pix_data}", width=150, caption="PIX Santander")
    
    uploaded_file = st.file_uploader("Adjuntar Comprobante de Pago")
    
    # --- PASO 3: FIRMA ---
    st.markdown("---")
    st.subheader("3. Firma Digital")
    st.caption("Al firmar, acepto los términos y condiciones del contrato de arrendamiento J&M.")
    
    canvas_result = st_canvas(
        stroke_width=2,
        stroke_color=COLOR_BORDO,
        background_color="#fff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas",
    )
    
    terms = st.checkbox("Acepto las cláusulas y confirmo el pago de la reserva.")
    
    if st.button("CONFIRMAR RESERVA"):
        if not terms or not name or not ci:
            st.error("Complete todos los campos y acepte los términos.")
        else:
            # Guardar Reserva
            new_res = {
                "id": str(uuid.uuid4()),
                "cliente": name,
                "ci": ci,
                "auto": vehicle['nombre'],
                "inicio": datetime.datetime.combine(start_date, start_time).isoformat(),
                "fin": datetime.datetime.combine(end_date, end_time).isoformat(),
                "total": total_brl,
                "pagado": reserva_fee,
                "status": "Confirmada",
                "metodoPago": method,
                "fechaRegistro": datetime.datetime.now().isoformat()
            }
            st.session_state.reservations.append(new_res)
            
            # Generar Link WhatsApp
            msg = f"Gestión JM Alquiler\nReserva: {name}\nUnidad: {vehicle['nombre']}\nPeriodo: {start_date} al {end_date}\nPago: {method}\nTotal: R$ {total_brl}"
            wa_link = f"https://wa.me/{CORPORATE_WA}?text={requests.utils.quote(msg)}"
            
            st.success("¡Reserva Exitosa!")
            st.markdown(f"<a href='{wa_link}' target='_blank'><button style='background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:10px; font-weight:bold;'>ENVIAR COMPROBANTE A WHATSAPP</button></a>", unsafe_allow_html=True)
            time.sleep(2)
            st.rerun()

def view_catalog():
    # Hero Section
    st.markdown(f"""
        <div style="background-color:{COLOR_BORDO}; padding: 3rem; border-radius: 2rem; color: white; margin-bottom: 2rem; position: relative; overflow: hidden;">
            <h1 style="color:white !important; font-size: 3.5rem;">Domina el <span style="color:{COLOR_GOLD}">Camino.</span></h1>
            <p style="opacity: 0.8; font-size: 1.2rem;">Calidad Certificada MERCOSUR. Gestión de flota ejecutiva en Ciudad del Este.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Unidades Disponibles")
    
    cols = st.columns(2)
    for idx, vehicle in enumerate(st.session_state.fleet):
        with cols[idx % 2]:
            with st.container():
                # Card Wrapper HTML emulation via markdown not needed if we use st container smarts
                st.markdown(f"""
                    <div class="vehicle-card">
                        <div style="display:flex; justify-content:space-between; align-items:start;">
                            <span style="font-weight:900; color:{COLOR_GOLD}; letter-spacing:0.2em;">{vehicle['placa']}</span>
                            <span class="status-pill {'status-available' if vehicle['estado'] == 'Disponible' else 'status-maintenance'}">{vehicle['estado']}</span>
                        </div>
                        <img src="{vehicle['img']}" style="width:100%; height:200px; object-fit:contain; margin: 1rem 0;">
                        <h3 style="margin:0;">{vehicle['nombre']}</h3>
                        <div style="margin-top:0.5rem; display:flex; gap:10px; flex-wrap:wrap;">
                            {' '.join([f'<span style="background:#f3f4f6; padding:2px 8px; border-radius:5px; font-size:0.7rem;">{s}</span>' for s in vehicle.get('specs', [])])}
                        </div>
                        <h2 style="font-size:2rem; margin:1rem 0;">R$ {vehicle['precio']} <span style="font-size:0.8rem; color:gray;">/ día</span></h2>
                        <p style="font-size:0.8rem; font-weight:bold; color:{COLOR_GOLD}">Gs. {int(vehicle['precio'] * st.session_state.rates['PYG']):,.0f}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Buttons logic inside the column
                c1, c2 = st.columns([1, 1])
                if vehicle['estado'] == "Disponible":
                    if st.button(f"Gestionar Reserva {vehicle['placa']}", key=f"btn_{vehicle['id']}"):
                        open_booking_modal(vehicle)
                else:
                    st.button("En Mantenimiento", disabled=True, key=f"btn_dis_{vehicle['id']}")
                
                with st.expander("Ver Ficha Técnica"):
                    st.write(f"**Motor:** {vehicle['motor']}")
                    st.write(f"**Transmisión:** {vehicle['transmision']}")

# --- VISTA 2: SEDE CENTRAL ---
def view_location():
    st.markdown(f"<h1 style='text-align:center; font-size:4rem;'>Sede <span style='color:{COLOR_GOLD}'>Central</span></h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="padding:2rem; background:white; border-radius:2rem; box-shadow:0 10px 30px rgba(0,0,0,0.05);">
            <h3>📍 Dirección Corporativa</h3>
            <p>Av. Aviadores del Chaco c/ Av. Monseñor Rodriguez<br>Ciudad del Este, Paraguay</p>
            <h3>📞 Línea de Asistencia</h3>
            <p>+595 991 681 191 (Atención 24/7)</p>
            <h3>⏰ Horario Operativo</h3>
            <p>Lun-Vie: 08:00 - 17:00<br>Sáb-Dom: 08:00 - 12:00</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        # Placeholder for Map (iframe or image)
        st.markdown(f"""
        <div style="background:{COLOR_BORDO}; padding:10px; border-radius:2rem;">
            <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d115256.02705976527!2d-54.6986!3d-25.5097!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68415d860e6e1%3A0xa19293121545722f!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="350" style="border:0; border-radius:1.5rem;" allowfullscreen="" loading="lazy"></iframe>
        </div>
        """, unsafe_allow_html=True)

# --- VISTA 3: ADMIN DASHBOARD ---
def view_admin():
    st.markdown("## 🛡️ Panel Administrativo")
    
    # Login simple
    password = st.text_input("Clave de Acceso", type="password")
    if password != ADMIN_KEY:
        st.warning("Ingrese la clave administrativa (8899) para acceder.")
        return

    # Cálculos
    df_res = pd.DataFrame(st.session_state.reservations)
    df_exp = pd.DataFrame(st.session_state.expenses)
    
    total_rev = df_res['total'].sum() if not df_res.empty else 0
    total_exp = df_exp['monto'].sum() if not df_exp.empty else 0
    net_profit = total_rev - total_exp
    
    # KPI Cards
    k1, k2, k3 = st.columns(3)
    k1.metric("Ingresos Totales (BRL)", f"R$ {total_rev:,.2f}", delta="Ventas Brutas")
    k2.metric("Egresos Operativos", f"R$ {total_exp:,.2f}", delta="-Gastos", delta_color="inverse")
    k3.metric("Utilidad Neta", f"R$ {net_profit:,.2f}", delta="Ganancia Real")
    
    st.markdown("---")
    
    # CHARTS (Plotly)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tendencia de Ingresos")
        if not df_res.empty:
            df_chart = df_res.groupby('fechaRegistro')['total'].sum().reset_index()
            fig = px.area(df_chart, x='fechaRegistro', y='total', color_discrete_sequence=[COLOR_BORDO])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de reservas.")
            
    with c2:
        st.subheader("Rentabilidad por Unidad")
        if not df_res.empty:
            fig2 = px.pie(df_res, values='total', names='auto', color_discrete_sequence=[COLOR_BORDO, COLOR_GOLD, '#333'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos.")
            
    # GEMINI AI INTEGRATION
    st.markdown("---")
    st.subheader("🤖 JM Business Intelligence (Powered by Gemini)")
    if st.button("Analizar Negocio con IA"):
        api_key = os.getenv("API_KEY") # Ensure API_KEY is set in environment
        if not api_key:
            st.error("Falta configurar la API_KEY en las variables de entorno.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Construir contexto
                summary = f"""
                Resumen Financiero JM Alquiler:
                - Ingresos: R$ {total_rev}
                - Egresos: R$ {total_exp}
                - Cantidad Reservas: {len(df_res)}
                - Flota: {[v['nombre'] for v in st.session_state.fleet]}
                """
                
                with st.spinner("Analizando estrategias de mercado..."):
                    response = model.generate_content(f"Eres un consultor de negocios experto. Analiza estos datos de una rentadora de autos en Paraguay y dame 3 consejos breves y accionables para mejorar la rentabilidad:\n\n{summary}")
                    st.success("Análisis Completado:")
                    st.markdown(f"<div style='background:#f0f9ff; padding:20px; border-radius:15px; border-left:5px solid {COLOR_GOLD};'>{response.text}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error conectando con Gemini: {str(e)}")

    # GESTIÓN DE GASTOS
    st.markdown("---")
    st.subheader("Gestión Fiscal de Egresos")
    with st.form("expenses_form"):
        c1, c2, c3 = st.columns(3)
        desc = c1.text_input("Concepto")
        amount = c2.number_input("Monto", min_value=0.0)
        curr = c3.selectbox("Moneda", ["BRL", "PYG"])
        
        if st.form_submit_button("Registrar Gasto"):
            final_amount = amount if curr == "BRL" else amount / st.session_state.rates['PYG']
            new_exp = {
                "id": str(uuid.uuid4()),
                "descripcion": desc,
                "monto": final_amount,
                "fecha": datetime.datetime.now().isoformat(),
                "categoria": "General"
            }
            st.session_state.expenses.append(new_exp)
            st.success("Gasto registrado.")
            st.rerun()
            
    if not df_exp.empty:
        st.dataframe(df_exp[['fecha', 'descripcion', 'monto']], use_container_width=True)

# --- APP MAIN FLOW ---
render_navbar()

if st.session_state.current_tab == "Unidades":
    view_catalog()
elif st.session_state.current_tab == "Sede":
    view_location()
elif st.session_state.current_tab == "Admin":
    view_admin()

# Footer
st.markdown("---")
st.markdown(f"<center style='color:gray; font-size:0.8rem;'>© 2024 JM Asociados. Excellence in Mobility Services.<br>Desarrollado con Streamlit & Gemini AI.</center>", unsafe_allow_html=True)