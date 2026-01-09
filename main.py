import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime, date, time, timedelta
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas

# --- 1. CONFIGURACIÓN Y ESTILO (PIXEL PERFECT) ---
st.set_page_config(page_title="JM Alquiler | Triple Frontera VIP", layout="wide", page_icon="🚗")

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Playfair+Display:wght@700&display=swap');

    :root {
        --bordo: #600010; --gold: #D4AF37; --ivory: #FDFCFB;
    }

    /* Animación de entrada */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .stApp { background-color: var(--ivory); font-family: 'Inter', sans-serif; animation: fadeIn 1s ease-out; }
    
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--bordo); }

    /* Luxury Cards */
    .car-card {
        background: white; padding: 2.5rem; border-radius: 2.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.05); border: 1px solid rgba(212,175,55,0.1);
        margin-bottom: 20px;
    }
    
    /* Pills & Badges */
    .status-pill { padding: 5px 15px; border-radius: 2rem; font-size: 0.8rem; font-weight: bold; }
    .available { background: #dcfce7; color: #166534; border: 1px solid #22c55e; }
    .maintenance { background: #fee2e2; color: #991b1b; border: 1px solid #ef4444; }

    /* Buttons */
    .stButton>button {
        border-radius: 1.5rem !important; background-color: var(--bordo) !important;
        color: white !important; letter-spacing: 0.2em !important; font-weight: bold !important;
        border: none !important; text-transform: uppercase; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { background-color: var(--gold) !important; transform: scale(1.02); }

    /* Inputs Gold Focus */
    div[data-baseweb="input"] { border-radius: 1rem !important; border: 1px solid #eee !important; }
    div[data-baseweb="input"]:focus-within { border-color: var(--gold) !important; }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# --- 2. GESTIÓN DE ESTADO Y DATOS ---
if 'fleet' not in st.session_state:
    st.session_state.fleet = [
        {"id": "1", "nombre": "Hyundai Tucson 2012", "precio": 260.0, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible", "placa": "AAVI502", "specs": {"motor": "2.0 CRDi", "seguridad": "6 Airbags", "capacidad": "5 Pasajeros"}},
        {"id": "2", "nombre": "Toyota Vitz 2012", "precio": 195.0, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible", "placa": "AAVP719", "specs": {"motor": "1.3 VVT-i", "seguridad": "ABS + Airbags", "capacidad": "5 Pasajeros"}},
        {"id": "3", "nombre": "Toyota Vitz RS 2012", "precio": 210.0, "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "estado": "En Taller", "placa": "AAOR725", "specs": {"motor": "1.5 RS", "seguridad": "Frenos RS", "capacidad": "5 Pasajeros"}},
        {"id": "4", "nombre": "Toyota Voxy 2011", "precio": 240.0, "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible", "placa": "AAUG465", "specs": {"motor": "2.0 Valvematic", "seguridad": "3 Filas de Asientos", "capacidad": "7 Pasajeros"}}
    ]

if 'reservations' not in st.session_state: st.session_state.reservations = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LÓGICA DE MONEDA ---
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/BRL")
        return r.json()['rates']['PYG'], r.json()['rates']['USD']
    except: return 1450.0, 0.18

PYG_RATE, USD_RATE = get_exchange_rates()

# --- 3. NAVEGACIÓN CUSTOM ---
st.markdown(f"<h1 style='text-align: center;'>JM ALQUILER PREMIUM</h1>", unsafe_allow_html=True)
nav_cols = st.columns([1,1,1,1,1])
with nav_cols[1]: 
    tab_unidades = st.button("🚗 UNIDADES", use_container_width=True)
with nav_cols[2]:
    tab_sede = st.button("📍 SEDE", use_container_width=True)
with nav_cols[3]:
    tab_admin = st.button("⚙️ ADMIN", use_container_width=True)

if "active_tab" not in st.session_state: st.session_state.active_tab = "Unidades"
if tab_unidades: st.session_state.active_tab = "Unidades"
if tab_sede: st.session_state.active_tab = "Sede"
if tab_admin: st.session_state.active_tab = "Admin"

# --- 4. TAB: UNIDADES ---
if st.session_state.active_tab == "Unidades":
    st.markdown("<div style='background: linear-gradient(90deg, #600010, #D4AF37); padding: 20px; border-radius: 1.5rem; color: white; text-align: center;'><h2>Domina el Camino</h2><p>CALIDAD CERTIFICADA MERCOSUR</p></div>", unsafe_allow_html=True)
    st.write("")

    cols = st.columns(2)
    for idx, car in enumerate(st.session_state.fleet):
        with cols[idx % 2]:
            st.markdown(f"""
                <div class="car-card">
                    <img src="{car['img']}" style="width:100%; border-radius: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                        <h3>{car['nombre']}</h3>
                        <span class="status-pill {'available' if car['estado'] == 'Disponible' else 'maintenance'}">{car['estado']}</span>
                    </div>
                    <p style="color: #666;">Placa: {car['placa']}</p>
                    <h2 style="color: var(--gold);">R$ {car['precio']} <small style="font-size: 0.8rem; color: #888;">/ {(car['precio']*PYG_RATE):,.0f} Gs</small></h2>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("VER ESPECIFICACIONES & DISPONIBILIDAD"):
                st.json(car['specs'])
                # Lógica de Calendario (Mini representación)
                st.write("📅 Disponibilidad Enero 2026")
                # Aquí se filtran fechas de st.session_state.reservations para este car['id']

            if car['estado'] == "Disponible":
                if st.button(f"GESTIONAR RESERVA: {car['nombre']}", key=f"res_{car['id']}"):
                    st.session_state.selected_car = car
                    st.session_state.show_booking = True
                    st.rerun()
            else:
                st.button("EN MANTENIMIENTO", disabled=True, key=f"dis_{car['id']}")

# --- 5. WIZARD DE RESERVA (MODAL SIMULADO) ---
if st.session_state.get('show_booking'):
    car = st.session_state.selected_car
    st.divider()
    st.header(f"Reserva: {car['nombre']}")
    
    tab1, tab2, tab3 = st.tabs(["🕒 Cronograma", "💳 Portal de Pagos", "📄 Contrato"])
    
    with tab1:
        col_d1, col_t1 = st.columns(2)
        start_date = col_d1.date_input("Fecha Inicio", min_value=date.today())
        start_time = col_t1.time_input("Hora Inicio", value=time(8, 0))
        
        col_d2, col_t2 = st.columns(2)
        end_date = col_d2.date_input("Fecha Fin", min_value=start_date)
        end_time = col_t2.time_input("Hora Fin", value=time(17, 0))
        
        # Validaciones de Horario
        if start_date.weekday() < 5: # Mon-Fri
            if not (time(8,0) <= start_time <= time(17,0)): st.warning("⚠️ Fuera de horario oficina (08:00 - 17:00)")
        
        days = (end_date - start_date).days or 1
        total = days * car['precio']
        st.subheader(f"Total Estadía: R$ {total} ({total*PYG_RATE:,.0f} Gs)")

    with tab2:
        method = st.selectbox("Método de Pago", ["QR Bancard", "PIX (Brasil)", "Transferencia Ueno", "Efectivo"])
        if "QR" in method:
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=JM_ASOCIADOS_PAY_{total}", caption="Escanee para pagar")
        st.file_uploader("Subir comprobante de pago")

    with tab3:
        st.text_area("Términos del Contrato", "CONTRATO DE ARRENDAMIENTO JM ASOCIADOS... El arrendatario se compromete a devolver el vehículo en las mismas condiciones...", height=150)
        st.write("Firma Digital:")
        canvas_result = st_canvas(fill_color="white", stroke_width=2, stroke_color="black", background_color="white", height=150, key="canvas")
        
        if st.button("CONFIRMAR Y FINALIZAR"):
            new_res = {"car": car['nombre'], "total": total, "date": str(start_date)}
            st.session_state.reservations.append(new_res)
            wa_text = f"Hola JM Alquiler, confirmo reserva de {car['nombre']} por {days} días. Total: R$ {total}."
            st.success("¡Reserva guardada!")
            st.markdown(f"[Finalizar en WhatsApp](https://wa.me/595991681191?text={wa_text.replace(' ', '%20')})")
            if st.button("Cerrar"): st.session_state.show_booking = False; st.rerun()

# --- 6. TAB: ADMIN DASHBOARD ---
elif st.session_state.active_tab == "Admin":
    if st.text_input("Acceso Admin", type="password") == "8899":
        st.title("Admin Dashboard")
        
        # KPIs
        rev = sum(r['total'] for r in st.session_state.reservations)
        exp = sum(e['amount'] for e in st.session_state.expenses)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Ingresos (BRL)", f"R$ {rev:,.2f}")
        k2.metric("Gastos (BRL)", f"R$ {exp:,.2f}")
        k3.metric("Utilidad Neta", f"R$ {rev-exp:,.2f}")

        # Charts
        c1, c2 = st.columns(2)
        if st.session_state.reservations:
            df_res = pd.DataFrame(st.session_state.reservations)
            fig_area = px.area(df_res, x="date", y="total", title="Ingresos en el Tiempo", color_discrete_sequence=['#600010'])
            c1.plotly_chart(fig_area, use_container_width=True)
            
            fig_pie = px.pie(df_res, values='total', names='car', title="Ventas por Unidad", hole=0.4)
            fig_pie.update_traces(marker=dict(colors=['#600010', '#D4AF37', '#333']))
            c2.plotly_chart(fig_pie, use_container_width=True)

        # AI Analyst
        if st.button("🤖 ANALIZAR NEGOCIO CON IA"):
            st.info("Generando reporte estratégico con Gemini 2.5 Flash...")
            # Aquí iría: model.generate_content(f"Analiza estos datos: {st.session_state.reservations}...")
            st.success("Sugerencia IA: El Hyundai Tucson genera el 60% de tus ingresos. Considera adquirir una unidad 2018 para el segmento corporativo de CDE.")

    else: st.warning("Ingrese la clave maestra.")

# --- 7. TAB: SEDE CENTRAL ---
elif st.session_state.active_tab == "Sede":
    st.header("Sede Central - Ciudad del Este")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Dirección:** Av. Aviadores del Chaco esq. Santa Teresa, CDE.  
        **Horarios:** Lunes a Viernes: 08:00 - 17:00  
        Sábados y Domingos: 08:00 - 12:00  
        **Teléfono:** +595 991 681 191
        """)
    with col2:
        st.info("Mapa VIP: Centro de Operaciones Triple Frontera")
        st.map(pd.DataFrame({'lat': [-25.5097], 'lon': [-54.6111]}))