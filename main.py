import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
import datetime
import uuid
import os
import json
import requests
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM Alquiler | Premium Car Rental",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES Y ESTILOS ---
APP_BORDO = "#600010"
APP_GOLD = "#D4AF37"
ADMIN_KEY = "8899"
CORPORATE_WA = "595991681191"

# CSS Personalizado para imitar el look de la App React
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    
    .stApp {{
        background-color: #FDFCFB;
        font-family: 'Inter', sans-serif;
    }}
    
    h1, h2, h3 {{
        font-family: 'Playfair Display', serif;
        color: {APP_BORDO};
    }}
    
    .stButton>button {{
        background-color: {APP_BORDO};
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        width: 100%;
    }}
    
    .stButton>button:hover {{
        background-color: {APP_GOLD};
        color: #fff;
    }}
    
    .metric-card {{
        background-color: white;
        border: 1px solid #eee;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }}
    
    .vehicle-card {{
        background: white;
        border-radius: 20px;
        padding: 15px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}
    
    .status-available {{ color: green; font-weight: bold; }}
    .status-maintenance {{ color: red; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- DATOS INICIALES (MOCK) ---
INITIAL_FLEET = [
  {
    "id": '1', "nombre": "Hyundai Tucson 2012", "precio": 260.0,
    "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible",
    "placa": "AAVI502", "transmision": "Automática", "combustible": "Diesel", "pasajeros": 5
  },
  {
    "id": '2', "nombre": "Toyota Vitz 2012", "precio": 195.0,
    "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible",
    "placa": "AAVP719", "transmision": "Automática", "combustible": "Nafta", "pasajeros": 5
  },
  {
    "id": '3', "nombre": "Toyota Vitz RS 2012", "precio": 195.0,
    "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", 
    "estado": "Disponible", "placa": "AAOR725", "transmision": "Secuencial", "combustible": "Nafta", "pasajeros": 5
  },
  {
    "id": '4', "nombre": "Toyota Voxy 2011", "precio": 240.0,
    "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible",
    "placa": "AAUG465", "transmision": "Automática", "combustible": "Nafta", "pasajeros": 7
  }
]

# --- GESTIÓN DE ESTADO Y PERSISTENCIA (LOCAL JSON) ---
DATA_FILE = "jm_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "fleet": INITIAL_FLEET,
            "reservations": [],
            "expenses": []
        }
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"fleet": INITIAL_FLEET, "reservations": [], "expenses": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Inicializar Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'view' not in st.session_state:
    st.session_state.view = 'HOME' # HOME, LOCATION, ADMIN, BOOKING
if 'selected_vehicle' not in st.session_state:
    st.session_state.selected_vehicle = None
if 'rates' not in st.session_state:
    st.session_state.rates = {"PYG": 1450, "USD": 0.18}

# --- SERVICIOS AUXILIARES ---
def get_currency_rates():
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/BRL")
        data = resp.json()
        st.session_state.rates = {
            "PYG": round(data['rates']['PYG']),
            "USD": data['rates']['USD']
        }
    except:
        pass # Usar default

def analyze_business_ai():
    # Asegúrate de configurar tu API Key en st.secrets o variable de entorno
    api_key = os.environ.get("API_KEY") # O st.secrets["API_KEY"]
    if not api_key:
        return "⚠️ Configura la API KEY de Gemini para usar esta función."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        data_summary = f"""
        Reservas Totales: {len(st.session_state.data['reservations'])}
        Ingresos Totales (BRL): {sum(r['total'] for r in st.session_state.data['reservations'])}
        Gastos Totales (BRL): {sum(e['monto'] for e in st.session_state.data['expenses'])}
        Flota: {[f['nombre'] + ' (' + f['estado'] + ')' for f in st.session_state.data['fleet']]}
        """
        
        prompt = f"""
        Eres un consultor de negocios experto para una rentadora de autos en Paraguay.
        Analiza estos datos y da 3 consejos cortos y accionables para mejorar la rentabilidad.
        Datos: {data_summary}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error IA: {str(e)}"

def get_contract_text(client_data, vehicle, start, end, total, days):
    return f"""
    CONTRATO DE ALQUILER DE VEHÍCULO - J&M ASOCIADOS
    
    ARRENDADOR: J&M ASOCIADOS (RUC/CI: 1.702.076-0)
    ARRENDATARIO: {client_data['nombre']} (CI: {client_data['ci']})
    
    VEHÍCULO: {vehicle['nombre']} | PLACA: {vehicle['placa']}
    FECHA RETIRO: {start} | FECHA DEVOLUCIÓN: {end} ({days} días)
    TOTAL A PAGAR: R$ {total}
    
    1. El arrendatario recibe el vehículo en buen estado y se compromete a devolverlo igual.
    2. El uso es exclusivo dentro del territorio nacional salvo autorización escrita.
    3. En caso de accidente, el arrendatario cubre la franquicia del seguro (Gs. 5.000.000).
    4. El arrendador autoriza al arrendatario a conducir el vehículo.
    
    Firma Digital Adjunta.
    """

# --- COMPONENTES UI ---

def render_header():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=60)
    with col2:
        st.markdown(f"<h3 style='margin:0'>JM ALQUILER</h3><span style='color:{APP_GOLD}; font-size: 0.8em; letter-spacing: 2px;'>TRIPLE FRONTERA VIP</span>", unsafe_allow_html=True)
    with col3:
        st.metric("Cotización BRL", f"Gs. {st.session_state.rates['PYG']:,}")

def render_nav():
    cols = st.columns(4)
    if cols[0].button("🏠 Flota"): st.session_state.view = 'HOME'; st.session_state.selected_vehicle = None; st.rerun()
    if cols[1].button("📍 Ubicación"): st.session_state.view = 'LOCATION'; st.rerun()
    if cols[2].button("👮 Admin"): st.session_state.view = 'ADMIN'; st.rerun()
    if cols[3].button("🔄 Actualizar"): get_currency_rates(); st.rerun()

# --- VISTA: FLOTA (HOME) ---
def view_home():
    st.markdown(f"<h1 style='text-align:center; font-size: 3rem;'>Domina el <span style='color:{APP_GOLD}'>Camino</span></h1>", unsafe_allow_html=True)
    
    fleet = st.session_state.data['fleet']
    
    # Grid layout for vehicles
    cols = st.columns(2)
    for idx, v in enumerate(fleet):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                <div class="vehicle-card">
                    <div style="position:relative;">
                        <span style="background-color:{'#e6fffa' if v['estado']=='Disponible' else '#fff5f5'}; 
                                     color:{'green' if v['estado']=='Disponible' else 'red'}; 
                                     padding:5px 10px; border-radius:10px; font-weight:bold; font-size:0.8em;">
                            {v['estado']}
                        </span>
                        <img src="{v['img']}" style="width:100%; height:200px; object-fit:contain; mix-blend-mode: multiply;">
                    </div>
                    <h3 style="margin-bottom:0;">{v['nombre']}</h3>
                    <p style="color:gray; font-size:0.8em; letter-spacing:1px; margin-top:0;">{v['placa']}</p>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin: 10px 0;">
                        <div>
                            <span style="font-size:1.5em; font-weight:900; color:{APP_BORDO}">R$ {v['precio']}</span>
                            <small style="color:gray;">/día</small>
                        </div>
                        <div style="text-align:right;">
                            <small>Aprox.</small><br>
                            <b>Gs. {(v['precio'] * st.session_state.rates['PYG']):,.0f}</b>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Detalles técnicos
                with st.expander("Ver Ficha Técnica"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Transmisión:** {v.get('transmision','-')}")
                    c1.write(f"**Pasajeros:** {v.get('pasajeros','-')}")
                    c2.write(f"**Combustible:** {v.get('combustible','-')}")
                
                if v['estado'] == 'Disponible':
                    if st.button(f"RESERVAR {v['nombre']}", key=f"btn_{v['id']}"):
                        st.session_state.selected_vehicle = v
                        st.session_state.view = 'BOOKING'
                        st.rerun()
                else:
                    st.button("NO DISPONIBLE", disabled=True, key=f"btn_dis_{v['id']}")

# --- VISTA: RESERVA (BOOKING WIZARD) ---
def view_booking():
    vehicle = st.session_state.selected_vehicle
    if not vehicle:
        st.session_state.view = 'HOME'
        st.rerun()

    st.markdown(f"## Reservando: {vehicle['nombre']}")
    col_img, col_form = st.columns([1, 2])
    
    with col_img:
        st.image(vehicle['img'])
        st.info(f"Tarifa Diaria: R$ {vehicle['precio']}")

    with col_form:
        # STEP 1: FECHAS
        st.subheader("1. Selección de Fechas")
        col_d1, col_d2 = st.columns(2)
        today = datetime.date.today()
        start_date = col_d1.date_input("Fecha Retiro", min_value=today, value=today)
        end_date = col_d2.date_input("Fecha Devolución", min_value=start_date, value=start_date + datetime.timedelta(days=1))
        
        start_time = col_d1.time_input("Hora Retiro", value=datetime.time(9,0))
        end_time = col_d2.time_input("Hora Devolución", value=datetime.time(9,0))

        # Check availability logic
        blocked = False
        for r in st.session_state.data['reservations']:
            if r['auto'] == vehicle['nombre'] and r['status'] != 'Cancelada':
                r_start = datetime.datetime.strptime(r['inicio'], "%Y-%m-%d").date()
                r_end = datetime.datetime.strptime(r['fin'], "%Y-%m-%d").date()
                # Simple overlap check
                if not (end_date < r_start or start_date > r_end):
                    blocked = True
                    break
        
        if blocked:
            st.error("🚫 Vehículo no disponible en estas fechas.")
            return

        days = (end_date - start_date).days
        if days < 1: days = 1
        total_brl = days * vehicle['precio']
        
        st.success(f"Días: {days} | **Total a Pagar: R$ {total_brl:,.2f}** (Aprox. Gs. {total_brl * st.session_state.rates['PYG']:,.0f})")

        # STEP 2: DATOS
        st.subheader("2. Datos del Cliente")
        name = st.text_input("Nombre Completo")
        ci = st.text_input("CI / DNI / Pasaporte")
        phone = st.text_input("WhatsApp (con código país)")

        # STEP 3: PAGO
        st.subheader("3. Método de Pago")
        payment_method = st.radio("Seleccione opción:", ["Efectivo (en local)", "PIX", "Transferencia Ueno", "Tarjeta"])
        
        if payment_method == "PIX":
            st.warning("Envía el pago a la llave: **24510861818** (Marina Baez). Sube el comprobante abajo.")
        
        proof_file = st.file_uploader("Subir Comprobante (Opcional)", type=['png', 'jpg', 'pdf'])

        # STEP 4: CONTRATO
        st.subheader("4. Contrato y Firma")
        contract = get_contract_text({"nombre": name, "ci": ci}, vehicle, start_date, end_date, total_brl, days)
        st.text_area("Contrato de Alquiler", value=contract, height=150, disabled=True)
        
        st.write("Firma Digital (Dibuja abajo):")
        signature = st_canvas(
            stroke_width=2,
            stroke_color="#000000",
            background_color="#ffffff",
            height=150,
            drawing_mode="freedraw",
            key="signature"
        )

        terms = st.checkbox("Acepto los términos y condiciones")

        if st.button("CONFIRMAR RESERVA"):
            if not name or not ci or not phone:
                st.error("Por favor completa todos los datos personales.")
            elif not terms:
                st.error("Debes aceptar los términos.")
            elif signature.json_data is None or len(signature.json_data["objects"]) == 0:
                st.error("Por favor firma el contrato.")
            else:
                # SAVE DATA
                new_res = {
                    "id": str(uuid.uuid4())[:8],
                    "cliente": name,
                    "ci": ci,
                    "celular": phone,
                    "auto": vehicle['nombre'],
                    "inicio": str(start_date),
                    "fin": str(end_date),
                    "total": total_brl,
                    "status": "Pendiente",
                    "metodoPago": payment_method,
                    "fechaRegistro": str(datetime.date.today())
                }
                st.session_state.data['reservations'].append(new_res)
                save_data(st.session_state.data)
                
                # SUCCESS
                st.balloons()
                msg = f"*NUEVA RESERVA JM*\nID: {new_res['id']}\nAuto: {vehicle['nombre']}\nCliente: {name}\nFecha: {start_date} al {end_date}\nTotal: R$ {total_brl}"
                wa_link = f"https://wa.me/{CORPORATE_WA}?text={requests.utils.quote(msg)}"
                
                st.success("¡Reserva Creada con Éxito!")
                st.markdown(f"""
                <a href="{wa_link}" target="_blank">
                    <button style="background-color:#25D366; color:white; padding:10px 20px; border:none; border-radius:10px; font-weight:bold;">
                        📱 ENVIAR A WHATSAPP
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
                time.sleep(5)
                st.session_state.view = 'HOME'
                st.rerun()

# --- VISTA: UBICACIÓN ---
def view_location():
    st.markdown("## 📍 Nuestra Sede")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        ### Dirección
        Av. Aviadores del Chaco c/ Av. Monseñor Rodriguez
        Ciudad del Este, Paraguay.
        
        ### Horarios
        - Lun a Vie: 08:00 - 17:00
        - Sáb a Dom: 08:00 - 12:00
        
        ### Contacto
        WhatsApp: +{CORPORATE_WA}
        """)
    with c2:
        # Un mapa estático o iframe de Google Maps
        st.map(pd.DataFrame({'lat': [-25.509], 'lon': [-54.611]}))

# --- VISTA: ADMIN ---
def view_admin():
    st.markdown("## 🛡️ Panel Administrativo")
    
    pwd = st.text_input("Clave de Acceso", type="password")
    if pwd != ADMIN_KEY:
        st.warning("Ingrese clave correcta.")
        return

    # DATA PROCESSING
    reservations = st.session_state.data['reservations']
    expenses = st.session_state.data['expenses']
    fleet = st.session_state.data['fleet']

    total_revenue = sum(r['total'] for r in reservations)
    total_expenses_brl = sum(e['monto'] if e.get('moneda')=='BRL' else e['monto']/st.session_state.rates['PYG'] for e in expenses)
    profit = total_revenue - total_expenses_brl

    # KPIS
    k1, k2, k3 = st.columns(3)
    k1.metric("Ingresos Totales", f"R$ {total_revenue:,.0f}")
    k2.metric("Gastos (Est. BRL)", f"R$ {total_expenses_brl:,.0f}")
    k3.metric("Beneficio Neto", f"R$ {profit:,.0f}", delta_color="normal")

    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🚗 Flota", "📝 Reservas", "💸 Gastos"])

    with tab1:
        st.subheader("Análisis de Negocio")
        if st.button("✨ Generar Análisis con Gemini AI"):
            with st.spinner("Consultando IA..."):
                analysis = analyze_business_ai()
                st.info(analysis)
        
        # Charts
        c1, c2 = st.columns(2)
        if reservations:
            df_res = pd.DataFrame(reservations)
            fig_rev = px.bar(df_res, x='fechaRegistro', y='total', title='Ingresos por Fecha', color_discrete_sequence=[APP_GOLD])
            c1.plotly_chart(fig_rev, use_container_width=True)
        
        if expenses:
            df_exp = pd.DataFrame(expenses)
            fig_exp = px.pie(df_exp, names='categoria', values='monto', title='Gastos por Categoría', color_discrete_sequence=px.colors.sequential.RdBu)
            c2.plotly_chart(fig_exp, use_container_width=True)

    with tab2:
        st.subheader("Gestión de Flota")
        for v in fleet:
            with st.expander(f"{v['nombre']} ({v['estado']})"):
                new_status = st.selectbox("Estado", ["Disponible", "En Taller"], index=0 if v['estado']=="Disponible" else 1, key=f"st_{v['id']}")
                new_maint = st.date_input("Próx. Mantenimiento", key=f"mt_{v['id']}")
                if st.button("Guardar Estado", key=f"sv_{v['id']}"):
                    v['estado'] = new_status
                    v['proximoMantenimiento'] = str(new_maint)
                    save_data(st.session_state.data)
                    st.success("Actualizado")
                    st.rerun()

    with tab3:
        st.subheader("Historial de Reservas")
        if reservations:
            st.dataframe(pd.DataFrame(reservations))
            
            # Manual Entry
            with st.form("manual_res"):
                st.write("Carga Manual")
                c1, c2, c3 = st.columns(3)
                m_cli = c1.text_input("Cliente")
                m_car = c2.selectbox("Auto", [v['nombre'] for v in fleet])
                m_tot = c3.number_input("Total R$", min_value=0.0)
                if st.form_submit_button("Agregar"):
                    new_r = {
                        "id": "MANUAL", "cliente": m_cli, "ci": "000", "celular": "000",
                        "auto": m_car, "inicio": str(datetime.date.today()), "fin": str(datetime.date.today()),
                        "total": m_tot, "status": "Completada", "metodoPago": "Efectivo",
                        "fechaRegistro": str(datetime.date.today())
                    }
                    st.session_state.data['reservations'].append(new_r)
                    save_data(st.session_state.data)
                    st.rerun()

    with tab4:
        st.subheader("Control de Gastos")
        with st.form("add_expense"):
            c1, c2, c3 = st.columns(3)
            desc = c1.text_input("Descripción")
            amount = c2.number_input("Monto", min_value=0.0)
            curr = c3.selectbox("Moneda", ["BRL", "PYG"])
            cat = st.selectbox("Categoría", ["Mantenimiento", "Lavado", "Seguro", "Otro"])
            
            if st.form_submit_button("Registrar Gasto"):
                new_exp = {
                    "id": str(uuid.uuid4())[:6],
                    "descripcion": desc,
                    "monto": amount,
                    "moneda": curr,
                    "categoria": cat,
                    "fecha": str(datetime.date.today())
                }
                st.session_state.data['expenses'].append(new_exp)
                save_data(st.session_state.data)
                st.success("Gasto registrado")
                st.rerun()
        
        if expenses:
            st.dataframe(pd.DataFrame(expenses))

# --- APP MAIN FLOW ---
render_header()
st.divider()
render_nav()

if st.session_state.view == 'HOME':
    view_home()
elif st.session_state.view == 'BOOKING':
    view_booking()
elif st.session_state.view == 'LOCATION':
    view_location()
elif st.session_state.view == 'ADMIN':
    view_admin()